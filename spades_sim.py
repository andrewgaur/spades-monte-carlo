import random
import sys
from time import perf_counter
import csv

SUITS = ["Spades", "Hearts", "Diamonds", "Clubs"]
DECK = [(rank, suit) for suit in SUITS for rank in range(2, 15)]


def legal_cards(hand, trick, spades_broken):
    if trick:
        cards_in_suit = [card for card in hand if card[1] == trick[0][1][1]]
        return cards_in_suit or hand
    if not spades_broken:
        not_spades = [card for card in hand if card[1] != "Spades"]
        if not_spades:
            return not_spades
    return hand


def beats(card, winning_card, led_suit):
    if card[1] == "Spades" and winning_card[1] != "Spades":
        return True
    if card[1] != "Spades" and winning_card[1] == "Spades":
        return False
    if card[1] != winning_card[1]:
        return False
    return card[0] > winning_card[0]


def winning_play(trick):
    winner = trick[0]
    led_suit = winner[1][1]
    for play in trick[1:]:
        if beats(play[1], winner[1], led_suit):
            winner = play
    return winner


def play_card(hand, trick, spades_broken):
    choices = legal_cards(hand, trick, spades_broken)
    if not choices:
        raise ValueError("Cannot play an empty hand")
    if not trick:
        return max(choices, key=lambda card: card[0])

    winning_card = winning_play(trick)[1]
    led_suit = trick[0][1][1]
    winning_options = [card for card in choices if beats(card, winning_card, led_suit)]
    if winning_options:
        return min(winning_options, key=lambda card: card[0])
    non_spades = [card for card in choices if card[1] != "Spades"]
    return min(non_spades or choices, key=lambda card: card[0])


def play_card_nil(hand, trick, spades_broken):
    choices = legal_cards(hand, trick, spades_broken)
    if not choices:
        raise ValueError("Cannot play an empty hand")
    if trick:
        winning_card = winning_play(trick)[1]
        led_suit = trick[0][1][1]
        safe = [card for card in choices if not beats(card, winning_card, led_suit)]
        if safe:
            return max(safe, key=lambda card: card[0])
    return min(choices, key=lambda card: card[0])


def play_trick(hands, start_player, spades_broken):
    trick = []
    for i in range(4):
        player = (start_player + i) % 4
        card = play_card(hands[player], trick, spades_broken)
        hands[player].remove(card)
        trick.append((player, card))
        if card[1] == "Spades":
            spades_broken = True

    winning_player, _ = winning_play(trick)
    return winning_player, spades_broken


def play_dealt_game(dealt_hands, start_player=0, spades_broken=False):
    if len(dealt_hands) != 4 or any(len(hand) != 13 for hand in dealt_hands):
        raise ValueError("Expected four 13-card hands")
    hands = [hand.copy() for hand in dealt_hands]
    tricks_won = [0, 0, 0, 0]
    for _ in range(13):
        winner, spades_broken = play_trick(hands, start_player, spades_broken)
        tricks_won[winner] += 1
        start_player = winner
    if sum(tricks_won) != 13:
        raise AssertionError("A dealt game must award 13 tricks")
    return tricks_won


def play_game(my_hand, cards_left):
    shuffled = cards_left.copy()
    random.shuffle(shuffled)
    return play_dealt_game([my_hand, shuffled[:13], shuffled[13:26], shuffled[26:]])[0]


def score_bid_totals(results):
    if not results:
        raise ValueError("trial_results must contain at least one result")
    return [sum((100 if tricks == 0 else -100) if bid == 0 else
                (10 * bid + tricks - bid if tricks >= bid else -10 * bid)
                for tricks in results) for bid in range(14)]


def score_bids(results):
    totals = score_bid_totals(results)
    return [total / len(results) for total in totals]


def load_fixtures(path):
    fixtures = []
    with open(path, encoding="ascii") as fixture_file:
        for line_number, line in enumerate(fixture_file, 1):
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            values = [int(value) for value in line.split()]
            if len(values) != 54 or values[0] not in range(4) or values[1] not in (0, 1):
                raise ValueError(f"Invalid fixture header or length on line {line_number}")
            card_ids = values[2:]
            if sorted(card_ids) != list(range(52)):
                raise ValueError(f"Fixture line {line_number} must contain every card ID once")
            cards = [(card_id % 13 + 2, SUITS[card_id // 13]) for card_id in card_ids]
            fixtures.append(([cards[i:i + 13] for i in range(0, 52, 13)], values[0], bool(values[1])))
    if not fixtures:
        raise ValueError("Fixture file is empty")
    return fixtures


def benchmark(path, games, repeats):
    fixtures = load_fixtures(path)
    expected = [play_dealt_game(*fixture) for fixture in fixtures]
    signature = ";".join(",".join(map(str, tricks)) for tricks in expected)
    print(f"CHECK fixtures={len(fixtures)} signature={signature}")

    for i in range(games):
        play_dealt_game(*fixtures[i % len(fixtures)])

    for repeat in range(1, repeats + 1):
        results = []
        checksum = 0
        start = perf_counter()
        for i in range(games):
            tricks = play_dealt_game(*fixtures[i % len(fixtures)])
            results.append(tricks[0])
            checksum += sum((player + 1) * count for player, count in enumerate(tricks))
        seconds = perf_counter() - start
        totals = score_bid_totals(results)
        best_bid = max(range(14), key=totals.__getitem__)
        print(f"TIME repeat={repeat} games={games} seconds={seconds:.9f} "
              f"checksum={checksum} best_bid={best_bid} score_totals={','.join(map(str, totals))}")



def evaluate_hand(my_hand, trials):
    remaining = [card for card in DECK if card not in my_hand]
    results = [play_game(my_hand, remaining) for _ in range(trials)]
    scores = score_bids(results)
    best_bid = max(range(14), key=scores.__getitem__)
    return best_bid, scores


def generate_dataset(path, length, trials):
    row_id = 0
    seed = 100
    random.seed(seed)
    deck = DECK.copy()

    score_columns = [f"Bid {bid} Score" for bid in range(14)]
    card_columns = [f"Card {number}" for number in range(1, 14)]
    
    with open(path, mode='x', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            "Row ID",
            "Seed",
            *card_columns,
            "Number of Trials",
            "Recommended Bid",
            *score_columns,
        ])

        for _ in range(length):

            row_id += 1
            random.shuffle(deck)

            my_hand = deck[:13]
            best_bid, scores = evaluate_hand(my_hand, trials)

            hand = []
            for card in my_hand:
                card_id = DECK.index(card)
                hand.append(card_id)

            hand.sort()
            
            print(f"generated row {row_id} of {length}")

            new_row = [
                row_id,
                seed,
                *hand,
                trials,
                best_bid,
                *scores
                ]
            # Append the numbers as a single new row
            writer.writerow(new_row)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--benchmark":
        if len(sys.argv) != 5:
            raise SystemExit("usage: python spades_sim.py --benchmark FIXTURES GAMES REPEATS")
        games, repeats = map(int, sys.argv[3:])
        if games <= 0 or repeats <= 0:
            raise SystemExit("GAMES and REPEATS must be positive")
        benchmark(sys.argv[2], games, repeats)
        return

    ## recall usage for --generate-dataset

    if len(sys.argv) > 1 and sys.argv[1] == "--dataset-usage":
        raise SystemExit("python SCRIPT_PATH --generate-dataset OUTPUT_PATH DATASET_LENGTH NUM_TRIALS")

    if len(sys.argv) > 1 and sys.argv[1] == "--generate-dataset":
        if len(sys.argv) != 5:
            raise SystemExit("usage: python spades_sim.py --generate-dataset PATH LENGTH TRIALS")

        len_dataset, trials = map(int, sys.argv[3:])
        if len_dataset <= 0 or trials <= 0: 
            raise SystemExit("Dataset length and trials must be positive")

        generate_dataset(sys.argv[2], len_dataset, trials)
        return

    num_trials = 10000
    deck = DECK.copy()
    random.shuffle(deck)
    my_hand, remaining = deck[:13], deck[13:]
    results = [play_game(my_hand, remaining) for _ in range(num_trials)]
    scores = score_bids(results)
    best_bid = max(range(14), key=scores.__getitem__)
    print("Hand:", my_hand)
    print("Estimated Tricks Taken:", sum(results) / num_trials)
    print("List of average scores for each bid:", scores)
    print("Recommended Bid of", best_bid, "with an average score of", scores[best_bid])


if __name__ == "__main__":
    main()
