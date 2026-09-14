# Python and C++ benchmark results

Run date: September 13, 2026

The C++ implementation completed the simulation in 1.1576963 seconds at the median. Python completed it in 5.563081 seconds. The median runtime ratio was 4.8053, so C++ ran about 4.81 times as many equivalent dealt games per second on this machine.


## Correctness check

Both implementations replayed the same nine deals from `benchmark_fixtures.txt`. They matched on all four trick totals for every fixture. Every game awarded 13 tricks. They also matched on the recommended bid and exact integer score totals during every measured run.

The fixture set includes different starting players, both initial spades states, and a deal where player 0 wins zero tricks. A separate regression check confirmed that `[1, 12, 10, 10, 6, 6, 5, 3, 1, 12]` selects bid 5 using exact mean scores. The old floor before selection incorrectly chose bid 3.

Fixture signature:

```text
3,4,2,4;5,4,1,3;6,2,2,3;6,2,3,2;4,1,4,4;3,3,4,3;1,8,3,1;2,3,4,4;0,4,4,5
```


## Method

Each sample replayed 100,000 dealt games. Each implementation ran one untimed 100,000 game warmup immediately before its measured batch. The seven samples alternated Python then C++.

Timing includes per game state copies, simulation, result retention, and checksum accumulation. It excludes fixture loading, bid scoring, compilation, imports, and console output.

The C++ project used its Release x64 configuration with whole program optimization enabled.


## Raw measurements

```text
Sample  Python seconds  C++ seconds  Python/C++ ratio
1       5.5118922       1.1241900    4.90299
2       5.6450898       1.1401566    4.95115
3       5.5155670       1.1454017    4.81540
4       5.6487818       1.1668535    4.84104
5       5.6419480       1.1576963    4.87343
6       5.5585850       1.1697273    4.75203
7       5.5630810       1.1938399    4.65982
```

Python median: 5.5630810 seconds, range 5.5118922 to 5.6487818 seconds, about 17,976 dealt games per second.

C++ median: 1.1576963 seconds, range 1.1241900 to 1.1938399 seconds, about 86,378 dealt games per second.

Speedup calculation: `5.5630810 / 1.1576963 = 4.8053`.


## Environment

CPU: Intel Core Ultra X7 358H, 16 cores and 16 logical processors

Operating system version: Microsoft Windows NT 10.0.26200.0

Python: CPython 3.14.7

C++ compiler: Microsoft C/C++ Optimizing Compiler 19.51.36257
