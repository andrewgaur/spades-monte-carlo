# analysis separate from simulator script
# intended to determine how consistent the 
# monte carlo labels from the simulator are

from spades_sim import DECK, evaluate_hand
import csv
import random

def test_hand(hand, seed, trials):
    
    random.seed(seed)
    
    best_bid, scores = evaluate_hand(hand, trials)
    return best_bid, scores

    

def main():
    path = "test_data/test_data_3.csv"
    path_out = "stability_results.csv"
    seed_list = [10, 12, 15, 29, 84]

    with (
        open(path, newline = "") as file,
        open(path_out, newline = "", mode="x") as file_out
    ):
        reader = csv.DictReader(file)
        writer = csv.writer(file_out)

        trials = [1000,10000]

        writer.writerow([
            "Hand_ID",
            "Seed",
            "Trials",
            "Recommended Bid",
            "Best Score",
            "Second Best Score",
            "Score Gap",
        ])

        for hand_id, row in enumerate(reader, start = 1):
            hand = [
                DECK[int(row[f"Card {number}"])]
                for number in range(1,14)
            ]

            for num_trials in trials:
                for seed in seed_list:

                    rec_bid, scores = test_hand(hand, seed, num_trials)
                    high_score = sorted(scores)[-1]
                    second_high = sorted(scores)[-2]
                    score_gap = high_score - second_high

                    writer.writerow([
                        hand_id,
                        seed,
                        num_trials,
                        rec_bid,
                        high_score,
                        second_high,
                        score_gap,
                    ])

                    print(f"seed {seed} ({trials.index(num_trials)}) written")

                print(f"num_trials {num_trials} done")
                                

if __name__ == "__main__":
    main()
