"""Prepare Higgsfield flat-lay sources before mask building (2026-10-20, 바 배치).

Two deterministic fixes, applied to a copy of each original PNG:

1. Background: pixels connected to the image border that are pale and nearly grey
   (saturation < 0.15, value > 205) become one shared ivory, so every drawing sits on the
   same background even when the generator drifted toward green or yellow.
2. Highlights: strongly coloured pixels that are almost white in value (saturation > 0.2,
   value >= 249) are scaled down to value 248. The mask builder ignores value >= 249 as
   background, so without this, bright spots inside a garment stay in their source colour
   (a pink fleck on a white shirt, a yellow glint on a black bag).

Usage: python scripts/prepare_flatlay_sources.py SRC_DIR DST_DIR
"""
from pathlib import Path
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import label

IVORY = (249, 247, 230)


def prepare(im: Image.Image) -> tuple[Image.Image, dict]:
    rgb = np.asarray(im.convert("RGB")).astype(np.float64)
    mx = rgb.max(axis=2)
    mn = rgb.min(axis=2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)

    pale = (sat < 0.15) & (mx > 205)
    lab, _ = label(pale)
    border = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    border = border[border != 0]
    bg = np.isin(lab, border)
    # Background enclosed by a garment (inside a bag strap, between an arm and the body) is not
    # border-connected; catch pale patches whose colour matches this image's own border colour.
    edge = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
    ref = np.median(edge, axis=0)
    near = pale & (np.abs(rgb - ref).max(axis=2) <= 8)
    plab, _ = label(near & ~bg)
    sizes = np.bincount(plab.ravel())
    keep = np.where(sizes >= 200)[0]
    keep = keep[keep != 0]
    bg |= np.isin(plab, keep)
    rgb[bg] = IVORY

    hot = (sat > 0.2) & (mx >= 249) & ~bg
    rgb[hot] *= (248.0 / mx[hot])[:, None]

    out = Image.fromarray(np.rint(np.clip(rgb, 0, 255)).astype("uint8"))
    return out, {"background_px": int(bg.sum()), "highlight_px": int(hot.sum())}


def main(src: Path, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    for path in sorted(src.glob("*.png")):
        out, stats = prepare(Image.open(path))
        out.save(dst / path.name)
        print(path.name, stats)


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
