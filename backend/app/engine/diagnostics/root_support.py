"""Describe raw root support and separately sourced functional judgments.

Presence alone does not establish effective force. Assessed restrictions retain
their evidence and never erase the original hidden-stem/root observations.
"""

from collections.abc import Mapping, Sequence

from app.engine.core.models import PillarFact, RelationshipResult, RootFacts


ROOT_SUPPORT_VERSION = "root-support-v2-natal-function-effects"
ROOT_SUPPORT_SOURCES = [
    {
        "id": "dt-ren-shuaiwang",
        "work": "滴天髓闡微", "section": "十七、衰旺", "attribution": "任鐵樵 주석",
        "url": "https://zh.wikisource.org/zh-hant/滴天髓闡微",
        "scope": "뿌리의 종류와 계절 외 지지 기반을 살펴야 한다는 해석 원칙",
    },
    {
        "id": "woo-kim-2022-root-support",
        "work": "천간과 지지의 상조와 상극에 관한 연구",
        "section": "Ⅱ.1, 표 1 및 통근 위치 비교", "attribution": "우연화·김만태(2022)",
        "url": "https://www.jdaos.org/archive/view_article?pid=jdaos-42-0-109",
        "scope": "뿌리 종류·위치·일부 계절 예외의 문헌 정리. 예측 정확도 검증 아님",
    },
]

_ORDER = {"year": 0, "month": 1, "day": 2, "hour": 3}
_ROOT_CATEGORIES = {
    "木": {"寅": "vigorous", "卯": "vigorous", "亥": "growth", "辰": "residual", "未": "storage"},
    "火": {"巳": "vigorous", "午": "vigorous", "寅": "growth", "未": "residual", "戌": "storage"},
    "金": {"申": "vigorous", "酉": "vigorous", "巳": "growth", "戌": "residual", "丑": "storage"},
    "水": {"亥": "vigorous", "子": "vigorous", "申": "growth", "丑": "residual", "辰": "storage"},
}


def _position(stem_pillar: str, branch_pillar: str) -> str:
    if branch_pillar == "month":
        return "month"
    if stem_pillar == branch_pillar:
        return "own_branch"
    if stem_pillar == "day":
        return {"hour": "hour", "year": "year"}.get(branch_pillar, "unknown")
    if stem_pillar not in _ORDER or branch_pillar not in _ORDER:
        return "unknown"
    return "adjacent" if abs(_ORDER[stem_pillar] - _ORDER[branch_pillar]) == 1 else "distant"


def describe_root_support(
    roots: RootFacts,
    pillars: Mapping[str, PillarFact | None],
    relationships: Sequence[RelationshipResult],
) -> list[dict]:
    """Preserve candidate roots for every visible stem, including shared roots."""
    month = pillars.get("month")
    month_branch = month.branch if month else None
    observations = []
    for root in roots.items:
        branch_pillar = pillars.get(root.branch_pillar)
        branch = branch_pillar.branch if branch_pillar else None
        category = _ROOT_CATEGORIES.get(root.element, {}).get(branch, "unclassified")
        if root.element == "土":
            # Fire/earth joint-location rules and seasonal exceptions require
            # their own interpretation; do not label every earth root alike.
            category = "earth_source_dependent"
        qualifications = []
        if root.element == "金" and branch == "巳" and month_branch in {"巳", "午", "未"}:
            qualifications.append("metal_growth_root_in_summer_requires_review")
        if root.element == "土" and branch == "寅" and month_branch in {"寅", "卯", "辰"}:
            qualifications.append("earth_root_in_spring_tiger_requires_review")
        if month_branch is None:
            qualifications.append("month_unavailable")
        ordinary_support = (
            "substantial_candidate" if category in {"vigorous", "growth"}
            else "limited_candidate" if category in {"residual", "storage"}
            else "unrated"
        )
        judgments = [target for relation in relationships for target in relation.function_targets
                     if target.get("effect_status") == "established"
                     and target.get("function_kind") == "root_support"
                     and target.get("stem_pillar") == root.stem_pillar
                     and target.get("root_connection", {}).get("branch_pillar") == root.branch_pillar
                     and target.get("root_connection", {}).get("hidden_stem") == root.hidden_stem]
        effect_states = {target["function_state"] for target in judgments}
        observations.append({
            **root.model_dump(mode="json"),
            "root_id": f"root:{root.branch_pillar}:{root.hidden_stem}",
            "branch": branch,
            "category": category,
            "ordinary_support": ordinary_support,
            "position": _position(root.stem_pillar, root.branch_pillar),
            "pillar_distance": (
                abs(_ORDER[root.stem_pillar] - _ORDER[root.branch_pillar])
                if root.stem_pillar in _ORDER and root.branch_pillar in _ORDER else None
            ),
            "seasonal_qualifications": qualifications,
            "effectiveness": next(iter(effect_states)) if len(effect_states) == 1 else "undetermined",
            "effect_evidence_ids": sorted({eid for j in judgments for eid in j.get("effect_evidence_ids", [])}),
            "effect_rules": sorted({j["effect_rule"] for j in judgments}),
            "related_relationship_ids": [
                relation.id for relation in relationships
                if relation.type.startswith("branch_") and any(
                    member.get("pillar") == root.branch_pillar for member in relation.members
                )
            ],
            "source_ids": [source["id"] for source in ROOT_SUPPORT_SOURCES],
        })
    return observations
