"""강약 저울 시제품(엔진 밖). 간지 네 기둥만으로 '돕는 힘 : 빼는 힘'을 잰다.

  돕는 힘 = 비겁(일간과 같은 오행) + 인성(일간을 생하는 오행)
  빼는 힘 = 식상 + 재성 + 관성
  천간 1칸 = 1, 지지 1칸 = 지장간 비중대로(element_balance와 같은 표). 일간 자신은 뺀다.
  자리 가중치: 월지(월령) W_M, 일지 W_D, 나머지 1.
  비율 r = 돕는 힘 / 전체. r ≥ HI → 신강, r ≤ LO → 신약, 사이 → 중화.

python strength_proto.py [csv ...]  — 격자 탐색은 첫 번째 파일(개발용)로만, 나머지는 시험용으로 채점만.
"""
import os as _os, sys as _sys
ROOT = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
DATA = _os.path.join(ROOT, 'docs', 'engine')
OUT = _os.environ.get('RESEARCH_OUT', '/tmp')
_sys.path[:0] = [ROOT, _os.path.join(ROOT, 'backend'), _os.path.dirname(_os.path.abspath(__file__))]

import sys, csv, itertools

STEM_EL = dict(zip("甲乙丙丁戊己庚辛壬癸", "木木火火土土金金水水"))
GEN = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
HIDDEN = {  # 지장간(정기 마지막) 과 비중 — element_balance._HIDDEN_WEIGHTS 와 같은 비율
    "子": [("水", 1.0)], "丑": [("土", .6), ("水", .3), ("金", .1)], "寅": [("木", 16/30), ("火", 7/30), ("土", 7/30)],
    "卯": [("木", 1.0)], "辰": [("土", .6), ("木", .3), ("水", .1)], "巳": [("火", 16/30), ("金", 7/30), ("土", 7/30)],
    "午": [("火", .7), ("土", .3)], "未": [("土", .6), ("火", .3), ("木", .1)], "申": [("金", 16/30), ("水", 7/30), ("土", 7/30)],
    "酉": [("金", 1.0)], "戌": [("土", .6), ("金", .3), ("火", .1)], "亥": [("水", .7), ("木", .3)],
}


def ratio(pillars, w_month, w_day):
    y, m, d, h = pillars
    dm = STEM_EL[d[0]]
    support_els = {dm, next(k for k, v in GEN.items() if v == dm)}
    sup = tot = 0.0
    for stem in (y[0], m[0], h[0]):
        e = STEM_EL[stem]; tot += 1; sup += e in support_els
    for pos, p in (("y", y), ("m", m), ("d", d), ("h", h)):
        w = w_month if pos == "m" else w_day if pos == "d" else 1.0
        for e, share in HIDDEN[p[1]]:
            tot += w * share; sup += w * share * (e in support_els)
    return sup / tot


def bucket(v):
    return "strong" if v in ("신강", "극신강") else "weak" if v in ("신약", "극신약") else None


def load(path):
    rows = list(csv.DictReader(open(path, encoding="utf-8-sig")))
    return [((r["year"], r["month"], r["day"], r["hour"]), bucket(r["verdict"]), r["id"]) for r in rows
            if bucket(r["verdict"]) and not r["special_structure"].strip()]


def judge(r, lo, hi):
    return "strong" if r >= hi else "weak" if r <= lo else "balanced"


def score(cases, wm, wd, lo, hi):
    got = [judge(ratio(p, wm, wd), lo, hi) for p, _, _ in cases]
    right = sum(g == gold for g, (_, gold, _) in zip(got, cases))
    wrong = sum(g not in ("balanced", gold) for g, (_, gold, _) in zip(got, cases))
    return right, wrong, got


if __name__ == "__main__":
    dev = load(sys.argv[1])
    best = None
    for wm, wd in itertools.product((1.5, 2, 2.5, 3, 4), (1, 1.5, 2)):
        rs = sorted(ratio(p, wm, wd) for p, _, _ in dev)
        for lo, hi in itertools.product([x / 100 for x in range(30, 56, 2)], [x / 100 for x in range(40, 66, 2)]):
            if hi <= lo:
                continue
            right, wrong, _ = score(dev, wm, wd, lo, hi)
            key = (right - 2 * wrong, -(hi - lo))   # 틀린 방향은 보류보다 두 배 나쁨, 보류 폭은 좁을수록
            if best is None or key > best[0]:
                best = (key, wm, wd, lo, hi, right, wrong)
    _, wm, wd, lo, hi, right, wrong = best
    print(f"개발 {len(dev)}건: 월지×{wm} 일지×{wd} 신약≤{lo} 신강≥{hi} → 맞음 {right} · 반대 {wrong} · 중화 {len(dev)-right-wrong}")
    for path in sys.argv[2:]:
        test = load(path)
        right, wrong, got = score(test, wm, wd, lo, hi)
        print(f"시험 {path} {len(test)}건 → 맞음 {right} · 반대 {wrong} · 중화 {len(test)-right-wrong}")
    _, _, got = score(dev, wm, wd, lo, hi)
    for (p, gold, i), g in zip(dev, got):
        if g != gold:
            print(" ", i, " ".join(p), "정답", gold, "→", g, round(ratio(p, wm, wd), 3))
