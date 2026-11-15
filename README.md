# tiny-chess-01 entry

A 4,096-byte chess engine for make.fun's tiny-chess-01 competition, written from
scratch (no third-party engine code).

- `main.py` (3,702 bytes): a three-line unpacker plus a raw-lzma payload holding the
  engine, written by the kit's own `makefun compress` from `engine6.py`. It talks to
  the env at `$MAKEFUN_ENV_URL` (POST /game, /move, /resign).
- Search: negamax alpha-beta with iterative deepening over a fixed node budget
  (never a clock, so every trial replays byte for byte), a capture-only quiescence,
  MVV-LVA ordering, a Zobrist transposition table that answers a node from a stored
  score once that entry's depth covers it, and a material plus piece-square
  evaluation (bishop, rook and queen tables derived from the knight table at import,
  so every piece has one).
- Board: a 10x12 array with sentinels; move generation validated against perft
  (start position 20/400/8,902/197,281; kiwipete 48 at depth 1).
- The root move always comes from the env's own `legal_moves` list, so an engine
  move can never be refused.

License: MIT (see LICENSE).
