from pathlib import Path
import re

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "assets" / "fashion-review.html"
BOARD_DIR = ROOT / "assets" / "fashion-v2-boards"


def main():
    html = PAGE.read_text(encoding="utf-8")
    files = re.findall(r"file:'(sample-v[456]-[^']+\.webp)'", html)

    assert len(files) == 16, f"expected 16 samples, got {len(files)}"
    assert len(set(files)) == 16, "sample filenames must be unique"
    roles = re.findall(r"role:'([^']+)'", html)
    assert sum("Daily" in role for role in roles) == 8
    assert sum("Trend" in role for role in roles) == 8
    assert "review-" not in html, "legacy v3 boards must not leak into v4 review"

    for filename in files:
        path = BOARD_DIR / filename
        assert path.exists(), f"missing board: {filename}"
        assert path.stat().st_size > 20_000, f"board is unexpectedly small: {filename}"
        with Image.open(path) as image:
            assert image.size == (800, 1000), f"wrong dimensions: {filename} {image.size}"

    assert sum(filename.startswith("sample-v4-") for filename in files) == 6
    assert sum(filename.startswith("sample-v5-") for filename in files) == 6
    assert sum(filename.startswith("sample-v6-") for filename in files) == 4
    assert html.count("캐주얼 · 더운 초가을") == 12
    print("fashion review final calibration: 16 boards OK")


if __name__ == "__main__":
    main()
