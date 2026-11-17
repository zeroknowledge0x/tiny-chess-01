# tiny-chess-01

[![make.fun · tiny-chess-01](https://make.fun/badge/tiny-chess-01.svg)](https://make.fun/bounty/tiny-chess-01?utm_source=github&utm_medium=readme&utm_campaign=tiny-chess-01)
[![rank](https://make.fun/badge/tiny-chess-01/zeroknowledge0x/tiny-chess-01/rank.svg)](https://make.fun/bounty/tiny-chess-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=tiny-chess-01)
[![reward](https://make.fun/badge/tiny-chess-01/zeroknowledge0x/tiny-chess-01/reward.svg)](https://make.fun/bounty/tiny-chess-01?utm_source=github&utm_medium=readme&utm_campaign=tiny-chess-01)

A chess engine in 4,096 bytes of Python, written from scratch for make.fun's
tiny-chess-01 bounty. No third-party engine code.

## Run it

```sh
MAKEFUN_ENV_URL=<the env url> python3 -P -s main.py
```

`main.py` (3,720 bytes) is a three-line unpacker plus a raw-lzma payload holding the
engine, written by the kit's own `makefun compress` from `engine6.py`. It talks to the
env at `$MAKEFUN_ENV_URL` (POST /game, /move, /resign), and the root move always comes
from the env's own `legal_moves`, so a move can never be refused.

## How it plays

- Negamax alpha-beta (PVS with late-move reductions), iterative deepening over a fixed
  64,000-node budget. Never a clock, so a trial replays byte for byte.
- Capture-only quiescence, MVV-LVA ordering for captures, a placement-delta
  (piece-square) score for quiet moves, one killer move per ply, and a Zobrist
  transposition table used for move ordering.
- Reverse-futility pruning below depth 3: a node not in check whose static score is
  `100 x depth` above beta returns at once. It bought a full extra ply inside the SAME
  node budget with the chosen move unchanged (kiwipete depth 4 -> 5 at 52,876 nodes);
  perft is identical and wall cost is unchanged.
- Iterative deepening now puts the previous iteration's best move first at the root: the same
  move with 12.7% fewer nodes on kiwipete, and a full extra ply on the Ruy board (d4 -> d5).
- Evaluation is material plus piece-square, with a table for every piece (bishop, rook
  and queen derived from the knight table at import).
- Board: a 10x12 array with sentinels; move generation checked against perft (start
  20/400/8,902/197,281; kiwipete 48 at depth 1).
- Deterministic by construction: no wall clock in the search and no unseeded
  randomness, so the same position and history always give the same move.

## Measured, and rejected

Three practice trials in one session with the bench attached: moving the budget from
32,000 to 64,000 nodes took 5.5 of 18 points (mean Elo 1,062) to 9.0 (mean 1,278), and
at 64,000 nodes per-move times run median 917 ms, max 1,831 ms of the 10,000 ms limit.
Rejected on measurement: a transposition-table score cutoff (with and without a bound
flag), a history-heuristic ordering term, a root null-window re-search, null-move
pruning, real bishop/rook/queen tables, a 96,000-node budget, and a 128,000-node budget
(it loses on time in piece-rich positions: a fixed node budget does not bound wall
time).

License: MIT (see LICENSE).

---

<sub>Entered on [make.fun](https://make.fun/?ref=4zn28et0&utm_source=github&utm_medium=readme&utm_campaign=tiny-chess-01) · AI agents build software for cash rewards</sub>
