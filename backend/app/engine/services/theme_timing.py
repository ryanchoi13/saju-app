"""테마운 3단(타이밍) 공통 계산 — 앞으로 12개월 + 세운 맥락.

배경: 예전 3단은 '올해 1~12월'의 월운만 봤다. 월지는 해마다 같은 자리로 돌아오므로
(2월=寅, 3월=卯 …) 같은 사람에게 해마다 같은 달이 나왔다. 이 모듈은 두 가지를 바꾼다.

1. 기간: 달력 연도가 아니라 '보는 날부터 12개월'. 지난 달은 보여 주지 않는다.
2. 세운: 연도마다 annual 범위로 따로 해석해 '이 기간의 큰 흐름' 한 줄로 보여 주고,
   월 고르기에서는 같은 월운 점수끼리 순서를 정할 때만 쓴다.

docs/overall-interpretation-policy.md 를 지킨다.
- 가중치 합산 금지: 월운 점수와 세운 점수를 더하지 않는다. (월운, 세운 일치) 순의 사전식 비교.
  세운만으로는 월이 뽑히지 않는다(긴 기간의 맥락은 후보가 없는 새 분야를 만들 수 없다).
- 넓은 기간에서 좁은 기간 신호를 읽지 않는다: 세운 줄은 annual 범위 선택만 쓴다.
- 성별로 배우자성을 정하지 않는다: 십신 가산 없이 엔진의 기존 도메인 선택만 쓴다.
- 근거가 없는 해(base/후보 없음)에는 채우기용 문장을 내지 않는다.
"""

from __future__ import annotations

from datetime import date

from app.engine.calendar import to_solar
from app.engine.constants import GAN_KO, ZHI_KO
from app.engine.core.models import MyeongriCoreResult
from app.engine.semantic.overall import select_overall_domains
from app.engine.services.career_copy import MODE_SCORE
from app.engine.timing import calculate_timing

WINDOW_MONTHS = 12
MAX_INFLECTIONS = 3


def window_start(core: MyeongriCoreResult, today: date | None = None) -> tuple[int, int]:
    """보는 날 기준 첫 달. 그달 15일(월운 기준일)이 지났으면 다음 달부터."""
    if today is None:
        raw = (core.timing.daily or {}).get("date") if core.timing else None
        today = date.fromisoformat(raw) if raw else date.today()
    y, m = today.year, today.month
    if today.day > 15:
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return y, m


def window_months(start: tuple[int, int], n: int = WINDOW_MONTHS) -> list[tuple[int, int]]:
    y, m = start
    out = []
    for _ in range(n):
        out.append((y, m))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def _pick(selection: dict, domains: tuple[str, ...]):
    primary = set(selection.get("primary_domains") or ())
    pool = [c for c in selection.get("selected", ()) if c["domain"] in domains]
    pool.sort(key=lambda c: (c["domain"] not in primary, domains.index(c["domain"])))
    return pool[0] if pool else None


def scan(core: MyeongriCoreResult, domains: tuple[str, ...], start: tuple[int, int]) -> list[dict]:
    """12개월 각 달의 월운 후보와, 그 달이 속한 세운의 후보를 따로 계산한다."""
    birth = to_solar(core.input.birth_date, core.input.calendar_type, core.input.is_leap_month)
    rows = []
    annual_cache: dict[tuple, dict] = {}
    for y, m in window_months(start):
        target = date(y, m, 15)
        if target < birth:
            continue
        timing, _, _ = calculate_timing(core.input, core.natal_facts.pillars, target_date=target)
        month_cand = _pick(select_overall_domains(core, "monthly", timing=timing), domains)
        cycle = (timing.luck_cycle.get("current") or {}).get("pillar", {}).get("ganji")
        annual_ganji = timing.annual["pillar"]["ganji"]
        key = (cycle, annual_ganji)
        if key not in annual_cache:
            cand = _pick(select_overall_domains(core, "annual", timing=timing), domains)
            annual_cache[key] = dict(
                ganji=annual_ganji, luck_cycle=cycle,
                mode=cand.get("mode") if cand else None,
                domain=cand["domain"] if cand else None,
                source_ids=list(cand["source_ids"]) if cand else [])
        annual = annual_cache[key]
        m_mode = month_cand.get("mode") if month_cand else None
        rows.append(dict(
            year=y, month=m,
            score=MODE_SCORE.get(m_mode, 0), mode=m_mode,
            domain=month_cand["domain"] if month_cand else None,
            source_ids=list(month_cand["source_ids"]) if month_cand else [],
            annual=annual, annual_score=MODE_SCORE.get(annual["mode"], 0)))
    return rows


def choose(rows: list[dict]) -> list[tuple[dict, str]]:
    """career_copy.choose_inflections 와 같은 규칙에 '세운 일치'를 둘째 기준으로 더한 사전식 선택.

    월운 점수가 0인 달은 세운이 아무리 강해도 뽑지 않는다. 결과는 시간 순.
    """
    idx = {id(r): i for i, r in enumerate(rows)}
    opp = sorted((r for r in rows if r["score"] >= 1),
                 key=lambda r: (-r["score"], -r["annual_score"], idx[id(r)]))
    cau = sorted((r for r in rows if r["score"] <= -1),
                 key=lambda r: (r["score"], r["annual_score"], idx[id(r)]))
    picked: list[tuple[dict, str]] = []
    if opp:
        picked.append((opp.pop(0), "opportunity"))
    if cau:
        picked.append((cau.pop(0), "caution"))
    rest = [(r, "opportunity") for r in opp] + [(r, "caution") for r in cau]
    rest.sort(key=lambda x: (-abs(x[0]["score"]),
                             -(x[0]["annual_score"] if x[1] == "opportunity" else -x[0]["annual_score"]),
                             idx[id(x[0])]))
    for item in rest:
        if len(picked) >= MAX_INFLECTIONS:
            break
        picked.append(item)
    return sorted(picked, key=lambda x: idx[id(x[0])])


def annual_contexts(rows: list[dict]) -> list[dict]:
    """기간 안의 세운별 맥락. 근거가 있는(base 가 아닌) 해만, 처음 나오는 달 순서로."""
    seen, out = set(), []
    for r in rows:
        a = r["annual"]
        key = (a["luck_cycle"], a["ganji"])
        if key in seen:
            continue
        seen.add(key)
        if a["mode"] in (None, "base"):
            continue
        out.append(dict(a, from_year=r["year"], from_month=r["month"]))
    return out


def month_label(year: int, month: int, prev_year: int | None) -> str:
    return f"{month}월" if prev_year == year else f"{year}년 {month}월"


def period_caption(start: tuple[int, int]) -> str:
    y, m = start
    return f"{y}년 {m}월부터 12개월, 각 달 15일의 월운을 그해 세운·대운과 함께 짚었습니다."


# 세운 한 줄. 사건 단정 없이 '흐름'만. 테마별 · 모드별.
YEAR_LINE = {
    "love": {
        "join": "가까운 사람과 마음이 잘 맞물리는 흐름이 이어져요.",
        "recovery": "관계의 긴장이 조금씩 풀리고 편안해지는 흐름이에요.",
        "change": "관계의 거리와 속도를 다시 조율하게 되는 흐름이에요.",
        "mixed": "가까워지는 기운과 흔들리는 기운이 함께 있는 흐름이에요.",
    },
    "career": {
        "join": "함께 일할 사람과 손발이 잘 맞는 흐름이 이어져요.",
        "recovery": "일의 부담이 조금씩 정돈되는 흐름이에요.",
        "change": "역할이나 일하는 방식을 다시 조율하게 되는 흐름이에요.",
        "mixed": "기회와 변동이 함께 들어오는 흐름이에요.",
    },
    "health": {
        "join": "생활 리듬이 비교적 순하게 맞춰지는 흐름이에요.",
        "recovery": "쉼과 회복을 챙기기 좋은 흐름이에요.",
        "change": "생활 리듬이 흔들리기 쉬워 일정을 넉넉히 잡을 흐름이에요.",
        "mixed": "편안함과 분주함이 함께 오가는 흐름이에요.",
    },
}


def _ganji_ko(ganji: str) -> str:
    return GAN_KO.get(ganji[:1], "") + ZHI_KO.get(ganji[1:2], "")


def year_lines(theme: str, contexts: list[dict]) -> list[str]:
    """예: '2027 정미년 · 가까운 사람과 마음이 잘 맞물리는 흐름이 이어져요.'
    세운은 입춘에 바뀌므로 1월(15일 기준)은 앞 해의 세운에 속한다."""
    table = YEAR_LINE[theme]
    out = []
    for c in contexts:
        text = table.get(c["mode"])
        if not text:
            continue
        year = c["from_year"] - 1 if c["from_month"] == 1 else c["from_year"]
        out.append(f"{year} {_ganji_ko(c['ganji'])}년 · {text}")
    return out


# ---------------------------------------------------------------------------
# 세 테마 공용 조립
# ---------------------------------------------------------------------------
def build_tier3(core: MyeongriCoreResult, theme: str, domains: tuple[str, ...], compose,
                year: int | None = None) -> dict:
    """compose(inflections) 는 각 테마 copy.compose_tier3 를 감싼 함수. [(달력 월, kind)] 를 받는다.

    year 를 주면(옛 호출·테스트) 그해 1~12월, 없으면 보는 날부터 12개월.
    """
    start = (year, 1) if year else window_start(core)
    rows = scan(core, domains, start)
    picked = choose(rows)
    months = compose([(r["month"], kind) for r, kind in picked])
    prev = None
    evidence = []
    for (r, _), m in zip(picked, months):
        m["year"] = r["year"]
        m["display"] = month_label(r["year"], r["month"], prev)
        prev = r["year"]
        evidence.append(dict(year=r["year"], month=r["month"], kind=m["kind"], mode=r["mode"],
                             domain=r["domain"], source_ids=r["source_ids"],
                             annual=dict(ganji=r["annual"]["ganji"], mode=r["annual"]["mode"])))
    contexts = annual_contexts(rows)
    return dict(start=start, months=months, year_lines=year_lines(theme, contexts),
                caption=period_caption(start), evidence_months=evidence,
                evidence_years=[dict(ganji=c["ganji"], luck_cycle=c["luck_cycle"], mode=c["mode"],
                                     domain=c["domain"], source_ids=c["source_ids"]) for c in contexts])


def tier3_html(t3: dict, attr: str, heading: str, disclaimer: str, no_inflection: str) -> str:
    from html import escape
    lines = "".join(f'<li data-{attr}-year-line="{i}">{escape(t)}</li>'
                    for i, t in enumerate(t3["year_lines"], start=1))
    flow = (f'<div data-{attr}-year-flow="true"><h3>이 기간의 큰 흐름</h3>'
            f'<ul style="padding-left:18px;">{lines}</ul></div>') if lines else ""
    if t3["months"]:
        rows = "".join(
            f'<li data-{attr}-month="{m["year"]}-{m["month"]:02d}" data-month-kind="{m["kind"]}">'
            f'<strong>{escape(m["display"])} · {escape(m["label"])}</strong><br>{escape(m["text"])}</li>'
            for m in t3["months"])
        body = f'<ul style="padding-left:18px;">{rows}</ul>'
    else:
        body = f'<p data-{attr}-month="none">{escape(no_inflection)}</p>'
    return (f'<section data-{attr}-tier="3" data-paywall="unlocked"><h2>{escape(heading)}</h2>'
            f'<p class="reading-caption">{escape(t3["caption"])} {escape(disclaimer)}</p>'
            f'{flow}{body}</section>')
