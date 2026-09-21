# analysis separate from simulator script
# intended to determine how consistent the 
# monte carlo labels from the simulator are

from spades_sim import DECK, evaluate_hand
import csv
import random
import sys
import numpy



# bring results from specific seed and hand using `spades_sim.py` logic
def test_hand(hand, seed, trials):
    
    random.seed(seed)
    
    best_bid, scores = evaluate_hand(hand, trials)
    return best_bid, scores

# list the bids for each seed, sorted by hand id and trials
# ie (hand id, number of trials) -> {bid for seed 1, bid for seed 2, bid for seed 3, etc}

def bids_by_trial(path):
    bids_by_hand_trials = {}

    with (open(path, newline = "") as file):
        reader = csv.DictReader(file)

        for row in reader:
            # hand_id equals the value in the row at the index "Hand_ID", translated to an int
            hand_id = int(row["Hand_ID"])
            trials = int(row["Trials"])
            bid = int(row["Recommended Bid"])

            key = (hand_id, trials)
            if key not in bids_by_hand_trials:
                bids_by_hand_trials[key] = []

            bids_by_hand_trials[key].append(bid)

    return bids_by_hand_trials


# lists the bids for each number of trials, sorted by hand id and seed
# ie (hand id, seed) -> {1000: bid, 5000: bid}

def bids_by_seed(path):
    bids_by_hand_seed = {}
    with open(path, newline = "") as file:
        reader = csv.DictReader(file)

        for row in reader:

            hand_id = int(row["Hand_ID"])
            seed = int(row["Seed"])
            bid = int(row["Recommended Bid"])

            key = (hand_id, seed)
            if key not in bids_by_hand_seed:
                bids_by_hand_seed[key] = []

            bids_by_hand_seed[key].append(bid)

    return bids_by_hand_seed
        

def score_gap_analysis(stability_results, trial_sorted, seed_sorted):
    #trial sorted input should be trial_sort_groups
    #seed sorted input should be seed_sort_groups

    unstable_trial_keys = {
        key for key, bids in seed_sorted.items()
        if len(set(bids)) != 1
    }

    unstable_seed_keys = {
        key for key, bids in trial_sorted.items()
        if len(set(bids)) != 1
    }

    stable_seed_gaps = []
    unstable_seed_gaps = []

    stable_trial_gaps = []
    unstable_trial_gaps = []

    with open(stability_results, newline = "") as file:
        reader = csv.DictReader(file)

        for row in reader:

            hand_id = int(row["Hand_ID"])
            seed = int(row["Seed"])
            trial = int(row["Trials"])
            score_gap = float(row["Score Gap"])

            trial_key = (hand_id, trial)
            seed_key = (hand_id, seed)

            if trial_key in unstable_seed_keys:
                unstable_seed_gaps.append(score_gap)
            else:
                stable_seed_gaps.append(score_gap)

            if seed_key in unstable_trial_keys:
                unstable_trial_gaps.append(score_gap)
            else:
                stable_trial_gaps.append(score_gap)
            # 

    #return [unstable_seed_keys, unstable_trial_keys]
    outputs = {
        "stable_seed_gaps": stable_seed_gaps,
        "unstable_seed_gaps": unstable_seed_gaps,
        "stable_trial_gaps": stable_trial_gaps,
        "unstable_trial_gaps": unstable_trial_gaps,
    }

    for name, output in outputs.items():

        print(
            f"{name} Count: {len(output)}, "
            f"Mean Score Gap: {round(numpy.mean(output),3)}, "
            f"Median Score Gap: {round(numpy.median(output),3)}"
            )

    return



def stability_analysis(path):
    trial_sort_groups = bids_by_trial(path)
    seed_sort_groups = bids_by_seed(path)

    # check if all five seeds recommended the same bid for each hand and trial count
    all_seeds_agree = True
    stable_seed_groups = 0

    for key,bids in trial_sort_groups.items():
        if len(set(bids)) == 1:
            stable_seed_groups += 1
        if len(set(bids)) != 1:
            all_seeds_agree = False
            print(f"Seeds disagree: {key}, {bids}")    

    seed_agree_rate = stable_seed_groups / len(trial_sort_groups)

    # check if both trial counts recommend the same bid for each hand and seed
    all_trials_agree = True
    stable_trial_groups = 0

    for key,bids in seed_sort_groups.items():
        if len(set(bids)) == 1:
            stable_trial_groups += 1

        if len(set(bids)) != 1:
            all_trials_agree = False
            print(f"Trial counts disagree: {key}, {bids}")

    trial_agree_rate = stable_trial_groups / len(seed_sort_groups)


    ## need score gap analysis logic??
    # bring using `unstable_keys` ??
    

    # return all agreement values for each seed and trial

    print(f"All five seeds agree for every hand and trial: {all_seeds_agree}")
    print(f"All trial counts agree for every hand and seed: {all_trials_agree}")

    print(
        f"Seed agreement: {stable_seed_groups}/{len(trial_sort_groups)} "
        f"({seed_agree_rate:.1%})"
    )

    print(
        f"Trial count agreement: {stable_trial_groups}/{len(seed_sort_groups)} "
        f"({trial_agree_rate:.1%})"
    )

    print("\nScore Gap Analysis:\n")
    score_gap_analysis(path, trial_sort_groups, seed_sort_groups)
    
    return
    

def stability_data(data_path, path_out):
    path = data_path
    seed_list = [61, 12, 38, 29, 84]

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
    return

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--get-data":
        if len(sys.argv) != 4:
            raise SystemExit("usage: python teacher_stability.py --get-data DATASET_PATH PATH_OUT")

        stability_data(sys.argv[2], sys.argv[3])
        return

    if len(sys.argv) > 1 and sys.argv[1] == "--analysis":
        if len(sys.argv) != 3:
            raise SystemExit("usage: python teacher_stability.py --analysis STABILITY_DATA")
        
        stability_analysis(sys.argv[2])
        return

    if len(sys.argv) == 1:
        raise SystemExit("teacher_stability.py requires at least one argument. try:" \
        "\n--get-data DATASET_PATH PATH_OUT" \
        "\n--analysis STABILITY_DATA")

if __name__ == "__main__":
    main()
