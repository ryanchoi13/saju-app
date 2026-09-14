from pathlib import Path
import re

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "assets" / "fashion-review.html"
BOARD_DIR = ROOT / "assets" / "fashion-v2-boards"


def main():
    html = PAGE.read_text(encoding="utf-8")
    files = re.findall(r"file:'(sample-v(?:[4-9]|1[01])-[^']+\.webp)'", html)

    assert len(files) == 16, f"expected 16 samples, got {len(files)}"
    assert len(set(files)) == 16, "sample filenames must be unique"
    roles = re.findall(r"role:'([^']+)'", html)
    assert sum("Daily" in role for role in roles) == 9
    assert sum("Trendy" in role for role in roles) == 7
    assert "sample-review-" not in html, "legacy v3 boards must not leak into current review"

    for filename in files:
        path = BOARD_DIR / filename
        assert path.exists(), f"missing board: {filename}"
        assert path.stat().st_size > 15_000, f"board is unexpectedly small: {filename}"
        with Image.open(path) as image:
            assert image.size == (800, 1000), f"wrong dimensions: {filename} {image.size}"

    assert sum(filename.startswith("sample-v4-") for filename in files) == 2
    assert sum(filename.startswith("sample-v5-") for filename in files) == 3
    assert sum(filename.startswith("sample-v6-") for filename in files) == 1
    assert sum(filename.startswith("sample-v7-") for filename in files) == 2
    assert sum(filename.startswith("sample-v8-") for filename in files) == 1
    assert sum(filename.startswith("sample-v9-") for filename in files) == 2
    assert sum(filename.startswith("sample-v10-") for filename in files) == 4
    assert sum(filename.startswith("sample-v11-") for filename in files) == 1
    assert "업무용 경계 샘플" not in html
    assert "같은 포멀 Daily에서 수트 인상과 넥타이 색·패턴" in html
    assert html.count("캐주얼 · 더운 초가을") == 12
    print("fashion review final calibration: 16 boards OK")


if __name__ == "__main__":
    main()
