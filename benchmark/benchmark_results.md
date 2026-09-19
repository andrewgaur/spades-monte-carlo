# Python and C++ benchmark results

Run date: September 14, 2026

The C++ implementation completed the simulation in 1.3109803 seconds at the median. Python completed it in 6.4818767 seconds. The median runtime ratio was 4.9443, so C++ ran about 4.94 times as many equivalent dealt games per second on this machine.


## Correctness check

Both implementations replayed the same nine deals from `benchmark_fixtures.txt`. They matched on all four trick totals for every fixture. Every game awarded 13 tricks. They also matched on the recommended bid and exact integer score totals during every measured run.

The fixture set includes different starting players, both initial spades states, and a deal where player 0 wins zero tricks. Separate regression checks confirm that players compare their choices with the current winning card and that `[1, 12, 10, 10, 6, 6, 5, 3, 1, 12]` selects bid 5 using exact mean scores. The old floor before selection incorrectly chose bid 3.

Fixture signature:

```text
3,3,3,4;5,4,1,3;6,2,2,3;6,2,3,2;4,1,4,4;3,3,4,3;1,8,3,1;2,3,4,4;0,4,3,6
```


## Method

Each sample replayed 100,000 dealt games. Each implementation ran one untimed 100,000 game warmup immediately before its measured batch. The seven samples alternated Python then C++.

Timing includes per game state copies, simulation, result retention, and checksum accumulation. It excludes fixture loading, bid scoring, compilation, imports, and console output.

The C++ project used its Release x64 configuration with whole program optimization enabled.


## Raw measurements

```text
Sample  Python seconds  C++ seconds  Python/C++ ratio
1       6.4624938       1.3456964    4.80234
2       6.5027792       1.3962995    4.65715
3       6.4744946       1.2656687    5.11547
4       6.4917457       1.2645558    5.13362
5       6.4812400       1.3109803    4.94381
6       6.5472687       1.2923152    5.06631
7       6.4818767       1.4229104    4.55537
```

Python median: 6.4818767 seconds, range 6.4624938 to 6.5472687 seconds, about 15,428 dealt games per second.

C++ median: 1.3109803 seconds, range 1.2645558 to 1.4229104 seconds, about 76,279 dealt games per second.

Speedup calculation: `6.4818767 / 1.3109803 = 4.9443`.


## Environment

CPU: Intel Core Ultra X7 358H, 16 cores and 16 logical processors

Operating system version: Microsoft Windows NT 10.0.26200.0

Python: CPython 3.14.7

C++ compiler: Microsoft C/C++ Optimizing Compiler 19.51.36257
