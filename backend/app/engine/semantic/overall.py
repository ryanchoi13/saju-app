"""Shared, scoped life-domain interpretation for all overall fortune surfaces.

Ranks the support for an editorial subject, NOT the likelihood/size of an event.
Facts and completed core operations are preserved. No random rotation, domain
quota, sex-based spouse assignment, or summation of correlated observations.
The rule contract and source limits live in docs/overall-interpretation-policy.md.
"""
from copy import deepcopy

from app.engine.core.models import PillarFact, TimingResult
from app.engine.facts.hidden_stems import get_hidden_stems
from app.engine.facts.relationship_candidates import calculate_relationship_candidates
from app.engine.facts.ten_gods import get_ten_god
from app.engine.synthesis.operation_scope import usable_operations
from app.engine.timing.conditions import assess_temporal_conditions

OVERALL_VERSION = "overall-life-domains-v1"
DOMAINS = {
    "love": "애정·가까운 관계", "relationships": "대인관계",
    "wellbeing": "건강·생활 리듬", "money": "재물운",
    "work": "직장·사업운", "learning": "학업·배움",
    "enjoyment": "취미·일상의 즐거움", "self": "마음·자기 기준",
    "change": "이동·생활 변화",
}
GOD_DOMAIN = {
    "day_master": "self", "peer": "self", "rob_wealth": "relationships",
    "eating_god": "enjoyment", "hurting_officer": "relationships",
    "direct_wealth": "money", "indirect_wealth": "money",
    "direct_officer": "work", "seven_killings": "work",
    "direct_resource": "learning", "indirect_resource": "learning",
}
AXES = ("luck_cycle", "annual", "monthly", "daily")
JOIN = {"stem_combination", "branch_six_combination", "branch_three_combination",
        "branch_directional_combination"}
SCENE_RELATIONS = JOIN | {"branch_clash"}
RECOVERY = {"support", "moisten", "cool", "stabilize", "warm"}
RECOVERY_GODS = {"direct_resource", "indirect_resource", "seven_killings"}


def _keys(members):
    return tuple(sorted((m.get("pillar"), m.get("position"), m.get("symbol")) for m in members))


def select_overall_domains(core, scope, *, timing=None, cycle=None):
    """Return all reviewed domains, selected subjects, and their exact provenance.

    scope is natal/daily/monthly/annual/luck_cycle. A lower time layer cannot
    affect an upper layer. Reassess structural conditions within that scope.
    """
    if scope not in {"natal", *AXES}:
        raise ValueError("Unknown overall interpretation scope")
    source_timing = timing or core.timing
    synthesis = core.synthesis.model_dump(mode="json")
    natal = {k: v for k, v in core.natal_facts.pillars.items() if v is not None}
    master = natal["day"].stem
    overlays = {}
    if scope != "natal":
        for axis in AXES[:AXES.index(scope) + 1]:
            value = (cycle if cycle is not None else source_timing.luck_cycle.get("current")) if axis == "luck_cycle" else getattr(source_timing, axis)
            if value and value.get("pillar"):
                overlays[axis] = deepcopy(value)
    focal = overlays.get(scope, {})
    focal_god = focal.get("ten_god")
    focal_branch = focal.get("pillar", {}).get("branch")
    branch_god = get_ten_god(master, get_hidden_stems(focal_branch).stems[0].stem).value if focal_branch else None
    background_domains = {GOD_DOMAIN.get(v.get("ten_god")) for k, v in overlays.items() if k != scope}
    focal_domains = {GOD_DOMAIN.get(g) for g in (focal_god, branch_god)} - {None}
    combined = dict(natal)
    combined.update({"timing:" + a: PillarFact.model_validate(v["pillar"]) for a, v in overlays.items()})
    facts = calculate_relationship_candidates(combined).items
    changes = [dict(relationship_id=r.id, type=r.type.value, target_element=r.target_element,
                    members=[m.model_dump(mode="json") for m in r.members],
                    status="candidate", requires_reassessment=True)
               for r in facts if any(m.pillar.startswith("timing:") for m in r.members)]
    scoped_timing = TimingResult(luck_cycle={"current": overlays.get("luck_cycle")},
        annual=overlays.get("annual", {}), monthly=overlays.get("monthly", {}),
        daily=overlays.get("daily", {}), relationship_changes=changes)
    conditions, condition_evidence = assess_temporal_conditions(natal, scoped_timing, core.synthesis) if overlays else ({"records": []}, [])
    checked = {r["relationship_id"]: r for r in conditions["records"]}
    natal_results = {r.id: r.model_dump(mode="json") for r in core.relationships}
    evidence = {e.id: e.model_dump(mode="json") for e in core.evidence}
    evidence.update({e.id: e.model_dump(mode="json") for e in condition_evidence})
    candidates = {}

    def add(domain, origin, sources, *, level=1, specificity=0, urgency=0,
            mode="base", members=(), god=None):
        if domain not in DOMAINS:
            return
        item = candidates.setdefault(domain, dict(domain=domain, label=DOMAINS[domain], supports=[]))
        source_ids = sorted(set(sources))
        support = dict(origin=origin, source_ids=source_ids, level=level,
            specificity=specificity, urgency=urgency, mode=mode,
            members=list(members), ten_god=god)
        if not any(s["origin"] == origin and s["source_ids"] == source_ids for s in item["supports"]):
            item["supports"].append(support)

    # A single ten-god offers a low-level symbolic reading, never an event claim.
    if focal_god:
        add(GOD_DOMAIN.get(focal_god), "period:visible-role", ["period:" + scope], specificity=1, god=focal_god)
        evidence["period:" + scope] = dict(id="period:" + scope, scope=scope, pillar=focal.get("pillar"),
            ten_god=focal_god, branch_main_ten_god=branch_god, kind="calculated_period_fact")
        if branch_god and GOD_DOMAIN.get(branch_god) != GOD_DOMAIN.get(focal_god):
            branch_id = "period:" + scope + ":branch"
            evidence[branch_id] = dict(id=branch_id, parent="period:" + scope,
                scope=scope, branch=focal_branch, main_hidden_ten_god=branch_god,
                kind="calculated_period_branch_fact")
            add(GOD_DOMAIN.get(branch_god), "period:branch-role", [branch_id], god=branch_god)
    elif scope == "natal":
        structure = synthesis.get("overall_structure", {}).get("ordinary")
        diag = core.diagnostics.get("structure")
        if structure and diag and diag.confidence.value != "undetermined":
            add(GOD_DOMAIN.get(structure), "natal:structure", diag.evidence_ids, specificity=1, god=structure)

    for relation in facts:
        kind = relation.type.value
        if kind not in SCENE_RELATIONS:
            continue
        members = [m.model_dump(mode="json") for m in relation.members]
        natal_members = [m for m in members if m["pillar"] in natal]
        if not natal_members:
            continue  # Timing-only links never identify a person's life subject.
        if scope == "natal":
            if any(m["pillar"].startswith("timing:") for m in members):
                continue
            reviewed = natal_results.get(relation.id, {})
            if reviewed.get("action_status") in {"blocked", "unsupported", "not_applicable"}:
                continue
            source_ids = reviewed.get("evidence_ids", [])
            if not source_ids:
                continue
        else:
            if not any(m["pillar"] == "timing:" + scope for m in members):
                continue
            reviewed = checked.get(relation.id, {})
            if (reviewed.get("eligibility") != "conditional" or not reviewed.get("checklist_evaluated")
                    or _keys(reviewed.get("members", [])) != _keys(members)):
                continue
            source_ids = reviewed.get("evidence_ids", [])
        mode = "join" if kind in JOIN else "change"
        # Reuse the existing love service's day-branch context as a CONDITIONAL
        # close-relationship subject. No marriage/sex/partner mind is inferred.
        touches_day_branch = any(m["pillar"] == "day" and m["position"] == "branch" for m in members)
        if touches_day_branch and len(members) == 2:
            add("love", "relationship:day-branch", source_ids, level=2, specificity=2,
                mode=mode, members=members)
        for member in natal_members:
            # The day branch already supplies the closer relationship context.
            if touches_day_branch and len(members) == 2 and member["pillar"] == "day" and member["position"] == "branch":
                continue
            stem = member["symbol"] if member["position"] == "visible_stem" else get_hidden_stems(member["symbol"]).stems[0].stem
            god = get_ten_god(master, stem).value
            add(GOD_DOMAIN.get(god), "relationship:natal-role", source_ids, level=2,
                specificity=1, mode=mode, members=members, god=god)
        # Preserve the core's affected-root/visible-role tracing. A target is
        # another interpretation of this SAME relation, never another vote.
        function_targets = reviewed.get("checks", {}).get("function_targets", []) if scope != "natal" else reviewed.get("function_targets", [])
        for target in function_targets:
            if (target.get("stem_pillar") in natal
                    and target.get("function_kind") in {"root_support", "visible_role"}):
                god = target.get("role_to_day_master")
                add(GOD_DOMAIN.get(god), "relationship:natal-function", source_ids,
                    level=2, specificity=1, mode=mode, members=members, god=god)
        # A clash supplies a conditional plan-change topic, not proof of a move.
        if kind == "branch_clash" and not touches_day_branch:
            add("change", "relationship:change", source_ids, level=2,
                specificity=1, mode=mode, members=members)

    # Wellbeing is a lifestyle reading. Only usable personal operations may
    # raise its priority; raw seasonal imbalance cannot become a health alert.
    recovery_context = focal_god in RECOVERY_GODS or branch_god in RECOVERY_GODS
    operations = usable_operations(synthesis)
    for operation in operations:
        op = operation.get("operation")
        if not operation.get("evidence_ids"):
            continue
        if op in RECOVERY and (scope == "natal" or recovery_context):
            add("wellbeing", "core:recovery", operation["evidence_ids"], level=3,
                specificity=1, urgency=1 if operation.get("urgency") == "high" else 0,
                mode="recovery")
        if op in {"mediate", "resolve_conflict"} and (scope == "natal" or "relationships" in focal_domains):
            add("relationships", "core:communication", operation["evidence_ids"], level=3,
                specificity=1, urgency=1 if operation.get("urgency") == "high" else 0)
    # Two roles of the SAME period remain ONE contextual observation.
    # This supports rest/pace advice without claiming sickness or energy levels.
    if focal_god and branch_god and ({focal_god, branch_god} & {"direct_resource", "indirect_resource"}) and ({focal_god, branch_god} & {"seven_killings", "direct_officer"}):
        add("wellbeing", "period:recovery-and-responsibility", ["period:" + scope],
            specificity=2, mode="recovery")

    ranked = []
    for domain, item in candidates.items():
        # MAX, not sum: duplicate rules/roles/time layers cannot manufacture force.
        def rank(s):
            return (s["level"], s["urgency"], s["specificity"],
                    int(domain in focal_domains), int(domain in background_domains))
        best = max(item["supports"], key=rank)
        item["priority"] = list(rank(best))
        item["source_ids"] = sorted({e for s in item["supports"] for e in s["source_ids"]})
        best_modes = {s["mode"] for s in item["supports"] if rank(s) == rank(best)}
        item["mode"] = "mixed" if {"join", "change"} <= best_modes else best["mode"]
        item["interpretation_level"] = "editorial_life_subject"
        item["event_likelihood"] = None
        ranked.append(item)
    ranked.sort(key=lambda c: (tuple(-p for p in c["priority"]), c["domain"]))
    primary = [c for c in ranked if c["priority"] == ranked[0]["priority"]] if ranked else []
    selected = list(primary)
    covered = {s for c in selected for s in c["source_ids"]}
    for item in ranked:
        if item in primary:
            continue
        # Keep another meaningful subject when it has distinct support. Do not
        # narrate the same relation again as money, work and love independently.
        independent = set(item["source_ids"]) - covered
        if independent and (item["priority"][0] >= 2 or any(s.startswith("period:" + scope) for s in independent)):
            selected.append(item)
            covered.update(item["source_ids"])
    considered = [dict(domain=d, label=label, status="supported" if d in candidates else "no_specific_support")
                  for d, label in DOMAINS.items()]
    return dict(version=OVERALL_VERSION, scope=scope, primary_domains=[c["domain"] for c in primary],
        selected=selected, candidates=ranked, considered_domains=considered,
        evidence_records=[evidence[e] for e in sorted({s for c in ranked for s in c["source_ids"]}) if e in evidence],
        policy=dict(priority_order=["support_level", "assessed_core_urgency", "subject_specificity",
                    "focal_period_context", "longer_context"],
                    ranking_is_editorial=True, event_importance_estimated=False,
                    ties_preserved=True, repeated_evidence_summed=False,
                    random_rotation=False, domain_quota=False, medical_prediction=False),
        focal_god=focal_god, focal_branch_god=branch_god)
