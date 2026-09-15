# Spades Monte Carlo Simulation

A simple Monte Carlo simulation that estimates how many tricks any given hand might take in the card game spades, and recommends a bid based on simulated scores. Includes an original Python implementation and a C++ port built as a learning project.

Both versions generate a random 13-card hand, keep it fixed, and simulate 10,000 deals of the remaining cards. They output the simulated hand, estimated tricks taken, average scores for bids from 0 to 13, and a recommended bid. For benchmarking, the program also runs an untimed warmup before each sample.

## Benchmark result

The C++ version completed the checked simulation workload 4.94 times faster than Python on the test machine. Across seven samples of 100,000 identical dealt games, Python's median runtime was 6.482 seconds and C++'s median was 1.311 seconds.

Both implementations matched on all four trick totals for each shared fixture, the recommended bid, and every bid score total. See [benchmark_results.md](benchmark_results.md) for the raw measurements and machine details.

## Python

Source: [spades_sim.py](spades_sim.py)

Requires Python 3. From the repository root:

```sh
python spades_sim.py
```

## C++

Source: [spades-monte-carlo.cpp](c++/spades-monte-carlo/spades-monte-carlo.cpp)

Open [the solution](c++/spades-monte-carlo/spades-monte-carlo.slnx) in a version of Visual Studio that supports `.slnx`, with C++ development tools installed, then build and run the project. The source uses only the C++ standard library.

## Configuration and limitations

Change `num_trials` in the Python script or in C++'s `main()` to adjust the simulation count.

The simulations enforce following suit and restrictions on leading spades, but use simple card-playing heuristics. Players compare candidate cards against the current winning card and play the lowest card that can take the trick. Player 0 starts the first trick during the normal random simulation. Benchmark fixtures vary the starting player and initial spades state.

Partnership strategy, team scoring, and accumulated bag penalties are not modeled. Nil bids are scored, but simulations do not use the separate nil-playing helper. Replaying benchmark fixtures measures simulation throughput and does not generate new Monte Carlo samples.
