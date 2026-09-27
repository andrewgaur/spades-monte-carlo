# feature creation, splitting, training, eval, timing, etc.
# all in this file. can separate later if helpful

#imports and const

import csv
from pathlib import Path
import sys
import numpy as np

from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import KFold, cross_val_score, train_test_split


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
    score_rows = []

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
            score_rows.append(scores)

        #checks

        if row_count != 1000:
            raise SystemExit(f"dataset should contain 1000 rows, found {row_count}")

        if (len(x) != row_count or len(y) != row_count or len(score_rows) != row_count):
            raise SystemExit(f"length of loaded dataset features does not equal {row_count}")

    return x, y, score_rows


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

def prediction_metrics(actual, predicted):
    actual = np.array(actual)
    predicted = np.array(predicted)

    # mean absolute error
    mae = np.mean(np.abs(actual-predicted))
    # exact match rate
    emr = np.mean(actual == predicted)
    # within one accuracy
    woa = np.mean(np.abs(actual - predicted) <= 1)

    return mae, emr, woa


def baseline_eval(x_train, y_train):
    # find median bid from y_train only
    # constant median baseline


    # make both prediction lists
    # predicted bid based on median bid
    med_bid = int(np.median(y_train))
    median_predictions = [med_bid for _ in y_train]
    
    high_bid_predictions = []
    # and predicted bid based on high card count
    for hand in x_train:
        q, k, a = hand[9:12]
        high_count = q + k + a
        high_bid_predictions.append(high_count)
    
    # return metrics/results for each

    median_metrics = prediction_metrics(y_train, median_predictions)
    high_card_metrics = prediction_metrics(y_train, high_bid_predictions)

    return median_metrics, high_card_metrics
    

# model cross validation and selection
def cross_val_models(x_train, y_train):
    # should ONLY recieve training lists, never the test data

    # Ridge works better when features have comparable ranges
    # features currently have diff ranges, so StandardScaler rescales them
    # before Ridge fits

    ridge = make_pipeline(
        StandardScaler(),
        Ridge()
    )

    boosting = HistGradientBoostingRegressor(
        random_state = 42
    )

    # fixed seed to make the folds reproducible
    folds = KFold(
        n_splits = 5,
        shuffle = True,
        random_state=42
    )

    # and evaluate each model
    ridge_scores = cross_val_score(
        ridge,
        x_train,
        y_train,
        cv=folds,
        scoring = "neg_mean_absolute_error"
    )

    ridge_errors = -ridge_scores
    ridge_mean = np.mean(ridge_errors)
    ridge_std = np.std(ridge_errors)

    boosting_scores = cross_val_score(
        boosting,
        x_train,
        y_train,
        cv = folds,
        scoring = "neg_mean_absolute_error"
    )

    boosting_errors = -boosting_scores
    boosting_mean = np.mean(boosting_errors)
    boosting_std = np.std(boosting_errors)

    return ridge_mean, ridge_std, boosting_mean, boosting_std


#final held-out eval

def final_eval(x_train, y_train, x_test, y_test):
    # recreate the models

    ridge = make_pipeline(
        StandardScaler(),
        Ridge()
    )

    # fit ridge model
    ridge.fit(x_train, y_train)
    # test data from x_test and y_test must NEVER appear in .fit()

    #generate test predictions
    ridge_raw_predictions = ridge.predict(x_test)

    ridge_continuous_mae = np.mean(np.abs(np.array(y_test) - ridge_raw_predictions))

    ridge_bid_predictions = np.clip(np.rint(ridge_raw_predictions), 0, 13).astype(int)

    ridge_metrics = prediction_metrics(y_test, ridge_bid_predictions)

    median_bid = int(np.median(y_train)) 
    median_test_predictions = [median_bid] * len(y_test)

    median_test_metrics = prediction_metrics(
        y_test,
        median_test_predictions,
    )

    return (
    ridge,
    ridge_continuous_mae,
    ridge_metrics,
    median_test_metrics,
    ridge_bid_predictions,
)

#error analysis and score regret

def calculate_regret(score_rows, test_indices, y_test, predictions):
    regrets = []

    for i in range(len(test_indices)):
        original_index = test_indices[i]
        scores = score_rows[original_index]

        teacher_bid = y_test[i]
        predicted_bid = predictions[i]

        teacher_score = scores[teacher_bid]
        predicted_score = scores[predicted_bid]

        regret = teacher_score - predicted_score
        regrets.append(regret)
        

    return regrets


#latency benchmark

def main(DATA_PATH):
    x, y, score_rows = load_dataset(DATA_PATH)
    (
        x_train,
        x_test,
        y_train,
        y_test,
        train_indices,
        test_indices,
    ) = split_dataset(x, y)

    (
        ridge,
        ridge_continuous_mae,
        ridge_metrics,
        median_test_metrics,
        ridge_bid_predictions,
    ) = final_eval(x_train, y_train, x_test, y_test)

    ridge_regrets = calculate_regret(
        score_rows,
        test_indices,
        y_test,
        ridge_bid_predictions,
    )

    assert len(ridge_regrets) == len(y_test)
    assert all(regret >= 0 for regret in ridge_regrets)

    mean_regret = np.mean(ridge_regrets)
    median_regret = np.median(ridge_regrets)
    max_regret = np.max(ridge_regrets)
    zero_regret_rate = np.mean(np.isclose(ridge_regrets, 0))


    ridge_mae, ridge_emr, ridge_woa = ridge_metrics
    median_mae, median_emr, median_woa = median_test_metrics

    print("Selected Ridge held-out results:")
    print(f"Continuous MAE: {ridge_continuous_mae:.4f}")
    print(f"Rounded bid MAE: {ridge_mae:.4f}")
    print(f"Exact match: {ridge_emr:.2%}")
    print(f"Within one: {ridge_woa:.2%}")

    print("\nMedian held-out baseline:")
    print(f"MAE: {median_mae:.4f}")
    print(f"Exact match: {median_emr:.2%}")
    print(f"Within one: {median_woa:.2%}")

    print("\nRidge score regret:")
    print(f"Mean regret: {mean_regret:.4f}")
    print(f"Median regret: {median_regret:.4f}")
    print(f"Maximum regret: {max_regret:.4f}")
    print(f"Zero-regret rate: {zero_regret_rate:.2%}")

    worst_position = int(np.argmax(ridge_regrets))
    worst_original_index = test_indices[worst_position]
    worst_scores = score_rows[worst_original_index]

    print("\nWorst Ridge prediction:")
    print(f"Original dataset index: {worst_original_index}")
    print(f"Teacher bid: {y_test[worst_position]}")
    print(f"Predicted bid: {ridge_bid_predictions[worst_position]}")
    print(f"Teacher score: {worst_scores[y_test[worst_position]]:.4f}")
    print(f"Predicted score: {worst_scores[ridge_bid_predictions[worst_position]]:.4f}")
    print(f"Regret: {ridge_regrets[worst_position]:.4f}")
    
    #for item in split_results:
    #    print(len(item))

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    data_path = root / "data" / "test_data" / "pilot_1000.csv"
    main(str(data_path))
