"""Detect the five approved shensha without treating them as core judgments."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.engine.core.models import (
    ConfidenceLevel,
    Evidence,
    EvidenceLayer,
    PillarFact,
    ShenshaResult,
    TimingResult,
)


SHENSHA_ENGINE_VERSION = "shensha-support-v1"

_TRIAD_RULES = {
    "travel_horse": {
        "申": "寅", "子": "寅", "辰": "寅",
        "寅": "申", "午": "申", "戌": "申",
        "巳": "亥", "酉": "亥", "丑": "亥",
        "亥": "巳", "卯": "巳", "未": "巳",
    },
    "peach_blossom": {
        "申": "酉", "子": "酉", "辰": "酉",
        "寅": "卯", "午": "卯", "戌": "卯",
        "巳": "午", "酉": "午", "丑": "午",
        "亥": "子", "卯": "子", "未": "子",
    },
    "solitary_star": {
        "申": "辰", "子": "辰", "辰": "辰",
        "寅": "戌", "午": "戌", "戌": "戌",
        "巳": "丑", "酉": "丑", "丑": "丑",
        "亥": "未", "卯": "未", "未": "未",
    },
}

_DAY_STEM_RULES = {
    "literary_star": {
        "甲": ("巳",), "乙": ("午",), "丙": ("申",), "丁": ("酉",),
        "戊": ("申",), "己": ("酉",), "庚": ("亥",), "辛": ("子",),
        "壬": ("寅",), "癸": ("卯",),
    },
    "heavenly_noble": {
        "甲": ("丑", "未"), "戊": ("丑", "未"), "庚": ("丑", "未"),
        "乙": ("子", "申"), "己": ("子", "申"),
        "丙": ("亥", "酉"), "丁": ("亥", "酉"),
        "辛": ("寅", "午"),
        "壬": ("巳", "卯"), "癸": ("巳", "卯"),
    },
}


def _timing_branches(timing: TimingResult | None) -> dict[str, str]:
    if timing is None:
        return {}
    items = {
        "luck_cycle": timing.luck_cycle.get("current"),
        "annual": timing.annual,
        "monthly": timing.monthly,
        "daily": timing.daily,
    }
    found = {}
    for axis, item in items.items():
        if not item or not isinstance(item, dict):
            continue
        pillar = item.get("pillar", {})
        if isinstance(pillar, dict) and pillar.get("branch"):
            found[axis] = pillar["branch"]
    return found


def _matches(targets: set[str], positions: Mapping[str, str]) -> list[dict[str, str]]:
    return [
        {"position": position, "branch": branch}
        for position, branch in positions.items()
        if branch in targets
    ]


def calculate_shensha(
    natal_pillars: Mapping[str, PillarFact | None],
    timing: TimingResult | None = None,
) -> tuple[list[ShenshaResult], list[Evidence]]:
    """Return detected shensha as supporting signals, never standalone verdicts."""

    day = natal_pillars.get("day")
    if day is None:
        return [], []

    natal_positions = {
        name: pillar.branch for name, pillar in natal_pillars.items() if pillar is not None
    }
    timing_positions = _timing_branches(timing)
    basis_branches = {
        pillar.branch
        for name in ("year", "day")
        if (pillar := natal_pillars.get(name)) is not None
    }
    definitions: list[tuple[str, set[str], dict[str, Any]]] = []
    for name, rule in _TRIAD_RULES.items():
        targets = {rule[branch] for branch in basis_branches}
        definitions.append((name, targets, {
            "basis_type": "natal_year_or_day_branch",
            "basis_values": sorted(basis_branches),
        }))
    for name, rule in _DAY_STEM_RULES.items():
        targets = set(rule[day.stem])
        definitions.append((name, targets, {
            "basis_type": "natal_day_stem",
            "basis_values": [day.stem],
        }))

    results = []
    evidence_items = []
    for name, targets, basis in definitions:
        natal_matches = _matches(targets, natal_positions)
        timing_matches = _matches(targets, timing_positions)
        if not natal_matches and not timing_matches:
            continue
        if natal_matches and timing_matches:
            source, activation = "natal+timing", "strongly_active"
        elif timing_matches:
            source, activation = "timing", "active"
        else:
            source, activation = "natal", "observed"
        evidence_id = f"evidence:shensha:{name}"
        basis_text = (
            f"{basis['basis_type']}={','.join(basis['basis_values'])}; "
            f"target={','.join(sorted(targets))}"
        )
        evidence_items.append(Evidence(
            id=evidence_id,
            layer=EvidenceLayer.SHENSHA,
            source_module=SHENSHA_ENGINE_VERSION,
            rule_code=f"{name}-traditional-v1",
            description="전통 위치식을 만족한 보조 신호이며 독립 길흉 판단에 사용하지 않음",
            source_values={
                **basis,
                "targets": sorted(targets),
                "natal_matches": natal_matches,
                "timing_matches": timing_matches,
                "standalone_judgment_allowed": False,
            },
            supports=[f"shensha:{name}"],
            reliability=ConfidenceLevel.MEDIUM,
        ))
        results.append(ShenshaResult(
            name=name,
            source=source,
            basis=basis_text,
            activation=activation,
            core_cross_checks=[
                "relationship_results",
                "diagnostic_synthesis",
                "supporting_signal_only",
            ],
            evidence_ids=[evidence_id],
            confidence=ConfidenceLevel.MEDIUM,
        ))
    return results, evidence_items
