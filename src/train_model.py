# feature creation, splitting, training, eval, timing, etc.
# all in this file. can separate later if helpful

#imports and const

import csv
import sys


# general checks for full dataset csv

def dataset_checks(path):
    with open(path, newline = "") as file:
        reader = csv.DictReader(file)
        

#card-id conversion

# path should be the data from `spades_sim.py`
# at the moment should be pilot_1000.csv
def extract_features(card_ids):

    #initial checks
    if len(card_ids) != 13:
        raise SystemExit("Number of Card IDs should be 13")
    
    if len(set(card_ids)) != 13:
        raise SystemExit("List of Card IDs should not contain duplicate IDs")
    
    if any(num < 0 or num > 51 for num in card_ids):
        raise SystemExit("All Card IDs should be between 0 and 51")

    # 0 = Spades, 1 = Hearts, 2 = Diamonds, 3 = Clubs
    suit_counts = [0,0,0,0]
    suit_high_cards = [0,0,0,0]

    # 0 = Jacks, 1 = Queens, 2 = Kings, 3 = Aces
    face_card_counts = [0,0,0,0]

    # same as suit counts, keeping track of point totals
    # points assigned as J = 1pt, Q = 2pt, K = 3pt, A = 4pt
    high_card_suit_totals = [0,0,0,0]

    for card in card_ids:
        suit_index = card // 13
        rank = card % 13 + 2

        suit_counts[suit_index] += 1
        if rank >= 11:
            face_card_counts[rank-11] += 1
            high_card_suit_totals[suit_index] += (rank - 10)
            suit_high_cards[suit_index] += 1

    high_spade_count = suit_high_cards[0]

    void_count = sum(1 for suit in suit_counts if suit == 0)
    singleton_count = sum(1 for suit in suit_counts if suit == 1)

    assert sum(suit_counts)==13, "total suit count does not equal 13"

    # return all 15 features from the card_ids,
    # with suit counts and high card totals per suit in lists
    return [
        suit_counts,
        high_card_suit_totals,
        face_card_counts[0],
        face_card_counts[1],
        face_card_counts[2],
        face_card_counts[3],
        void_count,
        singleton_count,
        high_spade_count,
    ]

def load_dataset(path):

    x = []
    y = []

    with open(path, newline= "") as file:
        reader = csv.DictReader(file)

        for row in reader:

            card_ids = [int(row[f"Card {number}"]) for number in range(1,14)]
            features = extract_features(card_ids)
            x.append(features)

            rec_bid = int(row["Recommended Bid"])
            y.append(rec_bid)

        #checks

        if (len(x) != 1000 or len(y) != 1000):
            raise SystemExit("length of loaded dataset features does not equal 1000")

    return [x,y]



#feature extraction for a single hand

#dataset loading and validation

#train/test split

#baseline evaluation

#model cross-validation and selection

#final held-out eval

#error analysis and score regret

#latency benchmark

def main():
    print(extract_features([1, 10, 15, 18, 23, 24, 28, 37, 40, 43, 46, 47, 51]))

main()