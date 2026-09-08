
// A C++ port of my python script that computes the estimated tricks taken and recommended bid
// for any given hand of 13 cards, following standard rules of the card game spades
// mostly intended to help me gain experience as I learn C++

#include <algorithm>
#include <array>
#include <cmath>
#include <iostream>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

// Python tuple: pair; Python list: vector.
using Card = std::pair<int, std::string>;
using Hand = std::vector<Card>;
using Trick = std::vector<std::pair<int, Card>>;
using Hands = std::array<Hand, 4>;

//define the deck; considered as a large hand (array of cards)
Hand Deck() {
    Hand deck{};
    for (const std::string suit : {"Spades", "Hearts", "Diamonds", "Clubs"})
        for (int rank = 2; rank < 15; ++rank) deck.emplace_back(rank, suit);
    return deck;
}

// const & reads a vector without copying or changing it.
Hand legal_cards(const Hand& hand, const Trick& trick, bool spades_broken) {
    Hand choices{};

    //if the trick has started, the only legal cards are those that follow suit
    if (!trick.empty()) {
        for (const auto& card : hand)

            // if the suit of the card in given hand is the same as the leading suit, it is legal
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

//check if any given card beats the current winner to evaluate trick winner

bool beats(const Card& card, const Card& winner, const std::string& /*led_suit*/) {
    if (card.second == "Spades" && winner.second != "Spades") return true;
    if (card.second != "Spades" && winner.second == "Spades") return false;
    if (card.second != winner.second) return false;
    return card.first > winner.first;
}


// Like key=lambda card: card[0]; ties retain the first card
// ease of use to check if a given card's rank is greater than another's
bool rank_less(const Card& a, const Card& b) { return a.first < b.first; }

Card play_card(const Hand& hand, const Trick& trick, bool spades_broken) {
    const auto choices = legal_cards(hand, trick, spades_broken);
    if (choices.empty()) throw std::invalid_argument("Cannot play an empty hand");
    if (trick.empty()) return *std::max_element(choices.begin(), choices.end(), rank_less);
    Hand winning_options, non_spades;
    // Preserves Python's policy: compare against the lead card, even if beaten.
    for (const auto& card : choices) {
        if (beats(card, trick.front().second, trick.front().second.second)) winning_options.push_back(card);
        if (card.second != "Spades") non_spades.push_back(card);
    }
    if (!winning_options.empty())
        return *std::min_element(winning_options.begin(), winning_options.end(), rank_less);
    const auto& discards = non_spades.empty() ? choices : non_spades;
    return *std::min_element(discards.begin(), discards.end(), rank_less);
}

// Available for future use; Python's simulation also does not call this policy.
Card play_card_nil(const Hand& hand, const Trick& trick, bool spades_broken) {
    const auto choices = legal_cards(hand, trick, spades_broken);
    if (choices.empty()) throw std::invalid_argument("Cannot play an empty hand");
    if (!trick.empty()) {
        Hand safe;
        for (const auto& card : choices)
            if (!beats(card, trick.front().second, trick.front().second.second)) safe.push_back(card);
        if (!safe.empty()) return *std::max_element(safe.begin(), safe.end(), rank_less);
    }
    return *std::min_element(choices.begin(), choices.end(), rank_less);
}

std::pair<int, bool> play_trick(Hands& hands, int start_player, bool spades_broken) {
    Trick trick;
    for (int i = 0; i < 4; ++i) {
        const int player = (start_player + i) % 4;
        auto& hand = hands[player]; // Mutable reference: remove from the actual hand.
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

int play_game(const Hand& my_hand, const Hand& cards_left, std::mt19937& rng) {
    if (my_hand.size() != 13 || cards_left.size() != 39)
        throw std::invalid_argument("Expected 13 cards in hand and 39 remaining cards");
    auto shuffled = cards_left; // Equivalent to .copy().
    std::shuffle(shuffled.begin(), shuffled.end(), rng);
    Hands hands = {my_hand, Hand(shuffled.begin(), shuffled.begin() + 13),
        Hand(shuffled.begin() + 13, shuffled.begin() + 26), Hand(shuffled.begin() + 26, shuffled.end())};
    std::array<int, 4> tricks_won{};
    int start_player = 0;
    bool spades_broken = false;
    for (int i = 0; i < 13; ++i) {
        const auto result = play_trick(hands, start_player, spades_broken);
        ++tricks_won[result.first];
        start_player = result.first;
        spades_broken = result.second;
    }
    return tricks_won[0];
}

double est_tricks(const Hand& my_hand, int num_trials, std::mt19937& rng) {
    if (num_trials <= 0) throw std::invalid_argument("num_trials must be positive");
    Hand remaining;
    for (const auto& card : Deck())
        if (std::find(my_hand.begin(), my_hand.end(), card) == my_hand.end()) remaining.push_back(card);
    double total = 0;
    for (int i = 0; i < num_trials; ++i) total += play_game(my_hand, remaining, rng);
    return total / num_trials;
}

std::vector<int> score_bids(const std::vector<int>& results) {
    if (results.empty()) throw std::invalid_argument("trial_results must contain at least one result");
    std::vector<int> scores;
    for (int bid = 0; bid < 14; ++bid) {
        double total = 0;
        for (int tricks : results) {
            if (bid == 0) total += tricks == 0 ? 100 : -100;
            else if (tricks >= bid) total += 10 * bid + tricks - bid;
            else total -= 10 * bid;
        }
        // floor matters for negative averages: integer division would truncate.
        scores.push_back(static_cast<int>(std::floor(total / results.size())));
    }
    return scores;
}

int main() {
    constexpr int num_trials = 10000;
    std::mt19937 rng(std::random_device{}());

    auto deck = Deck();
    std::shuffle(deck.begin(), deck.end(), rng);

    const Hand my_hand(deck.begin(), deck.begin() + 13);
    const Hand remaining(deck.begin() + 13, deck.end());

    std::vector<int> results;
    results.reserve(num_trials);

    for (int i = 0; i < num_trials; ++i) { 
        results.push_back(play_game(my_hand, remaining, rng));
    };

    const double mean = std::accumulate(results.begin(), results.end(), 0.0) / num_trials;

    std::cout << "Hand: ";
    for (const auto& card : my_hand) { 
        std::cout << '(' << card.first << ", " << card.second << ") ";
    };

    std::cout << "\nEstimated Tricks Taken: " << mean << '\n';

    const auto scores = score_bids(results);
    std::cout << "List of average scores for each bid: ";
    for (int score : scores) std::cout << score << ' ';

    const auto best = std::max_element(scores.begin(), scores.end());
    const auto best_bid = std::distance(scores.begin(), best);
    std::cout << "\nRecommended Bid of " << best_bid << " with an average score of " << *best << '\n';
}
