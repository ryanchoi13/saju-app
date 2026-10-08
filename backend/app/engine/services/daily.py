"""Daily fortune projection backed by the complete Myeongri core query."""

from __future__ import annotations

from app.engine.korean import josa
from datetime import date

from app.engine.constants import GAN_KO, ZHI_KO
from app.engine.core.models import MyeongriCoreResult
from app.engine.semantic.queries import build_service_query
from app.engine.services.simple_menu import daily_choices
from app.engine.services.daily_menu import recommend_mode_menus
from app.engine.services.daily_guidance import build_daily_guidance
from app.engine.services import daily_copy, daily_menu_copy
from app.engine.services.annual_copy import seed_from
from app.engine.services.daily_scenarios import select_daily_scenario
from app.engine.services.daily_topics import select_daily_topics
from app.engine.semantic.overall import select_overall_domains
from app.engine.services.overall_narrative import render_overall


DAILY_FORTUNE_VERSION = "daily-fortune-v6-exact-daily-role"

_TEN_GOD_KO = {
    "peer": "비견",
    "rob_wealth": "겁재",
    "eating_god": "식신",
    "hurting_officer": "상관",
    "direct_wealth": "정재",
    "indirect_wealth": "편재",
    "direct_officer": "정관",
    "seven_killings": "편관",
    "direct_resource": "정인",
    "indirect_resource": "편인",
}

_RELATION_KO = {
    "stem_combination": "천간합",
    "branch_six_combination": "육합",
    "branch_three_combination": "삼합",
    "branch_half_combination": "반합",
    "branch_directional_combination": "방합",
    "stem_control": "천간극",
    "branch_clash": "충",
    "branch_punishment": "형",
    "branch_harm": "해",
    "branch_break": "파",
}
_SUPPORT_RELATIONS = {
    "stem_combination", "branch_six_combination", "branch_three_combination",
    "branch_half_combination", "branch_directional_combination",
}
_TENSION_RELATIONS = {
    "stem_control", "branch_clash", "branch_punishment", "branch_harm", "branch_break",
}

_OPERATION_KO = {
    "protect": "중요한 것을 지키고 정리하는 일",
    "resolve_conflict": "엇갈린 기준을 정리하는 일",
    "release_binding": "묶인 일을 작은 단계로 푸는 일",
    "drain": "과한 힘을 적절히 빼는 일",
    "mediate": "서로 다른 입장을 연결하는 일",
    "warm": "몸과 분위기를 따뜻하게 만드는 일",
    "cool": "흥분과 과열을 식히는 일",
    "moisten": "여유와 회복을 보충하는 일",
    "dry": "늘어진 흐름을 정돈하는 일",
    "support": "체력과 준비를 보강하는 일",
    "stabilize": "흐트러진 순서를 바로잡는 일",
    "preserve_balance": "무리하지 않고 균형을 지키는 일",
    "preserve_special_structure": "잘 작동하는 방식을 함부로 바꾸지 않는 일",
}

_ELEMENT_GUIDE = {
    "木": {
        "ko": "목",
        "numbers": "3, 8",
        "direction": "동쪽",
        "colors": ["그린", "청록"],
    },
    "火": {
        "ko": "화",
        "numbers": "2, 7",
        "direction": "남쪽",
        "colors": ["레드", "코랄"],
    },
    "土": {
        "ko": "토",
        "numbers": "5, 10",
        "direction": "중앙·생활권 안쪽",
        "colors": ["베이지", "브라운"],
    },
    "金": {
        "ko": "금",
        "numbers": "4, 9",
        "direction": "서쪽",
        "colors": ["화이트", "실버"],
    },
    "水": {
        "ko": "수",
        "numbers": "1, 6",
        "direction": "북쪽",
        "colors": ["네이비", "블랙"],
    },
}

_TALISMAN = {
    "木": ("성장진전부 (成長進展)", "성장과 꾸준한 진전", "wood_growth"),
    "火": ("명광활력부 (明光活力)", "표현과 활력의 보강", "fire_vitality"),
    "土": ("안정수호부 (安定守護)", "안정과 생활 기반의 정돈", "earth_stability"),
    "金": ("결단정리부 (決斷整理)", "판단과 정리의 힘", "metal_clarity"),
    "水": ("지혜유통부 (智慧流通)", "유연한 판단과 흐름", "water_wisdom"),
}

_ITEMS = {
    "record": {
        "木": "초록 표지 메모장", "火": "붉은색 포인트 펜", "土": "베이지 메모패드",
        "金": "메탈 소재 펜", "水": "남색 노트",
    },
    "organize": {
        "木": "나무 소재 카드 케이스", "火": "붉은색 포인트 파우치", "土": "베이지 지퍼 파우치",
        "金": "메탈 손목시계", "水": "남색 카드지갑",
    },
    "pace": {
        "木": "나무 손잡이 텀블러", "火": "보온 텀블러", "土": "도자기 머그",
        "金": "스테인리스 텀블러", "水": "남색 물병",
    },
    "move": {
        "木": "작은 스케치 노트", "火": "붉은색 키링", "土": "베이지 크로스백",
        "金": "휴대용 보조배터리", "水": "남색 휴대용 파우치",
    },
}

# Product defaults for male profiles; preserve the element and practical purpose.
_MALE_ITEM_OVERRIDES = {
    "organize": {"火": "붉은색 포인트 카드 케이스", "土": "베이지 카드지갑"},
    "move": {"土": "베이지 키 케이스", "水": "남색 슬림 카드지갑"},
}

_GOD_ITEM_GROUP = {
    "peer": "record",
    "rob_wealth": "organize",
    "eating_god": "pace",
    "hurting_officer": "record",
    "direct_wealth": "organize",
    "indirect_wealth": "move",
    "direct_officer": "organize",
    "seven_killings": "pace",
    "direct_resource": "record",
    "indirect_resource": "record",
}

_SHENSHA_KO = {
    "travel_horse": ("역마살", "움직임과 이동을 활용하면 흐름을 살리기 좋습니다."),
    "peach_blossom": ("도화살", "사람의 시선이 모이기 쉬우니 만남과 표현을 자연스럽게 활용해 보세요."),
    "flower_canopy": ("화개살", "혼자 집중해 생각을 정리하는 시간이 도움이 됩니다."),
    "solitary_star": ("고신살", "혼자 판단을 끝내기보다 필요한 말은 짧게라도 확인하세요."),
    "widow_star": ("과숙살", "감정을 안으로만 쌓지 말고 믿을 만한 사람과 나누는 편이 좋습니다."),
    "literary_star": ("문창귀인", "읽고 쓰고 정리하는 일에서 도움을 받기 좋습니다."),
    "heavenly_noble": ("천을귀인", "막힌 일은 혼자 붙들기보다 적절한 도움을 구해 보세요."),
}


def _daily_relationships(query: dict) -> list[dict]:
    changes = (query.get("activated_state") or {}).get("relationship_changes", [])
    found = []
    seen = set()
    for item in changes:
        members = item.get("members", [])
        if not any(member.get("pillar") == "timing:daily" for member in members):
            continue
        symbols = tuple(sorted(member.get("symbol", "") for member in members))
        key = (item.get("type"), symbols)
        if key in seen:
            continue
        seen.add(key)
        found.append(item)
    return found


def _independent_relation_counts(relations: list[dict]) -> tuple[int, int]:
    """Do not count multiple rules from the same symbols as separate evidence."""

    grouped: dict[tuple, set[str]] = {}
    for item in relations:
        members = tuple(sorted(
            (member.get("pillar"), member.get("position"), member.get("symbol"))
            for member in item.get("members", [])
        ))
        grouped.setdefault(members, set()).add(item.get("type"))
    supportive = 0
    tension = 0
    for types in grouped.values():
        if types & _TENSION_RELATIONS:
            tension += 1
        elif types & _SUPPORT_RELATIONS:
            supportive += 1
    return supportive, tension


def _daily_shensha(core: MyeongriCoreResult) -> list[str]:
    evidence = {item.id: item for item in core.evidence}
    names = []
    for item in core.shensha:
        if item.activation == "observed":
            continue
        matched_today = False
        for evidence_id in item.evidence_ids:
            source = evidence.get(evidence_id)
            timing_matches = source.source_values.get("timing_matches", []) if source else []
            if any(match.get("position") == "daily" for match in timing_matches):
                matched_today = True
                break
        if matched_today:
            names.append(item.name)
    return names


def _primary_operation(query: dict) -> dict:
    operations = query.get("synthesis", {}).get("favorable_operations", [])
    return operations[0] if operations else {"operation": "unconfirmed", "elements": []}


def _lucky_element(query: dict, daily_element: str) -> str:
    favorable = query.get("semantic_state", {}).get("favorable_elements", [])
    return favorable[0] if favorable else daily_element


def _menu_timing_element_weights(timing: dict, semantic: dict | None = None) -> dict[str, int]:
    """Conservative service translation, not a classical food prescription.

    Presence does not imply dietary need. Timing only modulates directions already
    assessed by the core; uncertain relationships never become transformations here.
    """
    semantic = semantic or {}
    favorable = set(semantic.get("favorable_elements", []))
    caution = set(semantic.get("caution_elements", []))
    exposure: dict[str, int] = {}
    for axis, weight in (("luck_cycle", 1), ("annual", 1), ("monthly", 2), ("daily", 3)):
        pillar = (timing.get(axis) or {}).get("pillar") or {}
        for key in ("stem_element", "branch_element"):
            element = pillar.get(key)
            if element:
                exposure[element] = exposure.get(element, 0) + weight
    cap = 4 if semantic.get("confidence") in {"low", "undetermined", None} else 6
    result = {}
    for element in favorable | caution:
        if element in favorable and element in caution:
            result[element] = 0  # Conflicting core directions: no invented resolution.
        else:
            value = min(cap, 3 + exposure.get(element, 0) // 3)
            result[element] = -value if element in caution else value
    return result


def _menu_climate_tags(query: dict) -> frozenset[str]:
    climate = query.get("diagnostics", {}).get("climate", {})
    if climate.get("status") == "insufficient":
        return frozenset()
    mapping = {"warming": "warm", "cooling": "cool", "moistening": "moisten", "stabilizing": "stabilize"}
    return frozenset(mapping[item["operation"]] for item in climate.get("recommended_operations", [])
                     if item.get("operation") in mapping)


def _item_group(operation: str, daily_god: str) -> str:
    # The daily ten-god decides the practical item category so the recommendation
    # can change with the day. The natal synthesis decides why and which element.
    return _GOD_ITEM_GROUP.get(daily_god, "record")


def _score(
    *,
    aligned: bool,
    supportive_count: int,
    tension_count: int,
    daily_god: str,
    monthly_god: str | None,
    annual_god: str | None,
    positive_shensha: int,
    caution_shensha: int,
    confidence: str,
) -> int:
    value = 76
    value += 6 if aligned else 0
    value += min(supportive_count, 2)
    value -= min(tension_count, 3) * 2
    value += 2 if daily_god == monthly_god else 0
    value += 1 if daily_god == annual_god else 0
    value += min(positive_shensha, 2)
    value -= min(caution_shensha, 2)
    if confidence in {"low", "undetermined"}:
        value = 76 + round((value - 76) * 0.6)
    return max(62, min(91, value))


def _badge_style(score: int) -> str:
    if score >= 83:
        return "background:#DCFCE7; color:#166534; border:1px solid #86EFAC;"
    if score <= 69:
        return "background:#FFF1F2; color:#9F1239; border:1px solid #FECDD3;"
    return "background:#FEF3C7; color:#78350F; border:1px solid #FDE68A;"


def _menu_curation(core, target_date, current_hour, account_key, lucky_element, operation_name,
                   ganji_han, timing_element_weights, query, recent_menus, seed) -> list[dict]:
    """[외식·배달] / [10분 집밥] / [가벼운 한 끼] 세 모드의 큐레이션 카드."""
    cards = []
    for mode in daily_menu_copy.MODE_KEYS:
        picked = recommend_mode_menus(
            mode=mode, target_date=target_date, current_hour=current_hour,
            day_master=account_key or core.input.birth_date.isoformat(),
            daily_ganji=ganji_han, lucky_element=lucky_element, primary_operation=operation_name,
            recent_menus=recent_menus, timing_element_weights=timing_element_weights,
            climate_tags=_menu_climate_tags(query),
        )
        cards.append(daily_menu_copy.compose_mode_card(mode, lucky_element, picked["menus"], seed))
    return cards


def _with_ro(word: str) -> str:
    return josa(word, "으로/로")


def build_daily_fortune(
    core: MyeongriCoreResult,
    user_name: str,
    target_date: date,
    *,
    current_hour: int | None = None,
    account_key: str | None = None,
    recent_menus: frozenset[str] = frozenset(),
    used_cuisines: frozenset[str] = frozenset(),
    used_menus: frozenset[str] = frozenset(),
    include_menu: bool = True,
) -> dict:
    """Render one evidence-aware day without allowing shensha to decide it alone."""

    query = build_service_query(core, "daily_overall")
    timing = query["timing"]
    daily = timing["daily"]
    monthly = timing["monthly"]
    annual = timing["annual"]
    cycle = timing.get("luck_cycle") or {}
    daily_god = daily["ten_god"]
    monthly_god = monthly.get("ten_god")
    annual_god = annual.get("ten_god")
    daily_pillar = daily["pillar"]
    ganji_han = daily_pillar["ganji"]
    ganji_display = f"{GAN_KO[ganji_han[0]]}{ZHI_KO[ganji_han[1]]}({ganji_han})"
    daily_element = daily_pillar["stem_element"]

    relations = _daily_relationships(query)
    supportive = [item for item in relations if item.get("type") in _SUPPORT_RELATIONS]
    tensions = [item for item in relations if item.get("type") in _TENSION_RELATIONS]
    supportive_count, tension_count = _independent_relation_counts(relations)
    shensha = _daily_shensha(core)
    positive_shensha = sum(name in {"literary_star", "heavenly_noble"} for name in shensha)
    caution_shensha = sum(name in {"solitary_star", "widow_star"} for name in shensha)
    lucky_element = _lucky_element(query, daily_element)
    timing_element_weights = _menu_timing_element_weights(timing, query["semantic_state"])
    aligned = daily_element in set(query["semantic_state"].get("favorable_elements", []))
    confidence = str(query["semantic_state"].get("confidence", "undetermined"))
    score = _score(
        aligned=aligned,
        supportive_count=supportive_count,
        tension_count=tension_count,
        daily_god=daily_god,
        monthly_god=monthly_god,
        annual_god=annual_god,
        positive_shensha=positive_shensha,
        caution_shensha=caution_shensha,
        confidence=confidence,
    )

    operation = _primary_operation(query)
    operation_name = operation.get("operation", "unconfirmed")
    operation_text = _OPERATION_KO.get(operation_name, "하루의 우선순위를 지키는 일")
    item_group = _item_group(operation_name, daily_god)
    item = _ITEMS[item_group][lucky_element]
    if core.input.gender == "male":
        item = _MALE_ITEM_OVERRIDES.get(item_group, {}).get(lucky_element, item)
    element = _ELEMENT_GUIDE[lucky_element]
    talisman_title, talisman_power, talisman_type = _TALISMAN[lucky_element]
    core_operation_confirmed = bool(query["synthesis"].get("favorable_operations"))
    core_element_confirmed = bool(query["semantic_state"].get("favorable_elements"))
    recommendation_confirmed = core_operation_confirmed and core_element_confirmed
    item_reason = (
        f"오늘은 {josa(operation_text, '이/가')} 우선입니다. 추천 아이템은 {item}이며, "
        f"{element['ko']} 기운의 색·소재는 보조 근거로만 반영했습니다."
        if recommendation_confirmed else
        f"추천 아이템은 {item}입니다. 오늘의 일진을 상징하는 색·소재로 고른 참고 아이템입니다."
    )
    menu_selection = (daily_choices(core.input, target_date, timing_element_weights, account_key)
                      if include_menu else dict(menus=[], meals=[], pool_size=0, pool_version=None,
                                                reason='', season=None, meal_period=None))

    seed = seed_from(target_date.isoformat(), account_key or core.input.birth_date.isoformat(), "daily")
    menu_curation = _menu_curation(
        core, target_date, current_hour, account_key, lucky_element, operation_name,
        daily_pillar["ganji"], timing_element_weights, query, recent_menus, seed,
    ) if include_menu else []

    scenario = select_daily_scenario(query)
    guidance = build_daily_guidance(query, daily_god, relations, scenario=scenario)
    topics = select_daily_topics(query, relations, shensha, scenario=scenario)
    overall = select_overall_domains(core, "daily")
    narrative = render_overall(overall)
    # Supporting stars retain their practical note, never the power to select
    # or reorder a life domain. Avoid restating a subject already in the body.
    represented = {p["domain"] for p in narrative["subjects"]}
    note_domains = {"reflection": "self", "learning": "learning", "relationships": "relationships",
                    "movement": "change", "rest": "wellbeing"}
    extra_notes = [n["text"] for n in topics["evidence"]["notes"]
                   if n["origin"].startswith("shensha:")
                   and note_domains.get(n["topic"], n["topic"]) not in represented
                   and not (n["topic"] == "relationships" and "love" in represented)]
    extra_notes.extend(n["text"] for n in topics["evidence"]["notes"]
                       if n["status"] == "assessed" and n["origin"] == "timing:daily-conditions")
    lead = daily_copy.lead_key(overall["primary_domains"])
    tone = daily_copy.tone_key(supportive_count, tension_count)
    story = daily_copy.compose_story(lead, tone, seed)
    time_tips = daily_copy.compose_tips(lead, seed, current_hour)
    outfit = daily_copy.compose_outfit(lucky_element)
    topics["evidence"]["legacy_primary_topic"] = topics["evidence"]["primary_topic"]
    topics["evidence"]["primary_topic"] = overall["primary_domains"][0] if overall["primary_domains"] else "balance"
    topics["evidence"]["primary_topics"] = overall["primary_domains"]
    topics["evidence"]["topic_basis"] = overall["version"]
    guidance["evidence"]["rendered_by"] = overall["version"]
    guidance["evidence"]["legacy_operation_analysis_only"] = True

    return {
        "engine_version": DAILY_FORTUNE_VERSION,
        "date": target_date.isoformat(),
        "day_ganji": ganji_display,
        "day_ganji_han": ganji_han,
        "day_ten_god": _TEN_GOD_KO[daily_god],
        "copy_version": daily_copy.COPY_VERSION,
        "story": story,
        "time_tips": time_tips,
        "menu_curation": menu_curation,
        "menu_footnote": daily_menu_copy.FOOTNOTE,
        "outfit": outfit,
        "title": daily_copy.sanitize(narrative["title"]),
        "score": score,
        "mode_badge": f"운세 {score}점",
        "badge_style": _badge_style(score),
        "advice": daily_copy.sanitize(" ".join([narrative["advice"]] + extra_notes)),
        "time_flow": daily_copy.sanitize_any(narrative["time_flow"]),
        "unified_advice": daily_copy.sanitize(narrative["unified_advice"]),
        "mindset": daily_copy.sanitize(narrative["title"]),
        "action": daily_copy.sanitize(narrative["unified_advice"]),
        "lucky_element": lucky_element,
        "lucky_item": item,
        "lucky_item_reason": item_reason,
        "lucky_number": element["numbers"],
        "lucky_direction": f"{element['direction']} ({element['ko']} 기운)",
        "recommended_menu": menu_selection["menus"][0] if menu_selection["menus"] else '',
        "recommended_menus": menu_selection["menus"],
        "recommended_meals": menu_selection["meals"],
        "recommended_menu_reason": daily_copy.sanitize(menu_selection["reason"]),
        "menu_pool_size": menu_selection["pool_size"],
        "menu_pool_version": menu_selection["pool_version"],
        "menu_context": {
            "season": menu_selection["season"],
            "meal_period": menu_selection["meal_period"],
        },
        "talisman": {
            "title": talisman_title,
            "power": talisman_power,
            "desc": (
                f"오늘의 보완 방향인 {element['ko']} 기운을 상징적으로 담은 일일 부적입니다."
                if recommendation_confirmed else
                f"오늘의 일진에 해당하는 {element['ko']} 기운을 상징적으로 담은 일일 부적입니다."
            ),
            "talisman_type": talisman_type,
        },
        "supporting_shensha": [_SHENSHA_KO[name][0] for name in shensha],
        "evidence_summary": {
            "overall": overall,
            "guidance": guidance["evidence"],
            "topics": topics["evidence"],
            "scope": query["scope"],
            "daily_ten_god": daily_god,
            "daily_relationship_types": list(dict.fromkeys(item["type"] for item in relations)),
            "independent_supportive_relations": supportive_count,
            "independent_tension_relations": tension_count,
            "primary_operation": operation_name,
            "lucky_element": lucky_element,
            "lucky_recommendation_basis": {
                "core_operation_confirmed": core_operation_confirmed,
                "element_source": "core_favorable" if core_element_confirmed else "daily_symbolic_reference",
                "recommendation_confirmed": recommendation_confirmed,
                "fallback_is_not_a_prescription": not recommendation_confirmed,
            },
            "confidence": confidence,
            "shensha_is_supporting_only": True,
        },
    }
