"""Daeyun, annual, monthly, and daily overlays without fixed weights."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date

from lunar_python import Solar

from app.engine.calendar import solar_from_parts, to_solar
from app.engine.constants import GAN_WUXING, ZHI_WUXING
from app.engine.core.models import (
    ActivatedState,
    BirthInput,
    ConfidenceLevel,
    Evidence,
    EvidenceLayer,
    PillarFact,
    TimingResult,
)
from app.engine.facts.relationship_candidates import calculate_relationship_candidates
from app.engine.facts.ten_gods import get_ten_god


TIMING_ENGINE_VERSION = "timing-overlay-v1"
DAEYUN_CONVENTION_VERSION = "lunar-python-sect1-v1"
_YANG_STEMS = frozenset("甲丙戊庚壬")
_YANG_BRANCHES = frozenset("子寅辰午申戌")
_SUPPORTING_GODS = {"peer", "rob_wealth", "direct_resource", "indirect_resource"}
_DRAINING_GODS = {
    "eating_god", "hurting_officer", "direct_wealth", "indirect_wealth",
    "direct_officer", "seven_killings",
}


def _pillar(ganji: str) -> PillarFact:
    stem, branch = ganji[0], ganji[1]
    return PillarFact(
        stem=stem,
        branch=branch,
        ganji=ganji,
        stem_element=GAN_WUXING[stem],
        stem_yin_yang="yang" if stem in _YANG_STEMS else "yin",
        branch_element=ZHI_WUXING[branch],
        branch_yin_yang="yang" if branch in _YANG_BRANCHES else "yin",
    )


def _axis(name: str, ganji: str, day_master: str, **extra) -> dict:
    pillar = _pillar(ganji)
    return {
        "axis": name,
        "pillar": pillar.model_dump(mode="json"),
        "ten_god": get_ten_god(day_master, pillar.stem).value,
        **extra,
    }


def _relationship_changes(
    natal_pillars: Mapping[str, PillarFact | None],
    overlays: Mapping[str, PillarFact],
) -> list[dict]:
    combined = dict(natal_pillars)
    combined.update({f"timing:{name}": pillar for name, pillar in overlays.items()})
    candidates = calculate_relationship_candidates(combined)
    changes = []
    for candidate in candidates.items:
        timing_members = [
            item for item in candidate.members if item.pillar.startswith("timing:")
        ]
        if not timing_members:
            continue
        changes.append({
            "relationship_id": candidate.id,
            "type": candidate.type.value,
            "members": [item.model_dump(mode="json") for item in candidate.members],
            "target_element": candidate.target_element,
            "status": "candidate",
            "requires_reassessment": True,
        })
    return changes


def calculate_timing(
    birth: BirthInput,
    natal_pillars: Mapping[str, PillarFact | None],
    *,
    target_date: date | None = None,
    daeyun_count: int = 10,
) -> tuple[TimingResult, ActivatedState, list[Evidence]]:
    """Calculate ordered time overlays while preserving each layer separately."""

    target = target_date or date.today()
    solar_birth = to_solar(birth.birth_date, birth.calendar_type, birth.is_leap_month)
    if target < solar_birth:
        raise ValueError("target_date는 출생일보다 빠를 수 없습니다.")
    hour = 12 if birth.time_unknown or birth.birth_time is None else birth.birth_time.hour
    minute = 0 if birth.time_unknown or birth.birth_time is None else birth.birth_time.minute
    natal_lunar = solar_from_parts(
        solar_birth.year, solar_birth.month, solar_birth.day, hour, minute
    ).getLunar()
    eight_char = natal_lunar.getEightChar()
    eight_char.setSect(1)
    gender_code = 1 if birth.gender == "male" else 0
    yun = eight_char.getYun(gender_code)
    forward = (eight_char.getYearGan() in _YANG_STEMS) == (birth.gender == "male")

    cycles = []
    current_cycle = None
    for cycle in yun.getDaYun(daeyun_count + 1):
        if cycle.getIndex() == 0 or not cycle.getGanZhi():
            continue
        item = _axis(
            "luck_cycle",
            cycle.getGanZhi(),
            eight_char.getDayGan(),
            index=cycle.getIndex(),
            start_year=cycle.getStartYear(),
            end_year=cycle.getEndYear(),
            start_age=cycle.getStartAge(),
            end_age=cycle.getEndAge(),
        )
        cycles.append(item)
        if cycle.getStartYear() <= target.year <= cycle.getEndYear():
            current_cycle = item

    target_lunar = Solar.fromYmdHms(
        target.year, target.month, target.day, 12, 0, 0
    ).getLunar()
    annual = _axis(
        "annual", target_lunar.getYearInGanZhiExact(), eight_char.getDayGan(),
        year=target.year,
    )
    monthly = _axis(
        "monthly", target_lunar.getMonthInGanZhiExact(), eight_char.getDayGan(),
        year=target.year, month=target.month,
    )
    daily = _axis(
        "daily", target_lunar.getDayInGanZhiExact(), eight_char.getDayGan(),
        date=target.isoformat(),
    )

    overlay_items = [item for item in (current_cycle, annual, monthly, daily) if item]
    overlay_pillars = {
        item["axis"]: PillarFact.model_validate(item["pillar"]) for item in overlay_items
    }
    relationship_changes = _relationship_changes(natal_pillars, overlay_pillars)
    activated_gods = list(dict.fromkeys(item["ten_god"] for item in overlay_items))
    god_set = set(activated_gods)
    if god_set and god_set <= _SUPPORTING_GODS:
        strength_shift = "supportive"
    elif god_set and god_set <= _DRAINING_GODS:
        strength_shift = "draining_or_pressuring"
    elif god_set:
        strength_shift = "mixed"
    else:
        strength_shift = None

    evidence_id = "evidence:timing:ordered-overlays"
    evidence = Evidence(
        id=evidence_id,
        layer=EvidenceLayer.TIMING,
        source_module=TIMING_ENGINE_VERSION,
        rule_code=DAEYUN_CONVENTION_VERSION,
        description="원국 위에 대운·세운·월운·일진을 순서대로 보존한 시간축 계산",
        source_values={
            "solar_birth_date": solar_birth.isoformat(),
            "target_date": target.isoformat(),
            "forward": forward,
            "yun_start": {
                "years": yun.getStartYear(),
                "months": yun.getStartMonth(),
                "days": yun.getStartDay(),
                "hours": yun.getStartHour(),
                "solar_date": yun.getStartSolar().toYmd(),
            },
            "fixed_weight_used": False,
        },
        supports=["timing:current-overlays"],
        reliability=ConfidenceLevel.MEDIUM,
    )
    timing = TimingResult(
        luck_cycle={
            "direction": "forward" if forward else "reverse",
            "convention": DAEYUN_CONVENTION_VERSION,
            "start": evidence.source_values["yun_start"],
            "cycles": cycles,
            "current": current_cycle,
        },
        annual=annual,
        monthly=monthly,
        daily=daily,
        relationship_changes=relationship_changes,
        evidence_ids=[evidence_id],
    )
    activated = ActivatedState(
        activated_ten_gods=activated_gods,
        strength_shift=strength_shift,
        relationship_changes=relationship_changes,
        climate_shift={
            "annual_element": annual["pillar"]["stem_element"],
            "monthly_element": monthly["pillar"]["stem_element"],
            "daily_element": daily["pillar"]["stem_element"],
            "requires_reassessment": True,
        },
        structure_changes=[{
            "status": "requires_reassessment",
            "reason": "시간축 관계 후보를 반영해 구조와 합화를 다시 평가해야 함",
        }] if relationship_changes else [],
        caution_operations=[{
            "operation": "rerun_relationship_and_diagnostics",
            "required": True,
        }],
    )
    return timing, activated, [evidence]
