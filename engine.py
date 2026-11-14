"""tiny-chess-01 engine - the payload packed into main.py. Author zeroknowledge0x, MIT."""
import json
import os
import sys
import time
import urllib.error
import urllib.request

FN = "abcdefgh"
STEP = {"N": (-21, -19, -12, -8, 8, 12, 19, 21), "B": (-11, -9, 9, 11), "R": (-10, -1, 1, 10)}
STEP["Q"] = STEP["B"] + STEP["R"]
STEP["K"] = STEP["Q"]
VAL = {"P": 100, "N": 320, "B": 330, "R": 500, "Q": 900, "K": 20000}
PAWN = [0, 0, 0, 0, 0, 0, 0, 0,
        50, 50, 50, 50, 50, 50, 50, 50,
        10, 10, 20, 30, 30, 20, 10, 10,
        5, 5, 10, 25, 25, 10, 5, 5,
        0, 0, 0, 20, 20, 0, 0, 0,
        5, -5, -10, 0, 0, -10, -5, 5,
        5, 10, 10, -20, -20, 10, 10, 5,
        0, 0, 0, 0, 0, 0, 0, 0]
KNIGHT = [-50, -40, -30, -30, -30, -30, -40, -50,
          -40, -20, 0, 0, 0, 0, -20, -40,
          -30, 0, 10, 15, 15, 10, 0, -30,
          -30, 5, 15, 20, 20, 15, 5, -30,
          -30, 0, 15, 20, 20, 15, 0, -30,
          -30, 5, 10, 15, 15, 10, 5, -30,
          -40, -20, 0, 5, 5, 0, -20, -40,
          -50, -40, -30, -30, -30, -30, -40, -50]
BISHOP = [-20, -10, -10, -10, -10, -10, -10, -20,
          -10, 0, 0, 0, 0, 0, 0, -10,
          -10, 0, 5, 10, 10, 5, 0, -10,
          -10, 5, 5, 10, 10, 5, 5, -10,
          -10, 0, 10, 10, 10, 10, 0, -10,
          -10, 10, 10, 10, 10, 10, 10, -10,
          -10, 5, 0, 0, 0, 0, 5, -10,
          -20, -10, -10, -10, -10, -10, -10, -20]
ROOK = [0, 0, 0, 0, 0, 0, 0, 0,
        5, 10, 10, 10, 10, 10, 10, 5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        0, 0, 0, 5, 5, 0, 0, 0]
QUEEN = [-20, -10, -10, -5, -5, -10, -10, -20,
         -10, 0, 0, 0, 0, 0, 0, -10,
         -10, 0, 5, 5, 5, 5, 0, -10,
         -5, 0, 5, 5, 5, 5, 0, -5,
         0, 0, 5, 5, 5, 5, 0, -5,
         -10, 5, 5, 5, 5, 5, 0, -10,
         -10, 0, 5, 0, 0, 0, 0, -10,
         -20, -10, -10, -5, -5, -10, -10, -20]
KING = [-30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -20, -30, -30, -40, -40, -30, -30, -20,
        -10, -20, -20, -20, -20, -20, -20, -10,
        20, 20, 0, 0, 0, 0, 20, 20,
        20, 30, 10, 0, 0, 10, 30, 20]
PST = {"P": PAWN, "N": KNIGHT, "B": BISHOP, "R": ROOK, "Q": QUEEN, "K": KING}
BUDGET = int(os.environ.get("TCE_NODES") or 45000)
MATE = 30000


def idx(f, r):
    return 21 + r * 10 + f


def nm(i):
    return FN[i % 10 - 1] + str(i // 10 - 1)


def parse(fen):
    b = ["#"] * 120
    for r in range(8):
        for f in range(8):
            b[idx(f, r)] = "."
    for row, line in enumerate(fen.split()[0].split("/")):
        f = 0
        for c in line:
            if c.isdigit():
                f += int(c)
            else:
                b[idx(f, 7 - row)] = c
                f += 1
    p = fen.split()
    cast = p[2] if len(p) > 2 else "-"
    ep = 0
    if len(p) > 3 and p[3] != "-":
        ep = idx(ord(p[3][0]) - 97, int(p[3][1]) - 1)
    return b, p[1], cast, ep


def gen(b, side, ep, cast, caps=False):
    out = []
    up = side == "w"
    pr_rank = 7 if up else 0
    for i in range(21, 99):
        pc = b[i]
        if pc == "." or pc == "#" or up != pc.isupper():
            continue
        t = pc.upper()
        if t == "P":
            d = 10 if up else -10
            f1 = i + d
            if b[f1] == "." and not caps:
                if f1 // 10 - 2 == pr_rank:
                    for pr in "qrbn":
                        out.append((i, f1, pr))
                else:
                    out.append((i, f1, ""))
                    if i // 10 - 2 == (1 if up else 6) and b[i + 2 * d] == ".":
                        out.append((i, i + 2 * d, ""))
            for dd in (d - 1, d + 1):
                g = i + dd
                tg = b[g]
                if tg == "#" or (tg != "." and tg.isupper() == up):
                    continue
                if tg == "." and g != ep:
                    continue
                if g // 10 - 2 == pr_rank:
                    for pr in "qrbn":
                        out.append((i, g, pr))
                else:
                    out.append((i, g, ""))
        else:
            for d in STEP[t]:
                g = i + d
                while True:
                    tg = b[g]
                    if tg == "#":
                        break
                    if tg == ".":
                        if not caps:
                            out.append((i, g, ""))
                        if t in "NK":
                            break
                        g += d
                        continue
                    if tg.isupper() != up:
                        out.append((i, g, ""))
                    break
        if t == "K" and not caps:
            if up:
                if "K" in cast and b[26] == "." and b[27] == "." and b[25] == "K" and b[28] == "R":
                    out.append((25, 27, ""))
                if "Q" in cast and b[24] == "." and b[23] == "." and b[22] == "." and b[25] == "K" and b[21] == "R":
                    out.append((25, 23, ""))
            else:
                if "k" in cast and b[96] == "." and b[97] == "." and b[95] == "k" and b[98] == "r":
                    out.append((95, 97, ""))
                if "q" in cast and b[94] == "." and b[93] == "." and b[92] == "." and b[95] == "k" and b[91] == "r":
                    out.append((95, 93, ""))
    return out


def attacked(b, sq, byw):
    for d in STEP["Q"]:
        g = sq + d
        while True:
            tg = b[g]
            if tg == "#":
                break
            if tg != ".":
                if tg.isupper() == byw:
                    t = tg.upper()
                    straight = abs(d) in (1, 10)
                    if t == "Q" or (t == "K" and abs(g - sq) in (1, 9, 10, 11)) \
                            or (t == "R" and straight) or (t == "B" and not straight):
                        return True
                break
            g += d
    for d in STEP["N"]:
        tg = b[sq + d]
        if tg != "#" and tg != "." and tg.isupper() == byw and tg.upper() == "N":
            return True
    d = -10 if byw else 10
    for dd in (d - 1, d + 1):
        tg = b[sq + dd]
        if tg != "#" and tg != "." and tg.isupper() == byw and tg.upper() == "P":
            return True
    return False


def apply(b, m):
    i, g, pr = m
    pc = b[i]
    nb = b[:]
    if pr:
        nb[g] = pr.upper() if pc.isupper() else pr
    elif pc.upper() == "P" and b[g] == "." and g % 10 != i % 10:
        nb[g + (-10 if pc.isupper() else 10)] = "."
    else:
        pass
    if not pr:
        nb[g] = pc
    nb[i] = "."
    if pc.upper() == "K" and abs(g - i) == 2:
        if g > i:
            nb[i + 1] = nb[i + 3]
            nb[i + 3] = "."
        else:
            nb[i - 1] = nb[i - 4]
            nb[i - 4] = "."
    return nb


def king_of(b, up):
    for i in range(21, 99):
        if b[i] == ("K" if up else "k"):
            return i
    return 0


class Cut(Exception):
    pass


NODES = [0]


def evaluate(b):
    s = 0
    for i in range(21, 99):
        pc = b[i]
        if pc == "." or pc == "#":
            continue
        t = pc.upper()
        j = (7 - (i // 10 - 2)) * 8 + (i % 10 - 1)
        if pc.isupper():
            s += VAL[t] + PST[t][j]
        else:
            s -= VAL[t] + PST[t][j ^ 56]
    return s


def sgn(b, up):
    v = evaluate(b)
    return v if up else -v


def order(b, ms):
    def k(m):
        v = b[m[1]]
        sc = VAL[v.upper()] * 10 - VAL[b[m[0]].upper()] if v != "." else 0
        if m[2]:
            sc += 8000
        return -sc
    return sorted(ms, key=k)


def newep(b, m):
    if b[m[0]].upper() == "P" and abs(m[1] - m[0]) == 20:
        return (m[0] + m[1]) // 2
    return 0


def ncast(b, m, cast):
    # Castling rights after m, played from board b: a king move or a rook move
    # drops that side's rights, and so does a capture on a rook's home square.
    if cast == "-":
        return "-"
    s = cast
    pc = b[m[0]]
    t = pc.upper()
    if t == "K":
        s = s.replace("K", "").replace("Q", "") if pc == "K" else s.replace("k", "").replace("q", "")
    elif t == "R":
        if m[0] == 28:
            s = s.replace("K", "")
        elif m[0] == 21:
            s = s.replace("Q", "")
        elif m[0] == 98:
            s = s.replace("k", "")
        elif m[0] == 91:
            s = s.replace("q", "")
    sq = m[1]
    if sq == 28:
        s = s.replace("K", "")
    elif sq == 21:
        s = s.replace("Q", "")
    elif sq == 98:
        s = s.replace("k", "")
    elif sq == 91:
        s = s.replace("q", "")
    return s or "-"


def quiesce(b, up, ep, alpha, beta):
    NODES[0] += 1
    if NODES[0] > BUDGET:
        raise Cut()
    stand = sgn(b, up)
    if stand >= beta:
        return beta
    if stand > alpha:
        alpha = stand
    for m in order(b, gen(b, "w" if up else "b", ep, "-", True)):
        nb = apply(b, m)
        k = king_of(nb, up)
        if k and attacked(nb, k, not up):
            continue
        v = -quiesce(nb, not up, newep(b, m), -beta, -alpha)
        if v >= beta:
            return beta
        if v > alpha:
            alpha = v
    return alpha


def search(b, up, ep, depth, alpha, beta, ply, cast="-"):
    NODES[0] += 1
    if NODES[0] > BUDGET:
        raise Cut()
    if depth <= 0:
        return quiesce(b, up, ep, alpha, beta)
    side = "w" if up else "b"
    best = -MATE - 1
    anym = False
    for m in order(b, gen(b, side, ep, cast)):
        nb = apply(b, m)
        k = king_of(nb, up)
        if k and attacked(nb, k, not up):
            continue
        anym = True
        v = -search(nb, not up, newep(b, m), depth - 1, -beta, -alpha, ply + 1, ncast(b, m, cast))
        if v > best:
            best = v
        if v > alpha:
            alpha = v
        if alpha >= beta:
            break
    if not anym:
        k = king_of(b, up)
        return -MATE + ply if (k and attacked(b, k, not up)) else 0
    return best


def root(b, up, ep, cast, depth, alpha, beta):
    side = "w" if up else "b"
    best = None
    bestv = -MATE - 1
    for m in order(b, gen(b, side, ep, cast)):
        nb = apply(b, m)
        k = king_of(nb, up)
        if k and attacked(nb, k, not up):
            continue
        v = -search(nb, not up, newep(b, m), depth - 1, -beta, -alpha, 1, ncast(b, m, cast))
        if v > bestv:
            bestv = v
            best = m
        if v > alpha:
            alpha = v
    return best, bestv


def think(b, side, cast, ep, legal):
    up = side == "w"
    best = None
    for d in range(1, 12):
        NODES[0] = 0
        try:
            m, v = root(b, up, ep, cast, d, -MATE - 1, MATE + 1)
        except Cut:
            break
        if m is None:
            break
        best = m
    if best is None:
        return legal[0] if legal else None
    u = nm(best[0]) + nm(best[1]) + best[2]
    return u if u in legal else legal[0]


def post(url, path, body):
    err = None
    for _ in range(40):
        req = urllib.request.Request(url + path, data=json.dumps(body).encode(),
                                     headers={"content-type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            err = "HTTP %d %s" % (e.code, e.read().decode(errors="replace"))
            if e.code < 500:
                break
        except Exception as e:
            err = repr(e)
        time.sleep(0.2)
    sys.exit(err)


def main():
    url = os.environ.get("MAKEFUN_ENV_URL") or sys.exit("MAKEFUN_ENV_URL unset")
    while True:
        g = post(url, "/game", {})
        if g["status"] == "done":
            break
        while g["status"] == "your_move":
            b, side, cast, ep = parse(g["fen"])
            mv = think(b, side, cast, ep, g["legal_moves"])
            g = post(url, "/move", {"game": g["game"], "move": mv})
        print("game %s: %s (%s)" % (g.get("game"), g.get("outcome"), g.get("reason")), file=sys.stderr)
    print("done %s/%s/%s nodes" % (g.get("wins"), g.get("draws"), g.get("losses")), file=sys.stderr)


main()
