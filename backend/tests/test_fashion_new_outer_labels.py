"""#188: 플리스·퀼팅 label groundwork. Adds recognition only; live output must not change.

No template, candidate or drawing uses these labels yet, so every existing result is
pinned against snapshots taken on main 2ddebd3 before the change.
"""
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from fashion_v2.candidate_attributes import ATTRIBUTES, outer_type, policy_rule
from fashion_v2.candidate_registry import SELECTOR_SOURCE, active_candidates
from fashion_v2.svg_recommendation import canonical_name

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "backend" / "tests" / "fixtures"


def _canon(category, label, gender="male", tpo="casual"):
    try:
        return canonical_name({"category": category, "label": label}, gender, tpo)
    except ValueError as error:
        return f"ERROR: {error}"


def test_every_existing_label_maps_exactly_as_on_main():
    snapshot = json.loads((FIXTURES / "canonical_label_snapshot.json").read_text(encoding="utf-8"))["results"]
    assert len(snapshot) > 500
    changed = {}
    for key, expected in snapshot.items():
        category, label, gender, tpo = key.split("|")
        actual = _canon(category, label, gender, tpo)
        if actual != expected:
            changed[key] = (expected, actual)
    assert changed == {}


def test_existing_attributes_stay_pinned_and_two_reviewed_fleece_records_are_appended():
    snapshot = json.loads((FIXTURES / "candidate_attributes_snapshot.json").read_text(encoding="utf-8"))["attributes"]
    assert json.loads(json.dumps(ATTRIBUTES, ensure_ascii=False)) == snapshot
    legacy = {c["candidate_id"] for c in active_candidates() if c["source"] != SELECTOR_SOURCE}
    assert set(ATTRIBUTES) - legacy == {
            "pending-female-winter-casual-fleece", "pending-male-winter-casual-fleece"}


@pytest.mark.parametrize("label,expected", [
    ("플리스", "플리스"), ("플리스 집업", "플리스"), ("플리스 후드 집업", "플리스"),
    ("퀼팅 재킷", "퀼팅 재킷"), ("경량 퀼팅 재킷", "퀼팅 재킷"),
    ("퀼팅 패딩", "패딩"), ("퀼팅 코트", "코트"),            # precedence kept
    ("블루종", "블루종"), ("경량 재킷", "블레이저"), ("워크 재킷", "블루종"),  # unchanged neighbours
])
def test_new_labels_and_precedence(label, expected):
    for slot in ("outer", "coat", "mid", "carry_outer"):
        assert _canon(slot, label) == expected


def test_new_outer_types_get_the_confirmed_policy_only():
    assert outer_type("플리스") == "fleece" and outer_type("퀼팅 재킷") == "quilted"
    assert outer_type("퀼팅 패딩") == "puffer"
    for kind in ("fleece", "quilted"):
        rule = policy_rule(kind, "unknown")
        assert rule["min_inclusive"] == 5 and "max_exclusive" not in rule   # no upper bound is invented
        assert rule["source"] == "owner_policy_2026-10-15"


def test_no_live_template_uses_the_new_labels_yet():
    from fashion_v2.template_catalog import TEMPLATES
    from fashion_v2.weather_catalog import WARM_TRANSITION_LOOKS
    labels = {i["label"] for t in list(TEMPLATES) + list(WARM_TRANSITION_LOOKS) for i in t["items"]}
    assert not {l for l in labels if "플리스" in l or "퀼팅" in l}


def test_fallback_svg_accepts_the_new_outer_labels():
    if shutil.which("node") is None:
        if os.environ.get("CI"):
            pytest.fail("node is missing in CI: fallback SVG check must not be skipped")
        pytest.skip("node is required (installed in CI)")
    done = subprocess.run(["node", "--no-warnings", "scripts/test_fashion_new_outer_labels.mjs"],
                          cwd=ROOT, capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    assert json.loads(done.stdout.strip().splitlines()[-1]) == {"newOuterLabelsRendered": 4, "newOverOuterLabelsRendered": 4, "unknownRejected": True}
