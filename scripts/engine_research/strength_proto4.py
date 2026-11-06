"""세력 저울 4차: 득령·득지·득세 100점법 + 합·충 반영 (2026-11-06).

1~3차는 가중치를 데이터로 골라 과적합했다. 4차는 **이론에서 먼저 정하고** 데이터는 채점만 한다.
  자리 점수(일간 제외 7자리, 합 100): 연간 10 · 월간 10 · 시간 10 · 연지 10 · 월지 30 · 일지 20 · 시지 10
  지지는 정기(본기) 오행으로 본다(실무 100점법). 비겁·인성이면 돕는 점수.
합·충(옵션별로 켜고 끔):
  SANHAP  삼합·방합이 세 글자 다 있으면 그 지지들을 합화 오행으로 본다
  BANHAP  왕지(子午卯酉)가 낀 반합이면 두 지지를 합화 오행으로 반쯤(0.5) 본다
  CHUNG   월지가 다른 지지와 충이면 월지 점수를 절반으로(득령 약화)
  GANHAP  일간이 월간·시간과 천간합이면 일간을 돕는 힘에서 그 짝 자리 점수를 뺀다(합거)
판정: 돕는 점수 ≥ HI → 신강, ≤ LO → 신약, 사이 보류. HI·LO 는 이론값 60/40 고정(옵션 평가 때 바꾸지 않음).

python scripts/engine_research/strength_proto4.py            # set1+set2(개발) 채점, 옵션 조합별
python scripts/engine_research/strength_proto4.py --final F  # 고른 옵션으로 시험 세트 F 를 한 번만 채점
"""
import os as _os, sys as _sys
ROOT = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
DATA = _os.path.join(ROOT, 'docs', 'engine')
_sys.path[:0] = [_os.path.dirname(_os.path.abspath(__file__))]
import itertools
from strength_proto import STEM_EL, GEN, load

PARENT = {v: k for k, v in GEN.items()}
BRANCH_EL = dict(zip("子丑寅卯辰巳午未申酉戌亥", "水土木木土火火土金金土水"))
SANHAP = [("申子辰", "水"), ("亥卯未", "木"), ("寅午戌", "火"), ("巳酉丑", "金"),
          ("寅卯辰", "木"), ("巳午未", "火"), ("申酉戌", "金"), ("亥子丑", "水")]
BANHAP = {frozenset("申子"): "水", frozenset("子辰"): "水", frozenset("亥卯"): "木", frozenset("卯未"): "木",
          frozenset("寅午"): "火", frozenset("午戌"): "火", frozenset("巳酉"): "金", frozenset("酉丑"): "金"}
CHUNG = {frozenset("子午"), frozenset("丑未"), frozenset("寅申"), frozenset("卯酉"), frozenset("辰戌"), frozenset("巳亥")}
GANHAP = {frozenset("甲己"), frozenset("乙庚"), frozenset("丙辛"), frozenset("丁壬"), frozenset("戊癸")}
STEM_W = {"y": 10, "m": 10, "h": 10}
BRANCH_W = {"y": 10, "m": 30, "d": 20, "h": 10}
HI, LO = 60, 40


def support_points(pillars, opt):
    y, m, d, h = pillars
    dm = STEM_EL[d[0]]
    good = {dm, PARENT[dm]}
    branches = {"y": y[1], "m": m[1], "d": d[1], "h": h[1]}
    # 지지마다 (오행, 비중) 목록 — 기본은 정기 하나
    parts = {k: [(BRANCH_EL[b], 1.0)] for k, b in branches.items()}
    present = set(branches.values())
    if "SANHAP" in opt:
        for trio, el in SANHAP:
            if set(trio) <= present:
                for k, b in branches.items():
                    if b in trio:
                        parts[k] = [(el, 1.0)]
    if "BANHAP" in opt:
        for pair, el in BANHAP.items():
            if pair <= present:
                for k, b in branches.items():
                    if b in pair and parts[k] == [(BRANCH_EL[b], 1.0)]:
                        parts[k] = [(BRANCH_EL[b], 0.5), (el, 0.5)]
    bw = dict(BRANCH_W)
    if "CHUNG" in opt and any(frozenset((branches["m"], branches[k])) in CHUNG for k in ("y", "d", "h")):
        bw["m"] = BRANCH_W["m"] / 2
    total = sum(STEM_W.values()) + sum(bw.values())
    pts = 0.0
    stems = {"y": y[0], "m": m[0], "h": h[0]}
    for k, s in stems.items():
        if "GANHAP" in opt and k in ("m", "h") and frozenset((d[0], s)) in GANHAP:
            continue          # 일간과 합한 짝은 일간을 돕지 못한다(합거)
        pts += STEM_W[k] * (STEM_EL[s] in good)
    for k, ps in parts.items():
        pts += bw[k] * sum(w for e, w in ps if e in good)
    return 100 * pts / total


def judge(p):
    return "strong" if p >= HI else "weak" if p <= LO else None


def score(cases, opt):
    right = wrong = 0
    for pl, gold, _ in cases:
        j = judge(support_points(pl, opt))
        right += j == gold; wrong += j is not None and j != gold
    return right, wrong, len(cases) - right - wrong


def auc(cases, opt):
    s = [support_points(pl, opt) for pl, g, _ in cases if g == "strong"]
    w = [support_points(pl, opt) for pl, g, _ in cases if g == "weak"]
    return sum((a > b) + .5 * (a == b) for a in s for b in w) / (len(s) * len(w))


OPTIONS = ("SANHAP", "BANHAP", "CHUNG", "GANHAP")

if __name__ == "__main__":
    if "--final" in _sys.argv:
        path = _sys.argv[_sys.argv.index("--final") + 1]
        opt = set(_sys.argv[_sys.argv.index("--final") + 2:])
        cases = load(path)
        r, w, u = score(cases, opt)
        print(f"[시험 1회] {path} {len(cases)}건 옵션 {sorted(opt)}: 맞음 {r}({r/len(cases):.0%}) 반대 {w}({w/len(cases):.0%}) 보류 {u} AUC {auc(cases, opt):.3f}")
        _sys.exit()
    dev = load(_os.path.join(DATA, "strength-answer-set", "set1.csv")) + load(_os.path.join(DATA, "strength-answer-set", "set2.csv"))
    print(f"개발 {len(dev)}건 (신강 {sum(g == 'strong' for _, g, _ in dev)} · 신약 {sum(g == 'weak' for _, g, _ in dev)}), 판정선 {LO}/{HI} 고정")
    for k in range(len(OPTIONS) + 1):
        for opt in itertools.combinations(OPTIONS, k):
            r, w, u = score(dev, set(opt))
            print(f"  {'+'.join(opt) or '기본':28s} 맞음 {r:2d}({r/len(dev):.0%}) 반대 {w:2d}({w/len(dev):.0%}) 보류 {u:2d}  AUC {auc(dev, set(opt)):.3f}")


# ---- 5차(같은 날 오류 분석 뒤): 틀린 21건 중 15건이 '실령인데 신강' — 고전은 여기·중기 통근(戌未의 丁, 丑辰의 癸 등)을
# 무겁게 보는데 정기 100점법은 이를 버린다. 반대로 '인다신약'은 비겁 뿌리 없이 인성만 많은 경우.
# 이론 규칙(데이터로 고르지 않음):
#   지지는 지장간 비중(9·3·18 계열)으로 나누고, 일간과 같은 오행(비겁 뿌리)은 ×ROOT(=2) — 통근 중시
#   비겁(천간 + 뿌리)이 하나도 없으면 인성은 절반만 친다 — 인성만으로는 버티지 못한다(인다신약)
from strength_proto import HIDDEN

ROOT_MULT = 2.0


def support_points_v5(pillars, opt=()):
    y, m, d, h = pillars
    dm = STEM_EL[d[0]]; res = PARENT[dm]
    bw = dict(BRANCH_W)
    branches = {"y": y[1], "m": m[1], "d": d[1], "h": h[1]}
    if "CHUNG" in opt and any(frozenset((branches["m"], branches[k])) in CHUNG for k in ("y", "d", "h")):
        bw["m"] = BRANCH_W["m"] / 2
    peer = resp = total = 0.0
    for k, s in {"y": y[0], "m": m[0], "h": h[0]}.items():
        total += STEM_W[k]
        if "GANHAP" in opt and k in ("m", "h") and frozenset((d[0], s)) in GANHAP:
            continue
        peer += STEM_W[k] * (STEM_EL[s] == dm); resp += STEM_W[k] * (STEM_EL[s] == res)
    for k, b in branches.items():
        for e, share in HIDDEN[b]:
            w = bw[k] * share
            if e == dm:
                peer += w * ROOT_MULT; total += w * (ROOT_MULT - 1) + w
            else:
                total += w; resp += w * (e == res)
    if peer == 0:
        total -= resp / 2; resp /= 2
    return 100 * (peer + resp) / total


def score_v5(cases, opt=(), lo=LO, hi=HI):
    right = wrong = 0
    for pl, gold, _ in cases:
        p = support_points_v5(pl, opt)
        j = "strong" if p >= hi else "weak" if p <= lo else None
        right += j == gold; wrong += j is not None and j != gold
    return right, wrong, len(cases) - right - wrong


def auc_v5(cases, opt=()):
    s = [support_points_v5(pl, opt) for pl, g, _ in cases if g == "strong"]
    w = [support_points_v5(pl, opt) for pl, g, _ in cases if g == "weak"]
    return sum((a > b) + .5 * (a == b) for a in s for b in w) / (len(s) * len(w))
