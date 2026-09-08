# Spades Monte Carlo Simulation

A simple Monte Carlo simulation that estimates how many tricks any given hand might take in the card game spades, and recommends a bid based on simulated scores. Includes an original Python implementation and a C++ port built as a learning project.

Both versions generate a random 13-card hand, keep it fixed, and simulate 10,000 deals of the remaining cards. They output the simulated hand, estimated tricks taken, average scores for bids from 0 to 13, and a recommended bid.

## Python

Source: [spades_sim.py](spades_sim.py)

Requires Python 3, NumPy, and Matplotlib. From the repository root:

```sh
python -m pip install numpy matplotlib
python spades_sim.py
```

The script also calculates a running mean; uncomment the convergence plotting block to display it.

## C++

Source: [spades-monte-carlo.cpp](c++/spades-monte-carlo/spades-monte-carlo.cpp)

Open [the solution](c++/spades-monte-carlo/spades-monte-carlo.slnx) in a version of Visual Studio that supports `.slnx`, with C++ development tools installed, then build and run the project. The source uses only the C++ standard library.

## Configuration and limitations

Change `num_trials` in the Python script or in C++'s `main()` to adjust the simulation count.

The simulations enforce following suit and restrictions on leading spades, but use simple card-playing heuristics. Players compare potential plays the current winning card, and player 0 always leads the first trick. Partnership strategy, team scoring, and accumulated bag penalties are not yet modeled. Nil bids are scored, but the dedicated nil-playing policy hasn't been implemented in simulations.
