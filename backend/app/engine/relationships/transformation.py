"""Positive pair conversion and qualified day-master classification.

One staged decision: scope -> local support -> explicit exceptions -> retained
native support -> classification. Raw stems/roots and prescription gates stay
separate. These are bounded adopted-model rules, not predictive validation.
"""
from app.engine.constants import ZHI_WUXING
from app.engine.core.models import ConfidenceLevel, Evidence, EvidenceLayer, TransformationStatus
from app.engine.facts.hidden_stems import get_hidden_stems

VERSION = "natal-transformation-v1"
_ORDER = {"year": 0, "month": 1, "day": 2, "hour": 3}
_GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
_CONTROLS = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
_VIGOROUS = {"木": set("寅卯"), "火": set("巳午"), "金": set("申酉"), "水": set("亥子")}
_GROWTH = {"木": "亥", "火": "寅", "金": "巳", "水": "申"}
_PAIR_BRANCHES = {"木": set("亥寅卯"), "火": set("巳午"), "金": set("申酉")}
SOURCE = {
    "work": "子平真詮評注 / 滴天髓闡微",
    "attribution": "徐樂吾 평주의 천간합 범위와 任鐵樵의 化象·假化 맥락을 구분해 대조",
    "references": [
        {"section": "五、論十干合而不合 — 통근·승왕과 일간의 화기 구분",
         "url": "https://www.ncc.com.tw/fate/paleo/bg/bg_032.htm"},
        {"section": "六親論十三、化象; 十五、假化",
         "url": "https://zh.wikisource.org/zh-hant/滴天髓闡微"},
    ],
}


def _strong_roots(stem_pillar, roots, pillars):
    result = []
    for root in roots.items:
        if root.stem_pillar != stem_pillar:
            continue
        branch = pillars[root.branch_pillar].branch
        # Summer 巳 cannot certify a metal growth foundation by presence alone.
        if root.element == "金" and branch == "巳" and pillars['month'].branch in set("巳午未"):
            continue
        if branch in _VIGOROUS.get(root.element, set()) | {_GROWTH.get(root.element)}:
            result.append(root)
    return result


def _family(day, target):
    if day == target:
        return "peer"
    if _GENERATES[target] == day:
        return "resource"
    if _GENERATES[day] == target:
        return "output"
    if _CONTROLS[day] == target:
        return "wealth"
    return "officer"


def _decision(relation, pillars, roots, relations):
    if (relation.type != "stem_combination" or not relation.transformation
            or not all(pillars.get(k) for k in _ORDER)):
        return None
    keys = {m.get("pillar") for m in relation.members}
    if len(keys) != 2 or not keys <= set(_ORDER):
        return None
    positions = sorted(_ORDER[k] for k in keys)
    if positions[1] - positions[0] != 1:
        return None
    target = relation.transformation.target_element
    base = {"scope": "day_master_structure" if "day" in keys else "pair",
            "target_element": target, "source": SOURCE, "basis": "adopted_context_rule",
            "prescription_status": "unresolved", "actual_valence": "undetermined",
            "predictive_validated": False, "raw_facts_rewritten": False,
            "classification_status": "unresolved", "checks": {}}
    checks = base['checks']
    checks['prior_negative'] = relation.transformation.status is TransformationStatus.NOT_ESTABLISHED
    checks['competition'] = bool(relation.competing_relationship_ids) or relation.action_status in {'blocked', 'inactive', 'competing'}
    other_close = [r.id for r in relations if r.id != relation.id and r.type == 'stem_combination'
                   and len(r.members) == 2 and all(m.get('pillar') in _ORDER for m in r.members)
                   and abs(_ORDER[r.members[0]['pillar']] - _ORDER[r.members[1]['pillar']]) == 1
                   and keys & {m['pillar'] for m in r.members}]
    checks['other_adjacent_partner_ids'] = other_close
    # A competing local target carrier needs a distinct branch assessment.
    local_clashes = [r.id for r in relations if r.type == 'branch_clash'
                     and any(m['pillar'] in keys for m in r.members)
                     and not all(ZHI_WUXING.get(m['symbol']) == target for m in r.members)]
    checks['local_clash_ids'] = local_clashes
    if checks['prior_negative'] or checks['competition'] or other_close or local_clashes:
        return base
    month_branch = pillars['month'].branch
    native_element = pillars['day'].stem_element
    if base['scope'] == 'pair':
        checks['target_in_vigorous_month'] = month_branch in _VIGOROUS.get(target, set())
        checks['both_local_branches_support_target'] = all(
            pillars[k].branch in _PAIR_BRANCHES.get(target, set()) for k in keys)
        outside_controllers = [r.model_dump(mode='json') for k, p in pillars.items()
                               if p and k not in keys and _CONTROLS[p.stem_element] == target
                               for r in _strong_roots(k, roots, pillars)]
        checks['rooted_outside_controllers'] = outside_controllers
        if (checks['target_in_vigorous_month'] and checks['both_local_branches_support_target']
                and not outside_controllers):
            base.update(classification_status='established', kind='pair',
                        rule='adjacent-season-supported-pair-conversion-v1',
                        role_family_to_day=_family(native_element, target))
        return base

    # Whole-chart classification is never inferred from a pair excluding day.
    # These source-backed profiles cover wood/earth day-master conversion.
    # In particular, earth's native root force is not resolved by _strong_roots;
    # extending this to 戊癸 day-master fire conversion would overstate certainty.
    checks['supported_day_target_profile'] = target in {'木', '土'}
    if not checks['supported_day_target_profile']:
        return base
    month_aligned = ZHI_WUXING[month_branch] == target
    target_visible = [k for k, p in pillars.items() if p and p.stem_element == target
                      and any(r.stem_pillar == k for r in roots.items)]
    partner = next(k for k in keys if k != 'day')
    generating = next(e for e, child in _GENERATES.items() if child == target)
    partner_main = get_hidden_stems(pillars[partner].branch).stems[0].element
    checks.update(month_target_aligned=month_aligned, rooted_target_visible_pillars=target_visible,
                  partner_main_element=partner_main)
    if not month_aligned or not target_visible or partner_main not in {target, generating}:
        return base

    original_roots = _strong_roots('day', roots, pillars)
    resource = next(e for e, child in _GENERATES.items() if child == native_element)
    direct_resource_seat = ZHI_WUXING[pillars['day'].branch] == resource
    resource_support = [r for k, p in pillars.items() if p and k not in keys and p.stem_element == resource
                        for r in _strong_roots(k, roots, pillars)]
    outside_peers = [k for k, p in pillars.items() if p and k not in keys and p.stem_element == native_element]
    # A peer with its own separate adjacent partner is not a rival by count alone.
    separately_paired_peers = [k for k in outside_peers if any(
        r.type == 'stem_combination' and r.id != relation.id
        and len(r.members) == 2 and all(m.get('pillar') in _ORDER for m in r.members)
        and k in {m['pillar'] for m in r.members}
        and not keys & {m['pillar'] for m in r.members}
        and abs(_ORDER[r.members[0]['pillar']] - _ORDER[r.members[1]['pillar']]) == 1
        for r in relations)]
    # A feeding element between a rooted peer and the target is observed, not
    # scored as a verified mediation remedy.
    unpaired_peers = set(outside_peers) - set(separately_paired_peers)
    feeding_visible = [k for k, p in pillars.items() if p and p.stem_element == generating
                       and any(r.stem_pillar == k for r in roots.items)]
    strong_controllers = [r for k, p in pillars.items() if p and k not in keys
                          and _CONTROLS[p.stem_element] == target
                          for r in _strong_roots(k, roots, pillars)]
    checks.update(original_strong_roots=[r.model_dump(mode='json') for r in original_roots],
                  direct_resource_seat=direct_resource_seat,
                  original_resource_strong_roots=[r.model_dump(mode='json') for r in resource_support],
                  outside_peer_pillars=outside_peers, separately_paired_peer_pillars=separately_paired_peers,
                  rooted_feeding_visible_pillars=feeding_visible,
                  rooted_target_controllers=[r.model_dump(mode='json') for r in strong_controllers])
    if unpaired_peers and not feeding_visible:
        return base
    # A strong outside controller can indicate opposition rather than fake
    # conversion. Do not label every breaker as fake.
    if strong_controllers and not original_roots:
        return base
    if original_roots or direct_resource_seat or resource_support:
        # 附根/坐印 subtype only; off-season/weak-target fake types remain open.
        base.update(classification_status='established', kind='fake',
                    rule='season-supported-day-conversion-with-native-support-v1')
    elif not outside_peers and not strong_controllers:
        base.update(classification_status='established', kind='true',
                    rule='season-supported-day-conversion-without-strong-native-support-v1')
    return base


def assess_transformations(relations, pillars, roots):
    evidence = []
    for relation in relations:
        assessment = _decision(relation, pillars, roots, relations)
        if assessment is None:
            continue
        relation.transformation.assessment = assessment
        relation.transformation.scope = assessment['scope']
        if assessment['classification_status'] != 'established':
            continue
        kind = assessment['kind']
        relation.transformation.kind = kind
        relation.transformation.scope = assessment['scope']
        # Fake identifies a qualified structure; it is not unqualified true conversion.
        relation.transformation.status = (TransformationStatus.CONDITIONAL if kind == 'fake'
                                          else TransformationStatus.ESTABLISHED)
        relation.transformation.reasons.append('공통 성립 조건과 원래 기반을 대조해 적용 범위 내 종류를 판정함')
        eid = f'evidence:transformation-classification:{relation.id}'
        relation.evidence_ids.append(eid)
        relation.effect_assessment['replacement_role_review_required'] = True
        relation.effect_assessment['transformation_classification'] = {
            'kind': kind, 'scope': assessment['scope'], 'classification_status': 'established',
            'prescription_status': 'unresolved', 'evidence_ids': [eid]}
        # Preserve original roles as observations and attach the changed role
        # family instead of silently editing raw elements or doubling force.
        if kind == 'pair':
            relation.effect_assessment['replacement_role'] = {
                'element': assessment['target_element'], 'family_to_day': assessment['role_family_to_day'],
                'effective_force': 'undetermined', 'assessment_status': 'role_identified',
                'count_as_extra_element': False, 'evidence_ids': [eid]}
        evidence.append(Evidence(id=eid, layer=EvidenceLayer.RULE, source_module=VERSION,
            rule_code=assessment['rule'], description='범위를 구분한 합화·진화·가화 종류 판정',
            source_values=assessment, supports=[relation.id], reliability=ConfidenceLevel.MEDIUM))
    return evidence
