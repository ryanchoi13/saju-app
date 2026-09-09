"""Qualitative day-master strength diagnosis without a fixed score."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from app.engine.constants import GAN_WUXING, ZHI_WUXING
from app.engine.facts.hidden_stems import get_hidden_stems
from app.engine.relationships.assessment import strength_relation_needs_review
from app.engine.diagnostics.root_support import (
    ROOT_SUPPORT_SOURCES,
    ROOT_SUPPORT_VERSION,
    describe_root_support,
)
from app.engine.core.models import (
    ConfidenceLevel,
    DiagnosticResult,
    Evidence,
    EvidenceLayer,
    HiddenStemRole,
    PillarFact,
    RelationshipResult,
    RootFacts,
    StrengthState,
    TenGod,
    TenGodFacts,
)


STRENGTH_DIAGNOSTIC_VERSION = "strength-diagnostic-v4-decisive-natal-conditions"
_GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
_CONTROLS = {"木": "土", "火": "金", "土": "水", "金": "木", "水": "火"}
_SUPPORTING_GODS = {
    TenGod.PEER, TenGod.ROB_WEALTH, TenGod.DIRECT_RESOURCE, TenGod.INDIRECT_RESOURCE
}
_DRAINING_GODS = {
    TenGod.EATING_GOD, TenGod.HURTING_OFFICER,
    TenGod.DIRECT_WEALTH, TenGod.INDIRECT_WEALTH,
    TenGod.DIRECT_OFFICER, TenGod.SEVEN_KILLINGS,
}


def _season_relation(day_element: str, month_element: str) -> str:
    if day_element == month_element:
        return "same_element"
    if _GENERATES[month_element] == day_element:
        return "month_generates_day"
    if _GENERATES[day_element] == month_element:
        return "day_generates_month"
    if _CONTROLS[month_element] == day_element:
        return "month_controls_day"
    return "day_controls_month"


def _touches_day_or_month(relation: RelationshipResult) -> bool:
    return any(member.get("pillar") in {"day", "month"} for member in relation.members)


def diagnose_strength(
    day_master: str,
    pillars: Mapping[str, PillarFact | None],
    roots: RootFacts,
    ten_gods: TenGodFacts,
    relationships: Sequence[RelationshipResult],
) -> tuple[DiagnosticResult, list[Evidence]]:
    """Apply ordered qualitative checks; never total them into a strength score."""

    month = pillars.get("month")
    if day_master not in GAN_WUXING or month is None:
        return (
            DiagnosticResult(
                module="strength", status="insufficient",
                summary="일간 또는 월주 정보가 없어 강약을 진단할 수 없음",
                confidence=ConfidenceLevel.UNDETERMINED,
            ),
            [],
        )

    day_element = GAN_WUXING[day_master]
    month_element = ZHI_WUXING[month.branch]
    season_relation = _season_relation(day_element, month_element)
    season_supportive = season_relation in {"same_element", "month_generates_day"}

    day_roots = [item for item in roots.items if item.stem_pillar == "day"]
    all_root_contexts = describe_root_support(roots, pillars, relationships)
    root_contexts = [
        root for root in all_root_contexts if root["stem_pillar"] == "day"
    ]
    substantial_roots = [
        root for root in root_contexts
        if root["ordinary_support"] == "substantial_candidate"
        and not root["seasonal_qualifications"]
        and root["effectiveness"] != "reduced"
    ]
    month_roots = [item for item in day_roots if item.branch_pillar == "month"]
    strong_month_root = any(item.hidden_role is HiddenStemRole.MAIN for item in month_roots)
    exact_main_month_root = any(
        item.hidden_role is HiddenStemRole.MAIN and item.exact_stem for item in month_roots
    )

    visible_gods = {
        item.ten_god for item in ten_gods.visible
        if item.pillar != "day" and item.ten_god is not TenGod.DAY_MASTER
    }
    visible_support = visible_gods & _SUPPORTING_GODS
    visible_drain = visible_gods & _DRAINING_GODS
    restricted_stems = {target["stem_pillar"] for relation in relationships for target in relation.function_targets
                        if target.get("function_kind") == "visible_role"
                        and target.get("effect_status") == "established" and target.get("function_state") == "reduced"}
    replacement_roles = [
        {'relationship_id': relation.id, 'original_pillars': [m['pillar'] for m in relation.members
             if GAN_WUXING.get(m['symbol']) != relation.transformation.target_element],
         **relation.effect_assessment['replacement_role']}
        for relation in relationships if relation.transformation
        and relation.transformation.kind == 'pair'
        and relation.transformation.status.value == 'established'
        and relation.effect_assessment.get('replacement_role')
    ]
    converted_original_pillars = {k for item in replacement_roles for k in item['original_pillars']}
    # Reduced is not zero: do not use a restricted helper to certify strength,
    # but retain original support/drain facts as possible counter-evidence.
    operative_support = {item.ten_god for item in ten_gods.visible
                         if item.pillar != "day" and item.pillar not in restricted_stems | converted_original_pillars
                         and item.ten_god in _SUPPORTING_GODS}
    support_profiles = [
        {
            "pillar": item.pillar, "stem": item.stem, "ten_god": item.ten_god.value,
            "root_contexts": [
                root for root in all_root_contexts if root["stem_pillar"] == item.pillar
            ],
        }
        for item in ten_gods.visible
        if item.pillar != "day" and item.ten_god in _SUPPORTING_GODS
    ]
    # Multiple visible helpers can rely on the same hidden carrier. These IDs
    # describe independent locations, not force points or confirmed support.
    support_anchor_ids = sorted({
        root["root_id"] for profile in support_profiles for root in profile["root_contexts"]
    })
    unstable_relations = [
        item for item in relationships
        if _touches_day_or_month(item) and strength_relation_needs_review(item, day_element)
    ]

    signals = [
        {'step': 'transformation_roles', 'replacement_roles': replacement_roles,
         'converted_original_pillars': sorted(converted_original_pillars),
         'extra_element_points_awarded': False, 'replacement_force_established': False},
        {"step": "season", "relation": season_relation, "supportive": season_supportive},
        {
            "step": "rooting", "root_count": len(day_roots),
            "month_root": bool(month_roots), "main_month_root": strong_month_root,
            "exact_main_month_root": exact_main_month_root,
            "root_contexts": root_contexts,
            "substantial_root_candidate_ids": [root["root_id"] for root in substantial_roots],
            "root_support_rule_version": ROOT_SUPPORT_VERSION,
        },
        {
            "step": "support", "visible_ten_gods": sorted(god.value for god in visible_support),
            "visible_support_profiles": support_profiles,
            "distinct_root_anchor_ids": support_anchor_ids,
            "operative_support_ten_gods": sorted(g.value for g in operative_support),
            "restricted_visible_pillars": sorted(restricted_stems),
        },
        {
            "step": "drain_pressure", "visible_ten_gods": sorted(god.value for god in visible_drain),
        },
        {
            "step": "relationship_change",
            "unstable_relationship_ids": [item.id for item in unstable_relations],
        },
    ]

    season_only_weakness_blocked = False
    resource = next(element for element, child in _GENERATES.items() if child == day_element)
    support_elements = {day_element, resource}
    main_support_only = all(p.branch_element in support_elements for p in pillars.values() if p)
    any_hidden_support = any(GAN_WUXING[h.stem] in support_elements
                             for p in pillars.values() if p for h in get_hidden_stems(p.branch).stems)
    all_storage_support_reduced = bool(root_contexts) and all(r["effectiveness"] == "reduced" for r in root_contexts)
    peer_only_helpers = bool(visible_support) and visible_support <= {TenGod.PEER, TenGod.ROB_WEALTH}
    helpers_share_reduced_roots = all(profile["root_contexts"] and all(
        r["effectiveness"] == "reduced" for r in profile["root_contexts"]) for profile in support_profiles)
    storage_deficiency = (season_relation == "month_controls_day" and all_storage_support_reduced
                          and peer_only_helpers and helpers_share_reduced_roots
                          and bool(visible_drain))
    decisive_rule = "ordinary-season-root-support-v1"
    if (season_relation == "same_element" and strong_month_root and operative_support
            and not visible_drain and main_support_only):
        state = StrengthState.EXTREMELY_STRONG
        decisive_rule = "ren-seasonal-dominant-support-v1"
    elif season_supportive and strong_month_root and operative_support:
        state = StrengthState.STRONG
    elif not season_supportive and not day_roots and not visible_support and not any_hidden_support:
        state = StrengthState.EXTREMELY_WEAK
        decisive_rule = "ren-no-root-or-support-v1"
    elif storage_deficiency:
        state = StrengthState.WEAK
        decisive_rule = "ren-season-control-reduced-storage-support-v1"
        accounted = {r.id for r in relationships if r.type == "branch_clash"
                     and any(t.get("effect_status") == "established" and t.get("function_state") == "reduced"
                             and t.get("element") == day_element for t in r.function_targets)}
        unstable_relations = [r for r in unstable_relations if r.id not in accounted]
    elif not season_supportive and substantial_roots and not visible_support:
        # A vigorous/growth root is evidence against season-only weakness even
        # without a visible helper. It does not by itself establish strength.
        state = StrengthState.UNDETERMINED
        season_only_weakness_blocked = True
    elif not season_supportive and not (day_roots and visible_support):
        state = StrengthState.WEAK
        decisive_rule = "ordinary-weakness-direction-candidate"
    else:
        # Opposing observations do not prove that they cancel each other.
        state = StrengthState.UNDETERMINED

    counter_evidence = []
    signals[-1]["unstable_relationship_ids"] = [r.id for r in unstable_relations]
    signals.append({"step": "decision", "rule": decisive_rule,
                    "storage_support_reduced": storage_deficiency,
                    "extreme_direction_requires_separate_assessment": state in {
                        StrengthState.EXTREMELY_STRONG, StrengthState.EXTREMELY_WEAK}})
    if season_supportive and visible_drain:
        counter_evidence.append("득령 신호와 함께 설기·소모·압박 십성이 천간에 존재함")
    if not season_supportive and day_roots:
        counter_evidence.append("월령은 비우호적이지만 일간의 통근이 존재함")
    if not season_supportive and visible_support:
        counter_evidence.append("월령은 비우호적이지만 생조 십성이 천간에 존재함")
    if season_only_weakness_blocked:
        counter_evidence.append("록왕·장생 뿌리 후보가 있어 실효 비교 없이 계절과 천간 생조 부재만으로 약함을 확정하지 않음")
    if unstable_relations:
        counter_evidence.append("일주 또는 월주 관계의 작용이 미확정이므로 강약 결론이 변할 수 있음")
    unresolved = (state is StrengthState.UNDETERMINED
                  or decisive_rule == "ordinary-weakness-direction-candidate")
    if decisive_rule == "ordinary-weakness-direction-candidate":
        counter_evidence.append("비우호적인 계절과 통근·천간 생조 관찰은 약함의 후보이며 숨은 생조와 실효 비교는 남아 있음")
    if unresolved:
        counter_evidence.append("통근과 생조의 존재만으로 실제 힘이 균형을 이룬다고 확정할 수 없음")

    mixed = bool(counter_evidence)
    status = "conditional" if unstable_relations or unresolved else "completed"
    confidence = (
        ConfidenceLevel.LOW if unstable_relations or unresolved
        else ConfidenceLevel.MEDIUM if mixed or state is StrengthState.BALANCED
        else ConfidenceLevel.HIGH
    )
    evidence_id = "evidence:strength:ordered-diagnosis"
    evidence = Evidence(
        id=evidence_id,
        layer=EvidenceLayer.JUDGMENT,
        source_module=STRENGTH_DIAGNOSTIC_VERSION,
        rule_code="season-root-support-drain-relationship-order",
        description="득령·통근·생조·극설소모·관계 변화 순서의 정성 강약 판정",
        source_values={
            "signals": signals, "fixed_score_used": False,
            "root_support_sources": ROOT_SUPPORT_SOURCES,
            "season_only_weakness_blocked": season_only_weakness_blocked,
            "root_category_does_not_establish_effectiveness": True,
        },
        supports=[f"strength:{state.value}"],
        reliability=confidence,
    )
    return (
        DiagnosticResult(
            module="strength", status=status, conclusion=state.value,
            summary=("돕는 힘과 제약하는 힘의 실효가 확인되지 않아 강약 판단을 보류함"
                     if unresolved else "고정 점수 없이 순차 근거로 일간의 강약 구간을 판정함"),
            signals=signals,
            recommended_operations=[
                {"operation": "preserve_balance", "when": state is StrengthState.BALANCED},
                {"operation": "recheck_after_relationship_changes", "required": bool(unstable_relations) or unresolved},
            ],
            counter_evidence=counter_evidence,
            confidence=confidence,
            evidence_ids=[evidence_id],
        ),
        [evidence],
    )
