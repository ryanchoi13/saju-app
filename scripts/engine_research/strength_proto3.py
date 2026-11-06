"""강약 저울 3차: 12운성 뿌리 + 인성 감쇠. 80건 하나 빼기 교차검증(LOO)으로 정직한 성적을 낸다.

뿌리 점수: 지지마다 일간의 12운성 — 건록·제왕 R_STRONG, 장생·관대 R_MID, 묘 R_TOMB, 그 밖 0 (× 자리 가중치)
r = (비겁 + 인성×W_RES + 뿌리) / (전체 − 인성×(1−W_RES) + 뿌리)
"""
import os as _os, sys as _sys
ROOT = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
DATA = _os.path.join(ROOT, 'docs', 'engine')
OUT = _os.environ.get('RESEARCH_OUT', '/tmp')
_sys.path[:0] = [ROOT, _os.path.join(ROOT, 'backend'), _os.path.dirname(_os.path.abspath(__file__))]

import sys, itertools
from strength_proto import STEM_EL, GEN, HIDDEN, load
from app.engine.facts.twelve_stages import get_twelve_stage

PARENT = {v: k for k, v in GEN.items()}
STAGE_GROUP = {"OFFICIAL": "strong", "PROSPERITY": "strong", "BIRTH": "mid", "BATH": None,
               "CROWN": "mid", "TOMB": "tomb"}


def features(pl):
    y, m, d, h = pl
    dm_stem = d[0]; dm = STEM_EL[dm_stem]; res = PARENT[dm]
    f = {"peer": [0.0] * 3, "res": [0.0] * 3, "tot": [0.0] * 3, "root": {"strong": [0.0] * 3, "mid": [0.0] * 3, "tomb": [0.0] * 3}}
    # 자리 묶음: 0 = 월지, 1 = 일지, 2 = 나머지(천간 3 + 연지·시지)
    for stem in (y[0], m[0], h[0]):
        e = STEM_EL[stem]; f["tot"][2] += 1; f["peer"][2] += e == dm; f["res"][2] += e == res
    for slot, pll in ((2, y), (0, m), (1, d), (2, h)):
        for e, share in HIDDEN[pll[1]]:
            f["tot"][slot] += share; f["peer"][slot] += share * (e == dm); f["res"][slot] += share * (e == res)
        g = STAGE_GROUP.get(get_twelve_stage(dm_stem, pll[1]).name)
        if g:
            f["root"][g][slot] += 1
    return f


def ratio(f, p):
    wm, wd, w_res, r_s, r_m, r_t = p
    w = (wm, wd, 1.0)
    peer = sum(f["peer"][i] * w[i] for i in range(3))
    res = sum(f["res"][i] * w[i] for i in range(3))
    tot = sum(f["tot"][i] * w[i] for i in range(3))
    root = sum((f["root"]["strong"][i] * r_s + f["root"]["mid"][i] * r_m + f["root"]["tomb"][i] * r_t) * w[i] for i in range(3))
    return (peer + res * w_res + root) / (tot - res * (1 - w_res) + root)


GRID = list(itertools.product((1.5, 2.5), (1.0, 1.5), (0.5, 0.75, 1.0), (0, 0.5, 1.0), (0, 0.3, 0.6), (0, 0.2)))
CUTS = [(lo / 100, hi / 100) for lo in range(24, 52, 3) for hi in range(36, 70, 3) if hi > lo]


def judge(r, lo, hi):
    return "strong" if r >= hi else "weak" if r <= lo else None


def fit(cases, penalty):
    best = None
    for p in GRID:
        rs = [(ratio(f, p), g) for f, g in cases]
        for lo, hi in CUTS:
            right = wrong = 0
            for r, g in rs:
                j = judge(r, lo, hi)
                right += j == g; wrong += j is not None and j != g
            key = right - penalty * wrong
            if best is None or key > best[0]:
                best = (key, p, lo, hi)
    return best[1:]


if __name__ == "__main__":
    cases = [(features(pl), g) for pl, g, _ in load(_os.path.join(DATA, 'strength-answer-set', 'set1.csv')) + load(_os.path.join(DATA, 'strength-answer-set', 'set2.csv'))]
    for penalty in (2, 3, 5):
        right = wrong = 0
        for i in range(len(cases)):
            p, lo, hi = fit(cases[:i] + cases[i + 1:], penalty)
            j = judge(ratio(cases[i][0], p), lo, hi)
            right += j == cases[i][1]; wrong += j is not None and j != cases[i][1]
        n = len(cases)
        p, lo, hi = fit(cases, penalty)
        print(f"반대 벌점 ×{penalty}: LOO 맞음 {right}/{n} {right/n:.0%} · 반대 {wrong} {wrong/n:.0%} · 보류 {n-right-wrong} | 전체로 맞춘 값 {p} {lo}~{hi}")
