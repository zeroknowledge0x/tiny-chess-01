# tiny-chess-01 entry

A 4,096-byte chess engine for make.fun's tiny-chess-01 competition, written from
scratch (no third-party engine code).

- `main.py` (3,669 bytes): a three-line unpacker plus a raw-lzma payload holding the
  engine, written by the kit's own `makefun compress` from `engine6.py`. It talks to
  the env at `$MAKEFUN_ENV_URL` (POST /game, /move, /resign).
- Search: negamax alpha-beta (PVS with late-move reductions) and iterative deepening
  over a fixed node budget (never a clock, so every trial replays byte for byte), a
  capture-only quiescence, MVV-LVA ordering plus a killer move per ply, a Zobrist
  transposition table used for move ordering, and a material plus piece-square
  evaluation (bishop, rook and queen tables derived from the knight table at import,
  so every piece has one). A depth-covering transposition-table cutoff was measured
  and rejected: on the same practice trial it scored 0 of 6 (all lost) against 1 win
  1 draw 4 losses for this build, because a stored score that is only a bound was
  being returned as an exact value.
- Board: a 10x12 array with sentinels; move generation validated against perft
  (start position 20/400/8,902/197,281; kiwipete 48 at depth 1).
- The root move always comes from the env's own `legal_moves` list, so an engine
  move can never be refused.

License: MIT (see LICENSE).
