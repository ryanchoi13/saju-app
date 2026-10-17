"""Read-only integrity checks for the A-method illustration assets.

The client (assets/dalha-illustrations/catalog.js) picks an illustration only for an
exact garment geometry match, then recolours `<id>.webp` with `<id>-layers.png`.
This module reads the same registry from Python so tests can check that every
registered illustration has both files, that the two files have the same pixel
size, and that no unregistered file is shipped by accident.

It never decodes pixels and needs no image library: sizes come from file headers.
Nothing here is imported by the live recommendation path.
"""
from __future__ import annotations

import json
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "assets" / "dalha-illustrations"
REGISTRY_FILE = ASSET_DIR / "catalog-data.js"
MATCHER_FILE = ASSET_DIR / "catalog.js"
ADAPTER_FILE = ASSET_DIR / "adapter.js"

# Files that are rendered without their own registry entry. catalog.js swaps the
# matched entry id for the file id when the condition holds.
CONDITIONAL_VARIANTS = {
    "10": {"base": "06", "condition": "age >= 50",
           "matcher_rule": "entry.id==='06'&&Number(look.age)>=50?'10'"},
}


def load_registry(path: Path = REGISTRY_FILE) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    marker = "export const illustrations="
    start = text.index(marker) + len(marker)
    body = text[start:].strip()
    if body.endswith(";"):
        body = body[:-1]
    return json.loads(body)


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        head = handle.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
        raise ValueError(f"{path.name}: not a PNG")
    return struct.unpack(">II", head[16:24])


def webp_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        head = handle.read(30)
    if head[:4] != b"RIFF" or head[8:12] != b"WEBP":
        raise ValueError(f"{path.name}: not a WebP")
    chunk = head[12:16]
    if chunk == b"VP8X":
        width = int.from_bytes(head[24:27], "little") + 1
        height = int.from_bytes(head[27:30], "little") + 1
        return width, height
    if chunk == b"VP8 ":
        if head[23:26] != b"\x9d\x01\x2a":
            raise ValueError(f"{path.name}: bad VP8 frame")
        width, height = struct.unpack("<HH", head[26:30])
        return width & 0x3FFF, height & 0x3FFF
    if chunk == b"VP8L":
        if head[20] != 0x2F:
            raise ValueError(f"{path.name}: bad VP8L signature")
        bits = int.from_bytes(head[21:25], "little")
        return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
    raise ValueError(f"{path.name}: unknown WebP chunk {chunk!r}")


def asset_versions() -> dict:
    """Cache-busting versions the adapter requests (`?v=`)."""
    text = ADAPTER_FILE.read_text(encoding="utf-8")
    found = {}
    for name, pattern in (("webp", r"'\.webp\?v=([^']+)'"), ("mask", r"'-layers\.png\?v=([^']+)'")):
        match = re.search(pattern, text)
        found[name] = match.group(1) if match else None
    return found


def inspect_assets() -> dict:
    """Return the asset inventory and a list of problems (empty when healthy)."""
    registry = load_registry()
    problems = []
    ids = [entry["id"] for entry in registry]
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    if duplicates:
        problems.append(f"duplicate registry ids: {duplicates}")

    matcher_text = MATCHER_FILE.read_text(encoding="utf-8")
    expected_files = set(ids)
    for file_id, variant in CONDITIONAL_VARIANTS.items():
        if variant["base"] not in ids:
            problems.append(f"conditional file {file_id}: base {variant['base']} not registered")
        if variant["matcher_rule"] not in matcher_text:
            problems.append(f"conditional file {file_id}: catalog.js no longer contains its rule")
        if file_id in ids:
            problems.append(f"conditional file {file_id} is also registered")
        expected_files.add(file_id)

    sizes = {}
    for file_id in sorted(expected_files):
        art, mask = ASSET_DIR / f"{file_id}.webp", ASSET_DIR / f"{file_id}-layers.png"
        missing = [p.name for p in (art, mask) if not p.is_file()]
        if missing:
            problems.append(f"{file_id}: missing {missing}")
            continue
        art_size, mask_size = webp_size(art), png_size(mask)
        sizes[file_id] = art_size
        if art_size != mask_size:
            problems.append(f"{file_id}: webp {art_size} != mask {mask_size}")

    shipped = {p.name[:-5] for p in ASSET_DIR.glob("*.webp")}
    shipped_masks = {p.name[:-len("-layers.png")] for p in ASSET_DIR.glob("*-layers.png")}
    orphans = sorted((shipped | shipped_masks) - expected_files)
    if orphans:
        problems.append(f"unregistered files: {orphans}")

    for entry in registry:
        slots = entry.get("slots") or []
        if not slots or len(set(slots)) != len(slots):
            problems.append(f"{entry['id']}: slots must be non-empty and unique")

    return {
        "registry_entries": len(ids),
        "conditional_files": sorted(CONDITIONAL_VARIANTS),
        "files": len(expected_files),
        "sizes": sizes,
        "versions": asset_versions(),
        "problems": problems,
    }
