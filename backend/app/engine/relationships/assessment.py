"""Bounded natal function judgments under the recorded interpretation policy.

These are model judgments, not observed efficacy or event predictions. Raw
roots/relations survive. Timing relations require their own assessment.
"""
from app.engine.constants import GAN_WUXING, ZHI_WUXING
from app.engine.core.models import Evidence, EvidenceLayer, ConfidenceLevel, TransformationStatus
from app.engine.facts.hidden_stems import get_hidden_stems
from app.engine.relationships.combination_context import (
    shared_officer_context, rooted_water_context, metal_fire_release_context,
)

VERSION = "natal-function-assessment-v3"
POLICY = "ren-natal-functions-with-scoped-ziping-comparison-v3"
REFERENCE_ONLY_TYPES = frozenset({"branch_punishment", "branch_harm", "branch_break"})
_ORDER = {"year": 0, "month": 1, "day": 2, "hour": 3}
_VIGOROUS = {"木": set("寅卯"), "火": set("巳午"), "金": set("申酉"), "水": set("亥子")}
_GROWTH = {"木": "亥", "火": "寅", "金": "巳", "水": "申"}
_STORAGE = set("辰戌丑未")
_GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
_CONTROLS = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
REN_SOURCE = {"work": "滴天髓闡微", "attribution": "任鐵樵 주석", "section": "八、地支; 十七、衰旺; 六親論十一、閒神",
              "url": "https://zh.wikisource.org/zh-hant/滴天髓闡微"}
ZIPING_SOURCE = {"work": "子平真詮評注", "attribution": "沈孝瞻 원저·徐樂吾 평주 구분", "section": "四、論十干配合性情; 五、論十干合而不合",
                 "url": "https://www.ncc.com.tw/fate/paleo/bg/bg_032.htm"}


def _transformation_basis(relation, pillars):
    """A bounded negative test; available supplies never certify transformation.

    The source requires branch assistance. To avoid mistaking an indirect
    supply for absence we include the target's generating element, every hidden
    role, and all four branches. Missing-hour inputs cannot pass this test.
    """
    target = relation.transformation.target_element if relation.transformation else None
    if relation.type != "stem_combination" or not target:
        return None
    if any(not pillars.get(k) for k in _ORDER):
        return {"status": "unreviewed", "reason": "incomplete_natal_pillars"}
    support = {target, next(e for e, child in _GENERATES.items() if child == target)}
    carriers = [{"pillar": k, "stem": h.stem, "element": h.element, "role": h.role.value}
                for k in _ORDER for h in get_hidden_stems(pillars[k].branch).stems
                if h.element in support]
    return {"status": "observed" if carriers else "absent", "target": target,
            "support_elements": sorted(support), "branch_carriers": carriers,
            "scope": "current_natal_chart_only", "source": ZIPING_SOURCE,
            "absence_rule": "no-target-or-generating-branch-carrier-v1"}


def _opposed_original_context(relation, pillars, roots, clashed):
    """Narrow ordinary-role exception for a month-aligned target.

    Encodes the fourth comparison example's continuing native context, not a
    general proof that roots forbid transformation. Fake transformations can
    retain roots: this result must NOT set transformation=not_established.
    """
    day = pillars.get("day")
    target = relation.transformation.target_element if relation.transformation else None
    if not day or _CONTROLS[day.stem_element] != target:
        return None
    keys = {m["pillar"] for m in relation.members}
    if "day" in keys:
        return None
    original = next((m for m in relation.members if GAN_WUXING[m["symbol"]] == day.stem_element), None)
    if not original:
        return None
    # A visible controller of the native side needs a separate force judgment.
    if any(p and k not in keys and _CONTROLS[p.stem_element] == day.stem_element
           for k, p in pillars.items()):
        return None
    member_roots = [r for r in roots.items if r.stem_pillar == original["pillar"]
                    and r.branch_pillar != "day" and r.branch_pillar not in clashed
                    and pillars[r.branch_pillar].branch in _VIGOROUS.get(day.stem_element, set())]
    own_roots = [r for r in roots.items if r.stem_pillar == "day" and r.branch_pillar == "day"
                 and "day" not in clashed and day.branch in (
                     _VIGOROUS.get(day.stem_element, set()) | {_GROWTH.get(day.stem_element)})]
    if not member_roots or not own_roots:
        return None
    return {"day_element": day.stem_element, "target_element": target,
            "original_member": original,
            "member_vigorous_roots": [r.model_dump(mode="json") for r in member_roots],
            "day_own_root": [r.model_dump(mode="json") for r in own_roots],
            "transformation_verdict": "unresolved",
            "basis": "bounded_implementation_interpretation_of_source_context"}


def is_reference_only(relation):
    return relation.type in REFERENCE_ONLY_TYPES


def requires_role_review(relation):
    """Whether relation roles still need assessment; not a damage verdict."""
    if is_reference_only(relation) or relation.action_status == "inactive":
        return False
    return (relation.effect_assessment.get("status") != "established"
            or relation.effect_assessment.get("replacement_role_review_required", False))


def strength_relation_needs_review(relation, day_element):
    if not requires_role_review(relation) or relation.type == "stem_control":
        return False
    if relation.type.startswith("branch_") and "combination" in relation.type:
        support = {day_element, next(e for e, child in _GENERATES.items() if child == day_element)}
        target = relation.transformation.target_element if relation.transformation else None
        # Both untransformed and target main elements remain on the same side.
        # This establishes no transformation and awards no extra force.
        if target in support and all(ZHI_WUXING.get(m.get("symbol")) in support for m in relation.members):
            return False
    return True


def _adjacent(relation):
    positions = [_ORDER.get(m.get("pillar")) for m in relation.members]
    return len(positions) == 2 and None not in positions and abs(positions[0] - positions[1]) == 1


def _judge(target, state, rule, facts, source):
    target.update(effect_status="established", function_state=state,
                  effect_rule=rule, effect_facts=facts, effect_source=source,
                  assessment_scope="natal_original_function", assessment_basis="adopted_model_rule",
                  actual_valence="undetermined", predictive_validated=False)


def assess_natal_functions(relations, pillars, roots):
    month = pillars.get("month")
    if not month:
        return []
    evidence = []
    clashed = {m["pillar"] for r in relations if r.type == "branch_clash" for m in r.members}
    for relation in relations:
        pair_context = None
        if any(m.get("pillar") not in _ORDER for m in relation.members):
            relation.effect_assessment = dict(status="unresolved", scope="outside_natal_rule_scope", policy=POLICY)
            continue
        transformation_basis = _transformation_basis(relation, pillars)
        if transformation_basis and transformation_basis["status"] == "absent":
            # Absence of branch assistance rules out conversion in this scope;
            # it says nothing about role binding or later luck-cycle support.
            relation.transformation.status = TransformationStatus.NOT_ESTABLISHED
            relation.transformation.reasons.append("원국 지지에 목표 오행과 이를 생하는 기반이 모두 관측되지 않음")
            transformation_evidence_id = f"evidence:transformation-basis:{relation.id}"
            relation.evidence_ids.append(transformation_evidence_id)
            evidence.append(Evidence(id=transformation_evidence_id, layer=EvidenceLayer.RULE,
                source_module=VERSION, rule_code=transformation_basis["absence_rule"],
                description="완전한 원국에서 합화 목표와 생조 기반의 부재를 확인",
                source_values=transformation_basis, supports=[relation.id], reliability=ConfidenceLevel.MEDIUM))
        if is_reference_only(relation):
            relation.effect_assessment = dict(status="observation_only", policy=POLICY, source=REN_SOURCE,
                reason="이 해석 계통에서 관계 이름만을 독립적인 손상·보류 근거로 쓰지 않음")
        elif relation.type == "branch_clash":
            affected = {m["pillar"] for m in relation.members}
            for target in relation.function_targets:
                if target.get("function_kind") != "root_support" or target["element"] == "土":
                    continue
                stem_roots = [r for r in roots.items if r.stem_pillar == target["stem_pillar"]]
                branches = [pillars[r.branch_pillar].branch for r in stem_roots if pillars.get(r.branch_pillar)]
                root = target["root_connection"]
                competing_root_combination = any(
                    r.type.startswith("branch_") and "combination" in r.type
                    and any(m["pillar"] == root["branch_pillar"] for m in r.members)
                    for r in relations
                )
                if (branches and all(b in _STORAGE for b in branches)
                        and root["branch_pillar"] in affected and not competing_root_combination):
                    _judge(target, "reduced", "ren-storage-only-root-clashed-v1",
                           {"original_root_branches": branches, "clashed_root": root,
                            "raw_root_retained": True, "root_erased": False}, REN_SOURCE)
        elif relation.type == "stem_combination":
            members = relation.members
            day = pillars.get("day")
            shared_context = shared_officer_context(relation, pillars)
            water_context = rooted_water_context(relation, pillars, roots, relations)
            release_context = metal_fire_release_context(relation, pillars, roots, relations)
            negative_context = water_context or release_context
            if negative_context:
                relation.transformation.status = TransformationStatus.NOT_ESTABLISHED
                relation.transformation.reasons.append("명시된 원국 기반·해소 조건에서 합화 불성립으로 판단")
                context_evidence_id = f"evidence:combination-context:{relation.id}"
                relation.evidence_ids.append(context_evidence_id)
                evidence.append(Evidence(id=context_evidence_id, layer=EvidenceLayer.RULE,
                    source_module=VERSION, rule_code=negative_context["rule"],
                    description="채택한 원국 예외 조건의 합화 불성립 판정",
                    source_values=negative_context, supports=[relation.id], reliability=ConfidenceLevel.MEDIUM))
            # 子平真詮評注 V distinguishes another identical yin day stem
            # sharing its officer from ordinary loss of both useful roles.
            shared_officer = bool(day and day.stem in "乙丁己辛癸"
                and any(m["symbol"] == day.stem for m in members)
                and not any(m["pillar"] == "day" for m in members))
            scoped_pair = (not any(m["pillar"] == "day" for m in members)
                           and not relation.competing_relationship_ids
                           and not shared_officer
                           and relation.action_status not in {"inactive", "blocked"})
            anchored = set()
            target_element = relation.transformation.target_element if relation.transformation else None
            for m in members:
                element = GAN_WUXING[m["symbol"]]
                if (scoped_pair and (m["pillar"] == "month" or element == target_element)
                        and "month" not in clashed
                        and month.branch in _VIGOROUS.get(element, set())
                        and any(r.stem_pillar == m["pillar"] and r.branch_pillar == "month" and r.element == element
                                for r in roots.items)):
                    anchored.add(m["pillar"])
            for target in relation.function_targets:
                if target["stem_pillar"] in anchored:
                    retention_rule = ("seasonal-vigorous-month-role-retained-v1" if target["stem_pillar"] == "month"
                                      else "seasonal-vigorous-native-target-role-retained-v1")
                    _judge(target, "retained", retention_rule,
                           {"month_branch": month.branch, "month_element": ZHI_WUXING[month.branch],
                            "month_root_clashed": False}, ZIPING_SOURCE)
            # Close non-day pairs take precedence only when no second close
            # partner competes. Distant-pair behavior is deliberately separate.
            keys = {m["pillar"] for m in members}
            contested_roots = [r.model_dump(mode="json") for r in roots.items
                               if r.stem_pillar in keys and r.branch_pillar in clashed]
            other_close = any(r.id != relation.id and r.type == "stem_combination" and _adjacent(r)
                              and keys & {m["pillar"] for m in r.members} for r in relations)
            transformation_context = target_element == ZHI_WUXING[month.branch]
            opposed_context = _opposed_original_context(relation, pillars, roots, clashed)
            pair_context = {"shared_yin_day_officer": shared_officer,
                            "shared_officer_assessment": shared_context,
                            "rooted_water_assessment": water_context,
                            "metal_fire_release_assessment": release_context,
                            "clashed_member_roots": contested_roots,
                            "other_adjacent_partner": other_close,
                            "month_aligned_target": transformation_context,
                            "opposed_original_context": opposed_context}
            if (scoped_pair and _adjacent(relation) and not anchored
                    and not contested_roots
                    and not other_close and (not transformation_context or opposed_context)):
                for target in relation.function_targets:
                    _judge(target, "reduced", ("adjacent-opposed-target-role-restricted-v1" if transformation_context
                                              else "adjacent-non-day-pair-role-restricted-v1"),
                           {"adjacent": True, "other_adjacent_partner": False,
                            "month_vigorous_retention_exception": False,
                            "opposed_original_context": opposed_context,
                            "transformation_verdict": (relation.transformation.status.value
                                                       if relation.transformation else "unresolved")}, ZIPING_SOURCE)
            if shared_context:
                for target in relation.function_targets:
                    if target["target_id"] == shared_context["target_id"]:
                        _judge(target, "retained", shared_context["rule"], shared_context, shared_context["source"])
                        target.update(role_direction=shared_context["role_direction"],
                                      effective_force="undetermined", retained_scope="original_role_identity_only")
            if release_context:
                for target in relation.function_targets:
                    if target["stem_pillar"] == release_context["metal_pillar"]:
                        _judge(target, "retained", release_context["rule"], release_context, release_context["source"])
                        target.update(effective_force="undetermined", retained_scope=release_context["scope"])
        judged = [t for t in relation.function_targets if t.get("effect_status") == "established"]
        if not is_reference_only(relation):
            relation.effect_assessment = dict(status=("established" if judged and len(judged) == len(relation.function_targets)
                                                     else "partial" if judged else "unresolved"),
                scope="natal_original_function", policy=POLICY,
                judged_target_ids=[t["target_id"] for t in judged],
                unresolved_target_ids=[t["target_id"] for t in relation.function_targets if t not in judged],
                actual_valence="undetermined", predictive_validated=False)
            if pair_context is not None:
                relation.effect_assessment["pair_context"] = pair_context
            if transformation_basis:
                relation.effect_assessment["transformation_basis"] = transformation_basis
                relation.effect_assessment["replacement_role_review_required"] = bool(
                    relation.transformation.status is not TransformationStatus.NOT_ESTABLISHED
                    and any(t.get("function_state") == "reduced" for t in judged))
        if judged or is_reference_only(relation):
            evidence_id = f"evidence:function-assessment:{relation.id}"
            relation.evidence_ids.append(evidence_id)
            for target in judged:
                target["effect_evidence_ids"] = [evidence_id]
            for member in relation.member_function_assessments:
                target = next((t for t in judged if t["stem_pillar"] == member["pillar"]), None)
                if target:
                    member.update(function_state=target["function_state"], effect_rule=target["effect_rule"],
                                  assessment_scope="natal_original_function", actual_valence="undetermined")
                    member["evidence_ids"].append(evidence_id)
                    member["reasons"].append("명시된 원국 역할 규칙의 조건을 충족함; 전체 길흉은 별도 판단")
            evidence.append(Evidence(id=evidence_id, layer=EvidenceLayer.RULE, source_module=VERSION,
                rule_code=POLICY, description="채택한 원국 해석 규칙의 역할 판정과 관찰 범위",
                source_values={"assessment": relation.effect_assessment, "judgments": judged},
                supports=[relation.id], reliability=ConfidenceLevel.MEDIUM))
    return evidence
