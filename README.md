# tiny-chess-01 entry

A 4,096-byte chess engine for make.fun's tiny-chess-01 competition, written from
scratch (no third-party engine code).

- `main.py` (3,670 bytes): a three-line unpacker plus a raw-lzma payload holding the
  engine, written by the kit's own `makefun compress` from `engine6.py`. It talks to
  the env at `$MAKEFUN_ENV_URL` (POST /game, /move, /resign).
- Search: negamax alpha-beta (PVS with late-move reductions) and iterative deepening
  over a fixed node budget (never a clock, so every trial replays byte for byte), a
  capture-only quiescence, MVV-LVA ordering plus a killer move per ply, a Zobrist
  transposition table used for move ordering, and a material plus piece-square
  evaluation (bishop, rook and queen tables derived from the knight table at import,
  so every piece has one).
- Evaluation fix, measured on practice trial 0 with the sealed scorer: the
  piece-square tables are written with the first row on rank 8, but the import loop
  indexed them with `(7 - rank)`, so every table was applied vertically inverted. A
  white pawn on its own second rank scored the same as one a step from promotion
  (+50), and a white king was valued 60 centipawns SAFER on the enemy back rank than
  on e1. Correcting the index to `rank` (a four-byte deletion) took the trial from
  1 win 1 draw 4 losses (Elo 997) to 1 win 2 draws 3 losses (Elo 1099), no time loss.
  Knight, bishop, rook and queen tables are vertically symmetric, so only the pawn
  and king tables were affected.
- Measured and rejected as neutral or worse, all at the fixed 32,000-node budget: a
  depth-covering transposition-table cutoff (0 of 6 on trial 0 against 1 win 1 draw 4
  losses, because a stored score that is only a bound was returned as exact); the same
  cutoff with a bound flag; and a history-heuristic ordering term. The latter two
  completed the same depth (3-5 plies) and chose the same move in every probe
  position, so they did not earn their bytes.
- Board: a 10x12 array with sentinels; move generation validated against perft
  (start position 20/400/8,902/197,281; kiwipete 48 at depth 1). The root move always
  comes from the env's own `legal_moves` list, so an engine move can never be refused.

License: MIT (see LICENSE).
