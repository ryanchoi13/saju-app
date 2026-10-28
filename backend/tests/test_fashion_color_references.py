"""코디 색 참고 데이터(fashion_v2/color_references) 형식 검사."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "fashion_v2" / "color_references"
FILES = sorted(ROOT.glob("*.json"))


def test_reference_files_exist():
    assert FILES


def test_every_reference_has_source_roles_and_ratios():
    for path in FILES:
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["source"]["title"] and data["source"]["collected_on"], path.name
        assert data["domain"], path.name
        ids = [c["id"] for c in data["combinations"]]
        assert len(ids) == len(set(ids)), path.name
        for combo in data["combinations"]:
            colors = combo["colors"]
            assert sum(c["ratio"] for c in colors) == 100, combo["id"]
            assert all(re.fullmatch(r"#[0-9A-F]{6}", c["hex"]) for c in colors), combo["id"]
            roles = [c["role"] for c in colors]
            assert roles.count("base") == 1 and roles.count("point") == 1, combo["id"]
            ordered = sorted(colors, key=lambda c: -c["ratio"])
            assert ordered[0]["role"] == "base" and ordered[-1]["role"] == "point", combo["id"]


def test_godi_guide_matches_source_count():
    data = json.loads((ROOT / "godi_3color_guide_1.json").read_text(encoding="utf-8"))
    assert len(data["combinations"]) == 9
    assert sum(c["in_video"] for c in data["combinations"]) == 4
