# feature creation, splitting, training, eval, timing, etc.
# all in this file. can separate later if helpful

#imports and const

import csv
from pathlib import Path
import sys
from sklearn.model_selection import train_test_split
import numpy as np

#single hand feature extraction

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
        *suit_counts,
        *high_card_suit_totals,
        *face_card_counts,
        void_count,
        singleton_count,
        high_spade_count,
    ]

# dataset loading and validation

def load_dataset(path):

    x = []
    y = []

    with open(path, newline= "") as file:
        reader = csv.DictReader(file)

        seen_hands = set()
        row_count = 0

        for row in reader:
            row_count += 1

            # req checks
            try:
                card_ids = [int(row[f"Card {number}"]) for number in range(1,14)]
                rec_bid = int(row["Recommended Bid"])
                scores = [float(row[f"Bid {bid} Score"]) for bid in range(14)]
            except (KeyError, TypeError, ValueError):
                print(f"missing or invalid value in row {row}")
                continue

            if rec_bid < 0 or rec_bid > 13:
                print(f"recommended bid in row {row} must be within target range of 0 to 13")
                continue

            sorted_ids = tuple(sorted(card_ids))
            if sorted_ids in seen_hands:

                #hand is already seen, so there is a duplicate
                print(f"hand in row{row} is a duplicate")
                continue

            else:
                seen_hands.add(sorted_ids)

            #features

            features = extract_features(card_ids)
            assert len(features) == 15, "features should have a length of 15"

            best_bid = max(range(14), key=scores.__getitem__)
            if rec_bid != best_bid:
                print(f"recommended bid does not match the highest score in row {row}")
                continue
            
            x.append(features)
            y.append(rec_bid)

        #checks

        if row_count != 1000:
            raise SystemExit(f"dataset should contain 1000 rows, found {row_count}")

        if (len(x) != row_count or len(y) != row_count):
            raise SystemExit(f"length of loaded dataset features does not equal {row_count}")

    return x, y


# train/test split

def split_dataset(x,y):
    indices = list(range(len(x)))

    # train_test_split
    # scikit learn applies same shuffle to all inputs
    # so all values stay together in the same index/row
    (
        x_train,
        x_test,
        y_train,
        y_test,
        train_indices,
        test_indices
    ) = train_test_split(
        x,
        y,
        indices,
        test_size = 0.20,
        random_state = 42
    )

    # check correct split lengths

    assert len(x_train) == len(y_train) == len(train_indices) == 800, "training set != 800"
    assert len(x_test) == len(y_test) == len(test_indices) == 200, "test set != 200"

    #make sure no row is in both groups
    assert set(train_indices).isdisjoint(test_indices)

    #no disapperared rows
    assert set(train_indices) | set(test_indices) == set(indices)

    return x_train, x_test, y_train, y_test, train_indices, test_indices

    # return the six resulting lists

#baseline evaluation

def baseline_eval(y_train):
    # find median bid from y_train only
    # constant median baseline

    med_bid = np.median(y_train)

    bid_predictions = [med_bid for _ in y_train]

    # results
    # mean absolute error
    median_base_MAE = np.mean(np.abs(np.array(y_train) - med_bid))

    # exact match rate
    median_base_EMR = (y_train.count(2)) / len(y_train)

    # within one accuracy
    # find total count of numbers within 1 of the median bid,
    # divided by length of bid training set to find accuracy percentage

    median_base_WOA = (sum(1 for bid in y_train if abs(bid - med_bid) <= 1)) / len(y_train)

    



#model cross-validation and selection

#final held-out eval

#error analysis and score regret

#latency benchmark

def main(DATA_PATH):
    x, y = load_dataset(DATA_PATH)
    split_results = split_dataset(x, y)
    for item in split_results:
        print(len(item))

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    data_path = root / "data" / "test_data" / "pilot_1000.csv"
    main(str(data_path))
