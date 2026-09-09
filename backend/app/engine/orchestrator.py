"""End-to-end, evidence-preserving orchestrator for Myeongri core v1."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, time

from app.engine.calendar import solar_from_parts, to_solar
from app.engine.constants import GAN_WUXING, ZHI_WUXING
from app.engine.core.models import (
    BirthInput,
    ConfidenceLevel,
    DayMasterFact,
    MyeongriCoreResult,
    NatalFacts,
    PillarFact,
    UncertaintyResult,
)
from app.engine.diagnostics import (
    diagnose_climate,
    diagnose_mediation,
    diagnose_pathology,
    diagnose_special_structure,
    diagnose_strength,
    diagnose_structure,
)
from app.engine.facts import (
    calculate_element_inventory,
    calculate_exposed_stems,
    calculate_hidden_stems,
    calculate_relationship_candidates,
    calculate_roots,
    calculate_ten_gods,
    calculate_twelve_stages,
)
from app.engine.relationships import resolve_relationships
from app.engine.semantic import build_semantic_state
from app.engine.shensha import calculate_shensha
from app.engine.synthesis import synthesize_diagnostics
from app.engine.timing import calculate_timing
from app.engine.timing.conditions import assess_temporal_conditions
from app.engine.timing.direction import compare_temporal_directions


CORE_ENGINE_VERSION = "myeongri-core-v1"
UNKNOWN_TIME_CONVENTION = "12-branch-midpoint-scenarios-v1"
_YANG_STEMS = frozenset("甲丙戊庚壬")
_YANG_BRANCHES = frozenset("子寅辰午申戌")
_SCENARIO_HOURS = tuple(range(0, 24, 2))


def _pillar(stem: str, branch: str) -> PillarFact:
    return PillarFact(
        stem=stem,
        branch=branch,
        ganji=stem + branch,
        stem_element=GAN_WUXING[stem],
        stem_yin_yang="yang" if stem in _YANG_STEMS else "yin",
        branch_element=ZHI_WUXING[branch],
        branch_yin_yang="yang" if branch in _YANG_BRANCHES else "yin",
    )


def _calculate_natal(birth: BirthInput, clock: time | None) -> tuple[NatalFacts, list, dict, object, list]:
    solar_date = to_solar(birth.birth_date, birth.calendar_type, birth.is_leap_month)
    hour = clock.hour if clock else 12
    minute = clock.minute if clock else 0
    lunar = solar_from_parts(
        solar_date.year, solar_date.month, solar_date.day, hour, minute
    ).getLunar()
    eight = lunar.getEightChar()
    eight.setSect(1)
    pillars = {
        "year": _pillar(eight.getYearGan(), eight.getYearZhi()),
        "month": _pillar(eight.getMonthGan(), eight.getMonthZhi()),
        "day": _pillar(eight.getDayGan(), eight.getDayZhi()),
        "hour": (
            _pillar(eight.getTimeGan(), eight.getTimeZhi()) if clock is not None else None
        ),
    }
    day_master = pillars["day"].stem
    hidden = calculate_hidden_stems(pillars)
    ten_gods = calculate_ten_gods(day_master, pillars, hidden)
    roots = calculate_roots(pillars, hidden)
    exposed = calculate_exposed_stems(pillars, hidden)
    inventory = calculate_element_inventory(pillars, hidden)
    stages = calculate_twelve_stages(day_master, pillars)
    candidates = calculate_relationship_candidates(pillars)
    relationships, relationship_evidence = resolve_relationships(
        candidates, pillars, roots, exposed
    )

    structure, structure_evidence = diagnose_structure(
        pillars, hidden, ten_gods, exposed, roots, relationships
    )
    strength, strength_evidence = diagnose_strength(
        day_master, pillars, roots, ten_gods, relationships
    )
    climate, climate_evidence = diagnose_climate(
        pillars, inventory, roots, relationships
    )
    pathology, pathology_evidence = diagnose_pathology(
        structure, strength, climate, relationships
    )
    mediation, mediation_evidence = diagnose_mediation(
        day_master, inventory, roots, relationships, strength, climate
    )
    special, special_evidence = diagnose_special_structure(
        day_master, pillars, inventory, roots, ten_gods, relationships, strength
    )
    diagnostics = {
        "structure": structure,
        "strength": strength,
        "climate": climate,
        "pathology": pathology,
        "mediation": mediation,
        "special_structure": special,
    }
    synthesis, synthesis_evidence = synthesize_diagnostics(diagnostics)
    facts = NatalFacts(
        calendar={
            "solar_date": solar_date.isoformat(),
            "lunar_text": lunar.toString(),
            "sect": 1,
            "time_used": clock.isoformat(timespec="minutes") if clock else None,
        },
        pillars=pillars,
        day_master=DayMasterFact(
            stem=day_master,
            element=GAN_WUXING[day_master],
            yin_yang="yang" if day_master in _YANG_STEMS else "yin",
        ),
        hidden_stems=hidden,
        ten_gods=ten_gods,
        roots=roots,
        exposed_stems=exposed,
        element_inventory=inventory,
        twelve_stages=stages,
        relationship_candidates=candidates,
        calculation_meta={
            "engine_version": CORE_ENGINE_VERSION,
            "fixed_score_used": False,
            "hour_pillar_included": clock is not None,
        },
    )
    evidence = (
        relationship_evidence
        + structure_evidence
        + strength_evidence
        + climate_evidence
        + pathology_evidence
        + mediation_evidence
        + special_evidence
        + synthesis_evidence
    )
    return facts, relationships, diagnostics, synthesis, evidence


def _scenario_signature(core: dict) -> dict[str, str]:
    diagnostics = core["diagnostics"]
    current = core["timing"].luck_cycle.get("current") or {}
    current_pillar = current.get("pillar", {}) if isinstance(current, dict) else {}
    return {
        "ordinary_structure": str(core["synthesis"].overall_structure.get("ordinary")),
        "special_structure": str(core["synthesis"].overall_structure.get("special")),
        "strength": str(core["synthesis"].strength_state),
        "climate": str(core["synthesis"].climate_state.get("state")),
        "pathology": str(diagnostics["pathology"].conclusion),
        "mediation": str(diagnostics["mediation"].conclusion),
        "current_luck_cycle": str(current_pillar.get("ganji")),
        "shensha": ",".join(sorted(item.name for item in core["shensha"])),
    }


def _unknown_time_scenarios(
    birth: BirthInput,
    target_date: date | None,
) -> UncertaintyResult:
    values: dict[str, list[dict]] = defaultdict(list)
    for hour in _SCENARIO_HOURS:
        clock = time(hour, 0)
        scenario_birth = birth.model_copy(update={
            "birth_time": clock,
            "time_unknown": False,
        })
        facts, _, diagnostics, synthesis, _ = _calculate_natal(scenario_birth, clock)
        timing, _, _ = calculate_timing(
            scenario_birth, facts.pillars, target_date=target_date
        )
        shensha, _ = calculate_shensha(facts.pillars, timing)
        signature = _scenario_signature({
            "diagnostics": diagnostics,
            "synthesis": synthesis,
            "timing": timing,
            "shensha": shensha,
        })
        branch = facts.pillars["hour"].branch
        for topic, value in signature.items():
            values[topic].append({"hour_branch": branch, "value": value})

    stable = []
    conditional = []
    for topic, observations in values.items():
        distinct = sorted({item["value"] for item in observations})
        if len(distinct) == 1:
            stable.append({"topic": topic, "value": distinct[0], "scenario_count": 12})
        else:
            conditional.append({
                "topic": topic,
                "possible_values": distinct,
                "by_hour_branch": observations,
            })
    return UncertaintyResult(
        time_unknown=True,
        scenario_count=12,
        stable_conclusions=stable,
        conditional_conclusions=conditional,
        sensitive_topics=[item["topic"] for item in conditional],
    )


def calculate_myeongri_core(
    birth: BirthInput,
    *,
    target_date: date | None = None,
) -> MyeongriCoreResult:
    """Run core v1 without changing the legacy DALHA API or content generator."""

    known_clock = None if birth.time_unknown else birth.birth_time
    if not birth.time_unknown and known_clock is None:
        raise ValueError("출생시간이 없으면 time_unknown=true로 지정해야 합니다.")
    facts, relationships, diagnostics, synthesis, evidence = _calculate_natal(
        birth, known_clock
    )
    timing, activated, timing_evidence = calculate_timing(
        birth, facts.pillars, target_date=target_date
    )
    conditions, condition_evidence = assess_temporal_conditions(facts.pillars, timing, synthesis)
    activated.temporal_conditions = conditions
    direction, direction_evidence = compare_temporal_directions(conditions, synthesis)
    activated.temporal_direction = direction
    timing_evidence += condition_evidence + direction_evidence
    shensha, shensha_evidence = calculate_shensha(facts.pillars, timing)
    semantic, semantic_evidence = build_semantic_state(
        synthesis, activated, relationships, shensha
    )
    if birth.time_unknown:
        uncertainty = _unknown_time_scenarios(birth, target_date)
        warnings = [
            "출생시간 미상: 12개 시지 대표 시나리오의 공통·조건부 결론을 분리함",
            "대표 시각은 각 시지의 중간값이며 대운 시작 시점은 조건부로 취급해야 함",
        ]
    else:
        uncertainty = UncertaintyResult(time_unknown=False, scenario_count=1)
        warnings = []
    return MyeongriCoreResult(
        input=birth,
        natal_facts=facts,
        relationships=relationships,
        diagnostics=diagnostics,
        synthesis=synthesis,
        timing=timing,
        activated_state=activated,
        shensha=shensha,
        semantic_state=semantic,
        uncertainty=uncertainty,
        evidence=evidence + timing_evidence + shensha_evidence + semantic_evidence,
        warnings=warnings,
    )
