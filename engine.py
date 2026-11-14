"""tiny-chess-01 engine v3. Author zeroknowledge0x, MIT.
Zobrist TT, precomputed attacks, incremental eval, fixed node budget (never a clock)."""
import json
import os
import random
import sys
import time
import urllib.error
import urllib.request

FN = "abcdefgh"
ST = {"N": (-21, -19, -12, -8, 8, 12, 19, 21), "B": (-11, -9, 9, 11), "R": (-10, -1, 1, 10)}
ST["Q"] = ST["B"] + ST["R"]
ST["K"] = ST["Q"]
VL = {"P": 100, "N": 330, "B": 345, "R": 520, "Q": 950, "K": 30000}
PA = [0, 0, 0, 0, 0, 0, 0, 0,
      50, 50, 50, 50, 50, 50, 50, 50,
      10, 10, 20, 30, 30, 20, 10, 10,
      5, 5, 10, 25, 25, 10, 5, 5,
      0, 0, 0, 25, 25, 0, 0, 0,
      5, -5, -10, 0, 0, -10, -5, 5,
      5, 10, 10, -20, -20, 10, 10, 5,
      0, 0, 0, 0, 0, 0, 0, 0]
KN = [-50, -40, -30, -30, -30, -30, -40, -50,
      -40, -20, 0, 0, 0, 0, -20, -40,
      -30, 0, 10, 15, 15, 10, 0, -30,
      -30, 5, 15, 20, 20, 15, 5, -30,
      -30, 0, 15, 20, 20, 15, 0, -30,
      -30, 5, 10, 15, 15, 10, 5, -30,
      -40, -20, 0, 5, 5, 0, -20, -40,
      -50, -40, -30, -30, -30, -30, -40, -50]
KG = [-40, -50, -50, -60, -60, -50, -50, -40,
      -40, -50, -50, -60, -60, -50, -50, -40,
      -40, -50, -50, -60, -60, -50, -50, -40,
      -30, -40, -40, -50, -50, -40, -40, -30,
      -20, -30, -30, -40, -40, -30, -30, -20,
      -10, -20, -20, -30, -30, -20, -20, -10,
      10, 10, -10, -20, -20, -10, 10, 10,
      15, 35, 10, 0, 0, 10, 35, 15]
TA = {"P": PA, "N": KN, "K": KG}
BD = int(os.environ.get("TCE_NODES") or 48000)
M = 30000


def on(g):
    return 21 <= g <= 98 and 1 <= g % 10 <= 8


PT = {}
PB = {}
WV = {}
RA = {}
KNB = {}
KGB = {}
for t in "PNBRQK":
    PT[t] = [0] * 120
    PB[t] = [0] * 120
for i in range(21, 99):
    if not on(i):
        continue
    j = (7 - (i // 10 - 2)) * 8 + i % 10 - 1
    for t in "PNBRQK":
        a = TA.get(t)
        if a:
            PT[t][i] = a[j]
            PB[t][i] = a[j ^ 56]
    KNB[i] = [i + d for d in ST["N"] if on(i + d)]
    KGB[i] = [i + d for d in ST["Q"] if on(i + d)]
    L = []
    for d in ST["Q"]:
        r = []
        g = i + d
        while on(g):
            r.append(g)
            g += d
        L.append((abs(d) in (1, 10), r))
    RA[i] = L
for t in "PNBRQK":
    WV[t] = [VL[t] + PT[t][i] for i in range(120)]
    WV[t.lower()] = [-(VL[t] + PB[t][i]) for i in range(120)]
RG = random.Random(1234)
Z = {}
for p in "PNBRQKpnbrqk":
    Z[p] = [RG.getrandbits(64) | 1 for _ in range(120)]
TH = RG.getrandbits(64) | 1


def nm(i):
    return FN[i % 10 - 1] + str(i // 10 - 1)


def parse(fen):
    b = ["#"] * 120
    for r in range(8):
        for f in range(8):
            b[21 + r * 10 + f] = "."
    for row, line in enumerate(fen.split()[0].split("/")):
        f = 0
        for c in line:
            if c.isdigit():
                f += int(c)
            else:
                b[21 + (7 - row) * 10 + f] = c
                f += 1
    p = fen.split()
    cast = p[2] if len(p) > 2 else "-"
    ep = 0
    if len(p) > 3 and p[3] != "-":
        ep = 21 + (int(p[3][1]) - 1) * 10 + ord(p[3][0]) - 97
    return b, p[1], cast, ep


def gen(b, s, e, cast, caps=0):
    out = []
    up = s == "w"
    pr8 = 7 if up else 0
    for i in range(21, 99):
        pc = b[i]
        if pc == "." or pc == "#" or up != pc.isupper():
            continue
        t = pc.upper()
        if t == "P":
            d = 10 if up else -10
            f1 = i + d
            if not caps and b[f1] == ".":
                if f1 // 10 - 2 == pr8:
                    for q in "qrbn":
                        out.append((i, f1, q))
                else:
                    out.append((i, f1, ""))
                    if i // 10 - 2 == (1 if up else 6) and b[i + 2 * d] == ".":
                        out.append((i, i + 2 * d, ""))
            for dd in (d - 1, d + 1):
                g = i + dd
                if not on(g):
                    continue
                tg = b[g]
                if tg != "." and tg.isupper() == up:
                    continue
                if tg == "." and g != e:
                    continue
                if g // 10 - 2 == pr8:
                    for q in "qrbn":
                        out.append((i, g, q))
                else:
                    out.append((i, g, ""))
        else:
            for d in ST[t]:
                g = i + d
                while True:
                    if not on(g):
                        break
                    tg = b[g]
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


def atk(b, s, w):
    e = "N" if w else "n"
    for g in KNB[s]:
        if b[g] == e:
            return 1
    e = "K" if w else "k"
    for g in KGB[s]:
        if b[g] == e:
            return 1
    e = "P" if w else "p"
    for g in ((s - 9, s - 11) if w else (s + 9, s + 11)):
        if on(g) and b[g] == e:
            return 1
    for st, r in RA[s]:
        for g in r:
            p = b[g]
            if p != ".":
                if p.isupper() == w:
                    t = p.upper()
                    if t == "Q" or (t == "R" if st else t == "B"):
                        return 1
                break
    return 0


def kg(b, p):
    for i in range(21, 99):
        if b[i] == p:
            return i
    return 0


def ev(b):
    s = 0
    for i in range(21, 99):
        p = b[i]
        if p != "." and p != "#":
            s += WV[p][i]
    return s


def ap(b, m, h, s):
    i, g, pr = m
    p = b[i]
    n = b[:]
    t = b[g]
    ds = -WV[p][i]
    if t != ".":
        h ^= Z[t][g]
        ds -= WV[t][g]
    elif p.upper() == "P" and g % 10 != i % 10:
        c = g + (-10 if p.isupper() else 10)
        h ^= Z[b[c]][c]
        ds -= WV[b[c]][c]
        n[c] = "."
    if pr:
        q = pr.upper() if p.isupper() else pr
        n[g] = q
        h ^= Z[p][i] ^ Z[q][g]
        ds += WV[q][g]
    else:
        n[g] = p
        h ^= Z[p][i] ^ Z[p][g]
        ds += WV[p][g]
    n[i] = "."
    if p.upper() == "K" and abs(g - i) == 2:
        if g > i:
            rs, rd = i + 3, i + 1
        else:
            rs, rd = i - 4, i - 1
        r = n[rs]
        n[rd] = r
        n[rs] = "."
        h ^= Z[r][rs] ^ Z[r][rd]
        ds += WV[r][rd] - WV[r][rs]
    return n, h, s + ds


def ne(b, m):
    if b[m[0]].upper() == "P" and abs(m[1] - m[0]) == 20:
        return (m[0] + m[1]) // 2
    return 0


def od(b, ms, km=None):
    o = []
    for m in ms:
        v = b[m[1]]
        sc = 9000 if m[2] else 0
        if v != ".":
            sc += VL[v.upper()] * 10 - VL[b[m[0]].upper()]
        if m == km:
            sc += 900000
        o.append((-sc, m[0], m[1], m[2]))
    o.sort()
    return o


class C(Exception):
    pass


N = [0]
H = {}


def qs(b, u, e, a, be, h, s, k):
    N[0] += 1
    if N[0] > BD:
        raise C()
    ku = k[0] if u else k[1]
    ko = k[1] if u else k[0]
    st = s if u else -s
    if st >= be:
        return st
    if st > a:
        a = st
    for sc, i, g, pr in od(b, gen(b, "w" if u else "b", e, "-", 1)):
        v = b[g]
        if not pr and st + (VL[v.upper()] if v != "." else 0) + 120 < a:
            continue
        m = (i, g, pr)
        nb, h2, s2 = ap(b, m, h, s)
        ku2 = g if b[i].upper() == "K" else ku
        if atk(nb, ku2, not u):
            continue
        r = -qs(nb, not u, ne(b, m), -be, -a, h2 ^ TH, s2,
                (ku2, ko) if u else (ko, ku2))
        if r >= be:
            return r
        if r > a:
            a = r
    return a


def sr(b, u, e, d, a, be, h, s, ply, k, km=None):
    N[0] += 1
    if N[0] > BD:
        raise C()
    t = H.get(h)
    if t is not None and km is None:
        km = t[2]
    if d <= 0:
        return qs(b, u, e, a, be, h, s, k)
    ku = k[0] if u else k[1]
    ko = k[1] if u else k[0]
    oa = a
    bv = -M - 1
    bm = km
    am = 0
    for sc, i, g, pr in od(b, gen(b, "w" if u else "b", e, "-"), km):
        m = (i, g, pr)
        nb, h2, s2 = ap(b, m, h, s)
        ku2 = g if b[i].upper() == "K" else ku
        if atk(nb, ku2, not u):
            continue
        am = 1
        v = -sr(nb, not u, ne(b, m), d - 1, -be, -a, h2 ^ TH, s2, ply + 1,
                (ku2, ko) if u else (ko, ku2))
        if v > bv:
            bv = v
            bm = m
        if v > a:
            a = v
        if a >= be:
            break
    if not am:
        if atk(b, ku, not u):
            return -M + ply
        return 0
    H[h] = (d, bv, bm)
    return bv


def rt(b, u, e, cast, h, s, k, d):
    best = None
    bv = -M - 1
    a = -M - 1
    ku = k[0] if u else k[1]
    ko = k[1] if u else k[0]
    for sc, i, g, pr in od(b, gen(b, "w" if u else "b", e, cast)):
        m = (i, g, pr)
        nb, h2, s2 = ap(b, m, h, s)
        ku2 = g if b[i].upper() == "K" else ku
        if atk(nb, ku2, not u):
            continue
        v = -sr(nb, not u, ne(b, m), d - 1, -M - 1, -a, h2 ^ TH, s2, 1,
                (ku2, ko) if u else (ko, ku2))
        if v > bv:
            bv = v
            best = m
        if v > a:
            a = v
    return best


def think(b, s, cast, e, legal):
    u = s == "w"
    k = (kg(b, "K"), kg(b, "k"))
    if k[0] == 0 or k[1] == 0:
        return legal[0] if legal else None
    h = 0
    for i in range(21, 99):
        p = b[i]
        if p != "." and p != "#":
            h ^= Z[p][i]
    sc = ev(b)
    if len(H) > 300000:
        H.clear()
    best = None
    N[0] = 0
    for d in range(1, 13):
        try:
            m = rt(b, u, e, cast, h, sc, k, d)
        except C:
            break
        if m is None:
            break
        best = m
    if best is None:
        return legal[0] if legal else None
    u1 = nm(best[0]) + nm(best[1]) + best[2]
    return u1 if u1 in legal else legal[0]


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
    print("done %s/%s/%s" % (g.get("wins"), g.get("draws"), g.get("losses")), file=sys.stderr)


main()