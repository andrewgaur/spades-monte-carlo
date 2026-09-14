#include <algorithm>
#include <array>
#include <chrono>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <random>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

using Card = std::pair<int, std::string>;
using Hand = std::vector<Card>;
using Trick = std::vector<std::pair<int, Card>>;
using Hands = std::array<Hand, 4>;

struct Fixture {
    Hands hands;
    int start_player;
    bool spades_broken;
};

Hand deck() {
    Hand cards;
    for (const std::string suit : {"Spades", "Hearts", "Diamonds", "Clubs"})
        for (int rank = 2; rank < 15; ++rank) cards.emplace_back(rank, suit);
    return cards;
}

Hand legal_cards(const Hand& hand, const Trick& trick, bool spades_broken) {
    Hand choices;
    if (!trick.empty()) {
        for (const auto& card : hand)
            if (card.second == trick.front().second.second) choices.push_back(card);
        return choices.empty() ? hand : choices;
    }
    if (!spades_broken) {
        for (const auto& card : hand)
            if (card.second != "Spades") choices.push_back(card);
        if (!choices.empty()) return choices;
    }
    return hand;
}

bool beats(const Card& card, const Card& winner, const std::string& /*led_suit*/) {
    if (card.second == "Spades" && winner.second != "Spades") return true;
    if (card.second != "Spades" && winner.second == "Spades") return false;
    if (card.second != winner.second) return false;
    return card.first > winner.first;
}

bool rank_less(const Card& left, const Card& right) { return left.first < right.first; }

Card play_card(const Hand& hand, const Trick& trick, bool spades_broken) {
    const auto choices = legal_cards(hand, trick, spades_broken);
    if (choices.empty()) throw std::invalid_argument("Cannot play an empty hand");
    if (trick.empty()) return *std::max_element(choices.begin(), choices.end(), rank_less);

    Hand winning_options, non_spades;
    const auto& lead_card = trick.front().second;
    for (const auto& card : choices) {
        // Preserve the original policy for a fair port comparison.
        if (beats(card, lead_card, lead_card.second)) winning_options.push_back(card);
        if (card.second != "Spades") non_spades.push_back(card);
    }
    if (!winning_options.empty())
        return *std::min_element(winning_options.begin(), winning_options.end(), rank_less);
    const auto& discards = non_spades.empty() ? choices : non_spades;
    return *std::min_element(discards.begin(), discards.end(), rank_less);
}

Card play_card_nil(const Hand& hand, const Trick& trick, bool spades_broken) {
    const auto choices = legal_cards(hand, trick, spades_broken);
    if (choices.empty()) throw std::invalid_argument("Cannot play an empty hand");
    if (!trick.empty()) {
        Hand safe;
        const auto& lead_card = trick.front().second;
        for (const auto& card : choices)
            if (!beats(card, lead_card, lead_card.second)) safe.push_back(card);
        if (!safe.empty()) return *std::max_element(safe.begin(), safe.end(), rank_less);
    }
    return *std::min_element(choices.begin(), choices.end(), rank_less);
}

std::pair<int, bool> play_trick(Hands& hands, int start_player, bool spades_broken) {
    Trick trick;
    for (int i = 0; i < 4; ++i) {
        const int player = (start_player + i) % 4;
        auto& hand = hands[player];
        const auto card = play_card(hand, trick, spades_broken);
        hand.erase(std::find(hand.begin(), hand.end(), card));
        trick.emplace_back(player, card);
        if (card.second == "Spades") spades_broken = true;
    }
    auto winner = trick.front();
    for (std::size_t i = 1; i < trick.size(); ++i)
        if (beats(trick[i].second, winner.second, trick.front().second.second)) winner = trick[i];
    return {winner.first, spades_broken};
}

std::array<int, 4> play_dealt_game(const Hands& dealt_hands, int start_player = 0,
    bool spades_broken = false) {
    for (const auto& hand : dealt_hands)
        if (hand.size() != 13) throw std::invalid_argument("Expected four 13-card hands");
    auto hands = dealt_hands;
    std::array<int, 4> tricks_won{};
    for (int i = 0; i < 13; ++i) {
        const auto [winner, broken] = play_trick(hands, start_player, spades_broken);
        ++tricks_won[winner];
        start_player = winner;
        spades_broken = broken;
    }
    if (std::accumulate(tricks_won.begin(), tricks_won.end(), 0) != 13)
        throw std::logic_error("A dealt game must award 13 tricks");
    return tricks_won;
}

int play_game(const Hand& my_hand, const Hand& cards_left, std::mt19937& rng) {
    if (my_hand.size() != 13 || cards_left.size() != 39)
        throw std::invalid_argument("Expected 13 cards in hand and 39 remaining cards");
    auto shuffled = cards_left;
    std::shuffle(shuffled.begin(), shuffled.end(), rng);
    Hands hands = {my_hand, Hand(shuffled.begin(), shuffled.begin() + 13),
        Hand(shuffled.begin() + 13, shuffled.begin() + 26), Hand(shuffled.begin() + 26, shuffled.end())};
    return play_dealt_game(hands)[0];
}

std::vector<long long> score_bid_totals(const std::vector<int>& results) {
    if (results.empty()) throw std::invalid_argument("results must not be empty");
    std::vector<long long> totals(14);
    for (int bid = 0; bid < 14; ++bid)
        for (int tricks : results)
            totals[bid] += bid == 0 ? (tricks == 0 ? 100 : -100)
                : tricks >= bid ? 10 * bid + tricks - bid : -10 * bid;
    return totals;
}

std::vector<double> score_bids(const std::vector<int>& results) {
    const auto totals = score_bid_totals(results);
    std::vector<double> means;
    means.reserve(totals.size());
    for (const auto total : totals) means.push_back(static_cast<double>(total) / results.size());
    return means;
}

Card card_from_id(int id) {
    static const std::array<std::string, 4> suits = {"Spades", "Hearts", "Diamonds", "Clubs"};
    if (id < 0 || id >= 52) throw std::invalid_argument("Card ID must be from 0 through 51");
    return {id % 13 + 2, suits[id / 13]};
}

std::vector<Fixture> load_fixtures(const std::string& path) {
    std::ifstream input(path);
    if (!input) throw std::runtime_error("Could not open fixture file: " + path);
    std::vector<Fixture> fixtures;
    std::string line;
    int line_number = 0;
    while (std::getline(input, line)) {
        ++line_number;
        line = line.substr(0, line.find('#'));
        std::istringstream values(line);
        int start, broken;
        if (!(values >> start)) continue;
        if (!(values >> broken) || start < 0 || start > 3 || (broken != 0 && broken != 1))
            throw std::runtime_error("Invalid fixture header on line " + std::to_string(line_number));
        Fixture fixture{{}, start, broken != 0};
        std::array<bool, 52> seen{};
        for (int i = 0; i < 52; ++i) {
            int id;
            if (!(values >> id) || id < 0 || id >= 52 || seen[id])
                throw std::runtime_error("Invalid cards on fixture line " + std::to_string(line_number));
            seen[id] = true;
            fixture.hands[i / 13].push_back(card_from_id(id));
        }
        int extra;
        if (values >> extra)
            throw std::runtime_error("Too many cards on fixture line " + std::to_string(line_number));
        fixtures.push_back(std::move(fixture));
    }
    if (fixtures.empty()) throw std::runtime_error("Fixture file is empty");
    return fixtures;
}

void benchmark(const std::string& path, int games, int repeats) {
    const auto fixtures = load_fixtures(path);
    std::vector<std::array<int, 4>> expected;
    for (const auto& fixture : fixtures)
        expected.push_back(play_dealt_game(fixture.hands, fixture.start_player, fixture.spades_broken));

    std::cout << "CHECK fixtures=" << fixtures.size() << " signature=";
    for (std::size_t i = 0; i < expected.size(); ++i) {
        if (i) std::cout << ';';
        for (int player = 0; player < 4; ++player) {
            if (player) std::cout << ',';
            std::cout << expected[i][player];
        }
    }
    std::cout << '\n';

    for (int i = 0; i < games; ++i) {
        const auto& fixture = fixtures[i % fixtures.size()];
        play_dealt_game(fixture.hands, fixture.start_player, fixture.spades_broken);
    }

    for (int repeat = 1; repeat <= repeats; ++repeat) {
        std::vector<int> results;
        results.reserve(games);
        long long checksum = 0;
        const auto start = std::chrono::steady_clock::now();
        for (int i = 0; i < games; ++i) {
            const auto& fixture = fixtures[i % fixtures.size()];
            const auto tricks = play_dealt_game(fixture.hands, fixture.start_player, fixture.spades_broken);
            results.push_back(tricks[0]);
            for (int player = 0; player < 4; ++player) checksum += (player + 1) * tricks[player];
        }
        const double seconds = std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count();
        const auto totals = score_bid_totals(results);
        const int best_bid = static_cast<int>(std::distance(totals.begin(), std::max_element(totals.begin(), totals.end())));
        std::cout << std::fixed << std::setprecision(9) << "TIME repeat=" << repeat << " games=" << games
            << " seconds=" << seconds << " checksum=" << checksum << " best_bid=" << best_bid << " score_totals=";
        for (std::size_t i = 0; i < totals.size(); ++i) {
            if (i) std::cout << ',';
            std::cout << totals[i];
        }
        std::cout << '\n';
    }
}

int main(int argc, char* argv[]) {
    try {
        if (argc > 1 && std::string(argv[1]) == "--benchmark") {
            if (argc != 5) throw std::invalid_argument("usage: spades-monte-carlo --benchmark FIXTURES GAMES REPEATS");
            const int games = std::stoi(argv[3]);
            const int repeats = std::stoi(argv[4]);
            if (games <= 0 || repeats <= 0) throw std::invalid_argument("GAMES and REPEATS must be positive");
            benchmark(argv[2], games, repeats);
            return 0;
        }

        constexpr int num_trials = 10000;
        std::mt19937 rng(std::random_device{}());
        auto cards = deck();
        std::shuffle(cards.begin(), cards.end(), rng);
        const Hand my_hand(cards.begin(), cards.begin() + 13);
        const Hand remaining(cards.begin() + 13, cards.end());
        std::vector<int> results;
        results.reserve(num_trials);
        for (int i = 0; i < num_trials; ++i) results.push_back(play_game(my_hand, remaining, rng));
        const double mean = std::accumulate(results.begin(), results.end(), 0.0) / num_trials;
        const auto scores = score_bids(results);
        const int best_bid = static_cast<int>(std::distance(scores.begin(), std::max_element(scores.begin(), scores.end())));
        std::cout << "Hand: ";
        for (const auto& card : my_hand) std::cout << '(' << card.first << ", " << card.second << ") ";
        std::cout << "\nEstimated Tricks Taken: " << mean << "\nList of average scores for each bid: ";
        for (double score : scores) std::cout << score << ' ';
        std::cout << "\nRecommended Bid of " << best_bid << " with an average score of " << scores[best_bid] << '\n';
    } catch (const std::exception& error) {
        std::cerr << "error: " << error.what() << '\n';
        return 1;
    }
}
