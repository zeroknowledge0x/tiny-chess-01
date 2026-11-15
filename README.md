# tiny-chess-01 entry

A 4,096-byte chess engine for make.fun's tiny-chess-01 competition, written from
scratch (no third-party engine code).

- `main.py` (3,691 bytes): a three-line unpacker plus a raw-lzma payload holding the
  engine, written by the kit's own `makefun compress` from `engine6.py`. It talks to
  the env at `$MAKEFUN_ENV_URL` (POST /game, /move, /resign).
- Search: negamax alpha-beta (PVS with late-move reductions), iterative deepening over
  a fixed 64,000-node budget (never a clock, so every trial replays byte for byte),
  capture-only quiescence, MVV-LVA ordering for captures and a placement-delta
  (piece-square) score for quiet moves, a killer move per ply, a Zobrist
  transposition table for move ordering, material plus piece-square evaluation with a
  table for every piece (bishop, rook and queen derived from the knight table at
  import).
- Quiet moves are ordered by their own piece-square delta (captures keep MVV-LVA): at
  the baked 64,000 nodes a quiet middlegame position completes depth 3 -> 4 with the
  same move chosen, its depth-4 iteration costing 49,846 nodes against 161,314 before,
  and generated moves plus perft are byte-identical, so the change is ordering only.
- Budget raised 32,000 -> 64,000 nodes, measured on all three practice trials in one
  session with the single-core bench (6M `s+=i*i` in 1.02-1.20 s, a quiet box) attached
  to each: 5.5 of 18 points (Elo 1191/997/997, mean 1,062) -> 9.0 (Elo 1191/1364/1279,
  mean 1,278), a gain on every trial. Per-move times at 64,000: median 917 ms, p99
  1,615 ms, max 1,831 ms of the env's 10,000 ms limit. The budget is the depth cap
  (kiwipete completes depth 4 at 32,001 nodes, depth 5 at 64,001).
- Piece-square tables are written rank 8 first, but the import loop indexed them with
  `(7 - rank)`, so every table was applied vertically inverted: a pawn on its own second
  rank scored like one about to promote, and the king was 60 centipawns safer on the
  enemy back rank than on e1. Correcting the index (a four-byte deletion) is Elo-neutral
  on trial 0 (1 win 2 draws 3 losses against 2 wins 4 losses, both 2.0 points, both Elo
  1099), so it is recorded as a correctness fix, not a strength claim.
- Rejected on measurement: a transposition-table score cutoff (0 of 6 on trial 0; the
  stored value is often only a bound), the same cutoff with a bound flag, a
  history-heuristic ordering term and null-move pruning (all probed at 32,000 nodes:
  same depth, same move), real bishop/rook/queen tables in place of the
  knight-derived ones (5.0 of 18 points against 5.5, inside trial resolution, 99 bytes
  dearer), and a 96,000-node budget (identical completed depth and identical move to
  64,000 on both probe positions, at ~50% more wall time per move).
- Board: a 10x12 array with sentinels; move generation validated against perft (start
  20/400/8,902/197,281; kiwipete 48 at depth 1). The root move always comes from the
  env's own `legal_moves` list, so an engine move can never be refused.

License: MIT (see LICENSE).
