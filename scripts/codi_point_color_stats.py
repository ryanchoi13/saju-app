"""사례 카드 다시 세기 — 포인트 색은 어디에 오는가 (2026-11-25).

docs/codi-knowledge/cases/<나라>-<집단>-<스타일>-<시즌>.md 의 카드 표(룩북·실착)를 읽어,
착장마다 '색 있는 색'(무채·가라앉은 색이 아닌 색)이 어느 자리에 있는지 센다.
정오님 질문(2026-11-24 시안): 행운 색이 가방·신발로 자주 가는데 실제 착장도 그런가.

- 자리: 아우터 / 상의 / 이너(상의 칸의 '+' 뒤) / 하의 / 다리(타이츠·양말) / 신발 / 가방 / 모자 / 머플러·스카프 / 벨트
- 색: 글자에서 색 낱말을 찾는다(화면 근사값 기록이라 근사). 공식집 2절 기준으로
  무채·가라앉은 색(블랙·흰·회색·네이비·베이지·브라운·카키·올리브·데님 등)은 '바탕', 나머지는 '색 있음'.
  올리브·카키는 공식집에서 가라앉은 색이라 바탕으로 센다.
- 장신구(시계·목걸이·선글라스 등)와 무늬 설명만 있는 칸은 세지 않는다.
- 결과: python3 scripts/codi_point_color_stats.py  → 표를 출력하고 /tmp/codi_point_stats.json 저장
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "docs" / "codi-knowledge" / "cases"

# 색 낱말 → (분류, 대표 이름). 긴 낱말을 먼저 찾는다.
CHROMA = {
    "버건디": "버건디", "와인": "버건디", "레드": "빨강", "빨강": "빨강", "빨간": "빨강", "체리": "빨강",
    "핑크": "핑크", "분홍": "핑크", "로즈": "핑크", "코랄": "코랄", "살구": "코랄", "피치": "코랄",
    "오렌지": "주황", "주황": "주황", "러스트": "러스트", "테라코타": "러스트", "적갈": "러스트", "벽돌": "러스트",
    "머스타드": "노랑", "머스터드": "노랑", "옐로": "노랑", "노랑": "노랑", "노란": "노랑", "연노랑": "노랑", "버터": "노랑", "레몬": "노랑",
    "그린": "초록", "초록": "초록", "녹색": "초록", "포레스트": "초록", "세이지": "초록", "민트": "초록", "에메랄드": "초록", "연두": "초록",
    "블루": "파랑", "파랑": "파랑", "파란": "파랑", "코발트": "파랑", "하늘": "파랑", "스카이": "파랑", "라이트블루": "파랑", "로열": "파랑",
    "퍼플": "보라", "보라": "보라", "라벤더": "보라", "플럼": "보라", "자주": "보라", "바이올렛": "보라",
    "청록": "청록", "틸": "청록", "터콰이즈": "청록",
}
NEUTRAL = ["블랙", "검정", "검은", "화이트", "흰", "아이보리", "크림", "오프화이트", "에크루", "회색", "그레이", "멜란지", "차콜",
           "네이비", "남색", "베이지", "샌드", "카멜", "탄", "토프", "오트밀", "브라운", "갈색", "초콜릿", "카키", "올리브",
           "데님", "인디고", "중청", "연청", "진청", "흑청", "생지", "실버", "은색", "골드", "금색", "누드", "스톤", "그레이지"]
# 다크 네이비·라이트 그레이 등은 NEUTRAL 낱말로 잡힌다. '하늘'이 '하늘색' 등으로 쓰인다.
SKIP_SEG = ("시계", "목걸이", "귀걸이", "팔찌", "반지", "선글라스", "안경", "이어폰", "헤어", "폰", "우산")
BAG = ("가방", "백", "토트", "숄더", "크로스", "클러치", "파우치", "에코", "버킷백", "호보")
HAT = ("모자", "캡", "비니", "버킷", "베레", "헌팅", "바라클라바", "이어머프", "귀마개")
SCARF = ("머플러", "스카프", "목도리", "스톨", "숄")
LEGS = ("타이츠", "양말", "삭스", "레그워머", "니삭스", "스타킹")
BELT = ("벨트",)

WORDS = sorted(list(CHROMA) + NEUTRAL, key=len, reverse=True)


def colors_in(text):
    """글자에서 색 낱말을 찾아 [(분류, 이름)]. 괄호 안을 먼저 본다."""
    inside = " ".join(re.findall(r"\(([^)]*)\)", text)) or text
    found, used = [], [False] * len(inside)
    for w in WORDS:
        for m in re.finditer(re.escape(w), inside):
            if any(used[m.start():m.end()]):
                continue
            for i in range(m.start(), m.end()):
                used[i] = True
            found.append((m.start(), ("chroma", CHROMA[w]) if w in CHROMA else ("neutral", w)))
    return [c for _, c in sorted(found)]


def split_segments(text):
    return [s.strip() for s in re.split(r"\s\+\s|,\s(?![^()]*\))", text) if s.strip() and s.strip() not in ("—", "-", "없음", "안 보임")]


def slot_of(seg, column):
    if any(k in seg for k in SKIP_SEG):
        return None
    if any(k in seg for k in LEGS):
        return "다리"
    # '숄더백'·'오프숄더'의 '숄'을 머플러(숄)로 세지 않는다(2026-11-26 고침).
    if any(k in seg.replace("숄더", "") for k in SCARF):
        return "머플러·스카프"
    if any(k in seg for k in HAT):
        return "모자"
    if any(k in seg for k in BELT):
        return "벨트"
    if column == "가방·소품":
        return "가방" if any(k in seg for k in BAG) else None
    return column


def parse_file(path):
    m = re.match(r"(kr|us|eu|jp)-(f20|m40)-([a-z-]+)-(fw|ss)\.md", path.name)
    if m:
        country, group, style, season = m.groups()
    else:
        # 2차 조사 파일(r2-<번호>-<이름>.md)은 첫 줄 <!-- stats: <나라> <집단> <시즌> --> 으로 읽는다(2026-11-25).
        m2 = re.match(r"r2-(\d+)-[a-z0-9-]+\.md", path.name)
        meta = re.search(r"<!--\s*stats:\s*(kr|us|eu|jp)\s+(f20|m40)\s+(fw|ss)\s*-->", path.read_text(encoding="utf-8")) if m2 else None
        if not meta:
            return []
        country, group, season = meta.groups()
        style = "r2-" + m2.group(1)
    rows, header, kind = [], None, None
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            header = None if not line.strip() else header
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells and cells[0] == "#":
            header = cells
            kind = "실착" if ("스냅 번호" in cells or "판정(크부장)" in cells) else "룩북"
            continue
        if not header or set(cells[0]) <= {"-", " "} or not cells[0].isdigit() or len(cells) != len(header):
            continue
        rec = dict(zip(header, cells))
        slots = []
        for col in ("아우터", "상의·이너", "하의", "신발", "가방·소품"):
            text = rec.get(col, "")
            for i, seg in enumerate(split_segments(text)):
                base = col
                if col == "상의·이너":
                    base = "상의" if i == 0 else "이너"
                s = slot_of(seg, base)
                if not s:
                    continue
                for cls, name in colors_in(seg):
                    slots.append((s, cls, name))
        situation = rec.get("상황·계절", "")
        rows.append(dict(file=path.name, country=country, group=group, style=style, season=season, kind=kind,
                         situation=situation, test=bool(rec.get("시험용")), slots=slots))
    return rows


def summarize(rows, label):
    n = len(rows)
    if not n:
        return None
    chroma_slots = Counter()
    per_outfit = Counter()
    shoe = Counter()
    bag = Counter()
    chroma_names = Counter()
    for r in rows:
        cs = {(s, name) for s, cls, name in r["slots"] if cls == "chroma"}
        per_outfit[min(len({s for s, _ in cs}), 3)] += 1
        for s in {s for s, _ in cs}:
            chroma_slots[s] += 1
        for s, name in cs:
            chroma_names[name] += 1
        sh = [(cls, name) for s, cls, name in r["slots"] if s == "신발"]
        bg = [(cls, name) for s, cls, name in r["slots"] if s == "가방"]
        if sh:
            shoe["색 있음" if any(c == "chroma" for c, _ in sh) else "바탕색"] += 1
        if bg:
            bag["색 있음" if any(c == "chroma" for c, _ in bg) else "바탕색"] += 1
    return dict(label=label, n=n, with_color=n - per_outfit[0], per_outfit=dict(per_outfit),
                slots=dict(chroma_slots.most_common()), names=dict(chroma_names.most_common()),
                shoe=dict(shoe), bag=dict(bag))


def pct(a, b):
    return f"{a}/{b} ({round(100 * a / b)}%)" if b else "-"


def main():
    rows = [r for p in sorted(CASES.glob("*.md")) for r in parse_file(p)]
    out = {"rows": len(rows), "groups": []}
    combos = []
    for group in ("f20", "m40"):
        for kind in ("룩북", "실착"):
            for season in ("fw", "ss"):
                sel = [r for r in rows if r["group"] == group and r["kind"] == kind and r["season"] == season and r["country"] == "kr"]
                combos.append((f"한국 {'20대 여성' if group == 'f20' else '40대 남성'} · {season.upper()} · {kind}", sel))
        sel = [r for r in rows if r["group"] == group and r["country"] in ("us", "eu")]
        combos.append((f"미국·유럽 {'20대 여성' if group == 'f20' else '40대 남성'} · FW · 룩북", sel))
    for label, sel in combos:
        s = summarize(sel, label)
        if not s:
            continue
        out["groups"].append(s)
        print(f"\n## {label} — {s['n']}착장")
        print(f"- 색 있는 자리가 하나 이상: {pct(s['with_color'], s['n'])}  · 자리 수 분포 {s['per_outfit']}")
        print("- 색이 온 자리(착장 수): " + ", ".join(f"{k} {v}" for k, v in s["slots"].items()))
        print("- 색 이름: " + ", ".join(f"{k} {v}" for k, v in list(s["names"].items())[:10]))
        print(f"- 신발: {s['shoe']} · 가방: {s['bag']}")
    # 스타일별(한국, 룩북+실착)
    by_style = defaultdict(list)
    for r in rows:
        if r["country"] == "kr":
            by_style[(r["group"], r["style"], r["season"])].append(r)
    out["styles"] = {}
    print("\n## 한국 칸별 — 색 있는 착장 비율 · 가장 많이 온 자리")
    for key in sorted(by_style):
        s = summarize(by_style[key], "-".join(key))
        out["styles"]["-".join(key)] = s
        top = ", ".join(f"{k} {v}" for k, v in list(s["slots"].items())[:3])
        print(f"- {'-'.join(key)}: {pct(s['with_color'], s['n'])} · {top} · 신발 {s['shoe']} · 가방 {s['bag']}")
    # 상황별(룩북 상황 칸이 있는 것만)
    out["situations"] = {}
    print("\n## 한국 룩북 상황별")
    for group in ("f20", "m40"):
        for tag in ("출근", "주말", "데이트", "여행", "하객"):
            sel = [r for r in rows if r["country"] == "kr" and r["group"] == group and r["kind"] == "룩북" and tag in r["situation"]]
            s = summarize(sel, f"{group}-{tag}")
            if s:
                out["situations"][f"{group}-{tag}"] = s
                top = ", ".join(f"{k} {v}" for k, v in list(s["slots"].items())[:4])
                print(f"- {group} {tag}: {s['n']}착장 · 색 있음 {pct(s['with_color'], s['n'])} · {top}")
    # 상황별(실착, 상황 칸이 있는 것 — 2차 조사부터)
    print("\n## 한국 실착 상황별(2차 조사 파일 r2-*만 — 1차 카드의 상황 칸은 섞지 않음)")
    for group in ("f20", "m40"):
        for tag in ("출근", "주말", "데이트", "나들이"):
            sel = [r for r in rows if r["country"] == "kr" and r["group"] == group and r["kind"] == "실착" and r["style"].startswith("r2-") and tag in r["situation"]]
            s = summarize(sel, f"{group}-{tag}-실착")
            if s:
                out["situations"][f"{group}-{tag}-실착"] = s
                top = ", ".join(f"{k} {v}" for k, v in list(s["slots"].items())[:4])
                print(f"- {group} {tag} 실착: {s['n']}착장 · 색 있음 {pct(s['with_color'], s['n'])} · {top} · 신발 {s['shoe']}")
    Path("/tmp/codi_point_stats.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
