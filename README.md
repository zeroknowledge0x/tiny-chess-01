# tiny-chess-01 entry

A 4,096-byte chess engine for make.fun's tiny-chess-01 competition, written from
scratch (no third-party engine code).

- `main.py` (3,712 bytes): a three-line unpacker plus a raw-lzma payload holding the
  engine, written by the kit's own `makefun compress` from `engine6.py`. It talks to
  the env at `$MAKEFUN_ENV_URL` (POST /game, /move, /resign).
- Search: negamax alpha-beta (PVS with late-move reductions), iterative deepening over
  a fixed 64,000-node budget (never a clock, so every trial replays byte for byte),
  capture-only quiescence, MVV-LVA ordering for captures, a placement-delta
  (piece-square) score for quiet moves, a killer move per ply, a Zobrist
  transposition table for move ordering, and reverse-futility pruning at depth < 3
  (a node that is not in check and whose static score is 100 x depth above beta is
  returned at once). Evaluation is material plus piece-square, with a table for every
  piece (bishop, rook and queen derived from the knight table at import).
- Reverse futility bought a full extra ply inside the SAME 64,000-node budget with the
  chosen move unchanged, measured load-immune (node counts, not wall time) on four
  positions: kiwipete depth 4 -> 5 (52,876 nodes to depth 5, was 4 at 28,703), a Ruy
  Lopez middlegame 3 -> 4, an Italian depth 5 at 51,980 -> 45,882 nodes, the start
  position depth 6 at 46,907 -> 45,658. Perft is identical; wall cost is unchanged.
- Quiet moves are ordered by their own piece-square delta (captures keep MVV-LVA): at
  64,000 nodes a quiet middlegame completes depth 3 -> 4 with the same move, its
  depth-4 iteration costing 49,846 nodes against 161,314 before.
- Budget 32,000 -> 64,000 nodes, three practice trials in one session with the bench
  (6M `s+=i*i` in 1.02-1.20 s) attached to each: 5.5 of 18 points (Elo 1191/997/997,
  mean 1,062) -> 9.0 (Elo 1191/1364/1279, mean 1,278). Per-move times at 64,000:
  median 917 ms, p99 1,615 ms, max 1,831 ms of the env's 10,000 ms limit.
- Piece-square tables are written rank 8 first, but the import loop indexed them with
  `(7 - rank)`, applying every table vertically inverted (a pawn on its own second rank
  scored like one about to promote). Correcting the index is a four-byte deletion and
  Elo-neutral on trial 0 (2.0 points both ways, Elo 1099): a correctness fix, not a
  strength claim.
- Rejected on measurement: a transposition-table score cutoff (0 of 6 on trial 0; the
  stored value is often only a bound), the same cutoff with a bound flag, a
  history-heuristic ordering term, null-move pruning (all probed at 32,000 nodes: same
  depth, same move), real bishop/rook/queen tables (5.0 of 18 points against 5.5), and
  a 96,000-node budget (identical depth and move to 64,000).
- Board: a 10x12 array with sentinels; move generation validated against perft (start
  20/400/8,902/197,281; kiwipete 48 at depth 1). The root move always comes from the
  env's own `legal_moves` list, so an engine move can never be refused.

License: MIT (see LICENSE).
