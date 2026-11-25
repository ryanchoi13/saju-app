"""일의 성격(십성) 매핑과 사업 선택지 비교 (2026-11-25 정오님 요청 1·2번).

왜 만들었나
- 직업운의 '필요한 오행 → 분야' 표는 IT와 외식이 같은 화(火) 칸에 들어가서, 카페와 IT 사업을 가르지 못했다.
- 그래서 업종을 '하는 일의 성격'(십성 다섯 줄기)으로 한 번 더 나눈다.
  만들어 내놓는 일 = 식상, 사고팔고 잇는 일 = 재성, 규칙과 책임을 지는 일 = 관성,
  알려 주고 돌보는 일 = 인성, 내 실력으로 서는 일 = 비겁.

판정 원칙
- 숫자 가중치 대신 이름 붙은 규칙(필요한 오행인가 · 원국에 있는 별인가 · 감당할 힘 · 지금 대운)을 쓴다.
  규칙 개수로 '잘 맞음/무난/걸림' 세 단계만 정한다.
- 업종 → 십성·오행 짝은 명리에서 널리 쓰는 관례를 따른 것이다(고서 한 권의 규칙이 아님).
- 시장 크기·경쟁·수익은 사주가 보는 영역이 아니라서 판정하지 않는다. 결과 문구에 그 점을 남긴다.
"""
from __future__ import annotations

from datetime import date

from app.engine.constants import GAN_WUXING
from app.engine.core.models import MyeongriCoreResult
from app.engine.services import business_timing as bt
from app.engine.services import career_copy as copy
from app.engine.services.element_balance import CONTROLLED_BY, CONTROLS, GENERATED_BY, GENERATES, element_tiers
from app.engine.services.theme_core import hidden_tally, tally

NATURES = ("output", "wealth", "officer", "resource", "peer")
NATURE_GODS = {
    "output": ("eating_god", "hurting_officer"), "wealth": ("direct_wealth", "indirect_wealth"),
    "officer": ("direct_officer", "seven_killings"), "resource": ("direct_resource", "indirect_resource"),
    "peer": ("peer", "rob_wealth"),
}
NATURE_NAME = {
    "output": "만들어 내놓는 일", "wealth": "사고팔고 잇는 일", "officer": "규칙과 책임을 지는 일",
    "resource": "알려 주고 돌보는 일", "peer": "내 실력으로 서는 일",
}
NATURE_EXAMPLES = {
    "output": "콘텐츠·앱 서비스·기획·디자인",
    "wealth": "중개·유통·커머스·영업",
    "officer": "운영 관리·인증·공공·품질 관리",
    "resource": "교육·상담·돌봄·연구",
    "peer": "1인 전문직·기술 자영업·현장 책임",
}
_TEN_GOD_GROUP = {
    "eating_god": "output", "hurting_officer": "output", "direct_wealth": "wealth", "indirect_wealth": "wealth",
    "direct_officer": "officer", "seven_killings": "officer", "direct_resource": "resource",
    "indirect_resource": "resource", "peer": "peer", "rob_wealth": "peer",
}

# 업종 목록: 성격(첫째가 주된 성격) + 업종 오행(관례).
CATALOG = {
    "content_app": dict(name="콘텐츠·앱 서비스", natures=("output",), element="火"),
    "saas": dict(name="구독형 소프트웨어(B2B)", natures=("output", "officer"), element="火"),
    "commerce_broker": dict(name="중개·제휴 커머스 플랫폼", natures=("wealth",), element="水"),
    "online_shop": dict(name="온라인 판매·쇼핑몰", natures=("wealth", "output"), element="水"),
    "media_ads": dict(name="방송·광고·마케팅", natures=("output",), element="火"),
    "cafe_food": dict(name="카페·외식 매장", natures=("output", "wealth"), element="火"),
    "education": dict(name="교육·강의", natures=("resource", "output"), element="木"),
    "consulting": dict(name="상담·컨설팅", natures=("resource",), element="土"),
    "care_service": dict(name="돌봄·요양 서비스", natures=("resource", "officer"), element="土"),
    "senior_goods": dict(name="시니어 용품 유통", natures=("wealth",), element="水"),
    "real_estate": dict(name="부동산·임대", natures=("wealth",), element="土"),
    "finance": dict(name="금융·투자", natures=("wealth", "officer"), element="金"),
    "manufacturing": dict(name="제조·정밀 기술", natures=("peer", "officer"), element="金"),
    "freelance_pro": dict(name="1인 전문직·프리랜서", natures=("peer", "output"), element=None),
}

FIT_TEXT = {
    "need_good": "이 일의 성격이 내게 필요한 기운과 닿아요.",
    "need_avoid": "이 일의 성격이 내게 덜 맞는 기운이라 오래 하면 힘이 빠져요.",
    "natal_rich": "원국에 이 별이 뚜렷해서 타고난 감각이 있어요.",
    "natal_none": "원국에 없는 별이라 감각을 배워서 채워야 해요.",
    "heavy_for_weak": "기운이 가벼운 편이라 이 일의 무게를 혼자 지기 버거워요.",
    "peer_for_strong": "이미 기운이 든든한데 같은 기운을 더하는 일이라 고집과 경쟁이 세져요.",
    "cycle_same": "지금 10년 대운이 이 일과 같은 성격이라 흐름을 타요.",
    "cycle_rob": "지금 10년 대운이 재물을 나눠 갖는 기운이라 사고파는 일에서 남는 것이 줄어요.",
    "element_good": "업종의 오행이 내게 필요한 기운이에요.",
    "element_avoid": "업종의 오행이 내게 덜 맞는 기운이에요.",
    "partner_risk": "원국에 나와 같은 기운(비겁)이 많아 동업·공동 투자에서 돈 나누는 문제로 부딪히기 쉬워요.",
    "partner_help": "기운이 가벼운 편이라 믿을 동업자가 힘을 보태요.",
    "capital_keep_cycle": "지금은 새던 돈을 막고 지키는 10년이라, 큰돈을 먼저 거는 구조는 부담이 커요.",
    "capital_rob": "겁재가 있는 사주라 큰돈을 한 번에 넣으면 사람과 경쟁 쪽으로 새요.",
    "capital_light": "적은 돈으로 시작하는 구조라 지키는 10년에도 부담이 작아요.",
}
GOOD_RULES = {"need_good", "natal_rich", "cycle_same", "element_good", "partner_help", "capital_light"}
FIT_GRADE_NAME = {"good": "잘 맞음", "ok": "무난", "hard": "걸림"}
LIMIT_NOTE = ("사주로는 사람과 시기의 흐름만 봐요. 시장 크기·경쟁·수익은 판정하지 않았으니, "
              "작은 비용으로 실제 반응을 먼저 재 보고 정하세요.")
MULTI_NOTE = ("일에서 빠지기 쉬운 함정이 '여러 기회에 손대다 힘이 흩어지는 것'이에요. "
              "한 가지를 주력으로 정하고, 나머지는 주력이 자리 잡은 뒤에 여세요.")


def _group_element(dm: str, group: str) -> str:
    e = GAN_WUXING[dm]
    return {"peer": e, "output": GENERATES[e], "wealth": CONTROLS[e], "officer": CONTROLLED_BY[e],
            "resource": GENERATED_BY[e]}[group]


def _strength(core: MyeongriCoreResult) -> str:
    s = str(core.synthesis.strength_state or "")
    return copy.strength_key(s) if copy.strength_decided(s) else "unknown"


def nature_fit(core: MyeongriCoreResult, nature: str, year: int | None = None, *, with_cycle: bool = True) -> dict:
    """한 성격(십성 줄기)이 이 사람에게 맞는지. with_cycle=False 면 원국만 본다(평생 풀이용). rules 는 걸린 규칙 이름, good/hard 는 그중 좋은·걸리는 것."""
    dm = core.natal_facts.pillars["day"].stem
    tiers = element_tiers(core)["tiers"]
    tier = tiers[_group_element(dm, nature)]
    gods = NATURE_GODS[nature]
    natal = sum(tally(core, gods).values())
    hidden = sum(hidden_tally(core, gods).values())
    strength = _strength(core)
    cyc = bt.cycle_for_year(core, year or date.today().year) if with_cycle else None
    cyc_group = _TEN_GOD_GROUP.get((cyc or {}).get("ten_god"))

    rules = []
    if tier == "good":
        rules.append("need_good")
    elif tier == "avoid":
        rules.append("need_avoid")
    if natal >= 2:
        rules.append("natal_rich")
    elif natal == 0 and hidden == 0:
        rules.append("natal_none")
    if strength == "weak" and nature in ("output", "wealth", "officer"):
        rules.append("heavy_for_weak")
    if strength == "strong" and nature == "peer":
        rules.append("peer_for_strong")
    if cyc_group == nature:
        rules.append("cycle_same")
    if cyc_group == "peer" and nature == "wealth":
        rules.append("cycle_rob")
    return _graded(rules)


def _graded(rules: list[str]) -> dict:
    good = [r for r in rules if r in GOOD_RULES]
    hard = [r for r in rules if r not in GOOD_RULES and r != "natal_none"]
    # natal_none 은 '걸림'이 아니라 '배워서 채움'이라 등급에는 넣지 않는다
    diff = len(good) - len(hard)
    grade = "good" if diff >= 2 else "hard" if diff < 0 else "ok"
    return dict(grade=grade, grade_name=FIT_GRADE_NAME[grade], rules=rules,
                good=[FIT_TEXT[r] for r in good], hard=[FIT_TEXT[r] for r in hard],
                note=[FIT_TEXT[r] for r in rules if r == "natal_none"])


def nature_ranking(core: MyeongriCoreResult, year: int | None = None, *, with_cycle: bool = True) -> list[dict]:
    """다섯 성격을 맞는 순서로. 같은 등급이면 좋은 규칙이 많은 쪽, 그다음 NATURES 순서."""
    order = {"good": 0, "ok": 1, "hard": 2}
    rows = []
    for i, n in enumerate(NATURES):
        f = nature_fit(core, n, year, with_cycle=with_cycle)
        rows.append(dict(nature=n, name=NATURE_NAME[n], examples=NATURE_EXAMPLES[n], **f,
                         _key=(order[f["grade"]], -len(f["good"]) + len(f["hard"]), i)))
    rows.sort(key=lambda r: r["_key"])
    for r in rows:
        r.pop("_key")
    return rows


def nature_text(core: MyeongriCoreResult, lead_group: str, year: int | None = None) -> str:
    """직업운 '잘 맞는 일의 종류' 칸에 붙는 한 단락. 오행 분야표가 못 가르던 것(IT↔외식)을 일의 성격으로 가른다."""
    ranks = nature_ranking(core, year, with_cycle=False)   # 평생 풀이라 지금 대운은 빼고 원국만
    top, low = ranks[0], ranks[-1]
    if top["grade"] == "hard":
        return ""
    parts = [f"일의 성격으로 나눠 보면 {top['name']}({top['examples']})이 가장 잘 맞아요."]
    if top["good"]:
        parts.append(top["good"][0])
    parts.append("타고난 감각과 필요한 기운이 같은 쪽을 가리키는 셈이에요." if top["nature"] == lead_group
                 else "위의 직무가 타고난 감각이라면, 이쪽은 필요한 기운까지 함께 따진 답이에요.")
    if low["grade"] == "hard" and low["hard"]:
        parts.append(f"반대로 {low['name']}({low['examples']})은 덜 맞아요. {low['hard'][0]}")
    return " ".join(parts)


def _option_rules(core: MyeongriCoreResult, opt: dict, year: int) -> tuple[list[str], dict]:
    natures = tuple(opt.get("natures") or CATALOG.get(opt.get("category", ""), {}).get("natures") or ())
    if not natures:
        raise ValueError(f"업종 성격을 알 수 없어요: {opt.get('name') or opt.get('category')}")
    element = opt.get("element", CATALOG.get(opt.get("category", ""), {}).get("element"))
    main = nature_fit(core, natures[0], year)
    rules = list(main["rules"])
    tiers = element_tiers(core)["tiers"]
    if element and tiers.get(element) == "good":
        rules.append("element_good")
    elif element and tiers.get(element) == "avoid":
        rules.append("element_avoid")
    peers = bt.natal_peer_count(core)
    strength = _strength(core)
    if opt.get("partnership"):
        if peers >= 2:
            rules.append("partner_risk")
        elif strength == "weak":
            rules.append("partner_help")
    capital = opt.get("capital", "mid")
    cyc = bt.cycle_for_year(core, year)
    cyc_group = _TEN_GOD_GROUP.get((cyc or {}).get("ten_god"))
    if capital == "high":
        if cyc_group in ("officer", "resource"):
            rules.append("capital_keep_cycle")
        if sum(tally(core, ("rob_wealth",)).values()) >= 1:
            rules.append("capital_rob")
    elif capital == "low" and cyc_group in ("officer", "resource"):
        rules.append("capital_light")
    return rules, dict(natures=natures, element=element)


def compare_options(core: MyeongriCoreResult, options: list[dict], start_year: int | None = None) -> dict:
    """사업 선택지 비교(사업 궁합).

    options: [{name, category(CATALOG 키) 또는 natures+element, partnership: bool, capital: low|mid|high}]
    돌려주는 것: 선택지별 등급·맞는 점·걸리는 점·문 열기 좋은 해, 5년 흐름, 공통 안내.
    """
    year = start_year or date.today().year
    flow = bt.five_year_flow(core, year)
    lead = copy.lead_group(tally(core), hidden_tally(core))
    rows = []
    for opt in options:
        rules, meta = _option_rules(core, opt, year)
        g = _graded(rules)
        nature = meta["natures"][0]
        open_years = [r["year"] for r in flow if r["events"]["open"]["grade"] == "good"]
        same_years = [r["year"] for r in flow if r["group"] == nature and r["events"]["open"]["grade"] != "caution"]
        rows.append(dict(
            name=opt.get("name") or CATALOG.get(opt.get("category", ""), {}).get("name", ""),
            category=opt.get("category"), natures=list(meta["natures"]),
            nature_name=NATURE_NAME[nature], element=meta["element"],
            grade=g["grade"], grade_name=g["grade_name"], good=g["good"], hard=g["hard"], note=g["note"],
            rules=rules, open_years=open_years, nature_years=same_years,
        ))
    order = {"good": 0, "ok": 1, "hard": 2}
    ranked = sorted(rows, key=lambda r: (order[r["grade"]], -len(r["good"]) + len(r["hard"])))
    notes = [LIMIT_NOTE]
    if len(options) >= 2 and lead in ("wealth", "output"):
        notes.insert(0, MULTI_NOTE)
    return dict(options=ranked, flow=flow, notes=notes, lead_group=lead, start_year=year)
