"""Mark the rolled-up inside of jeans cuffs in illustration masks (2026-10-15).

Real denim shows its lighter reverse side where the hem is rolled up. The source
pictures draw that band in a paler, less saturated blue, but the bottom slot
paints it with the same flat trouser colour. This step re-labels those pixels
as ``100 + slot`` in the red channel; renderer.js paints them with a lightened
version of the slot colour so the cuff stays paler than the leg in any colour.

Run after the mask builders (they call it for DENIM_CUFFS) or on its own:
    python scripts/mark_denim_cuffs.py [id ...]
Idempotent: existing cuff labels are reset before detection.
"""
from pathlib import Path
import json, io, sys
import numpy as np
from PIL import Image
from scipy.ndimage import binary_opening, binary_closing, binary_dilation, label

OUT = Path(__file__).resolve().parents[1] / 'assets/dalha-illustrations'
DENIM_CUFFS = ('m-casual-a', 'm-casual-b', 'f-casual-a', 'all-019', 'all-025', 'all-054', 'all-055', 'all-064')
INSIDE_OFFSET = 100
BASE_SLOTS = ['outerColor', 'topColor', 'bottomColor', 'shoeColor']


def bottom_slot(key):
    for q in json.loads((OUT / 'expansion-provenance.json').read_text()):
        if q['id'] == key:
            return [s['field'] for s in q['slots']].index('bottomColor') + 1
    return BASE_SLOTS.index('bottomColor') + 1


def mark_cuffs(key):
    path = OUT / f'{key}-layers.png'
    layers = np.asarray(Image.open(path).convert('RGB')).copy()
    r = layers[:, :, 0]
    r[r > INSIDE_OFFSET] -= INSIDE_OFFSET
    slot = bottom_slot(key)
    a = np.asarray(Image.open(OUT / f'{key}.webp').convert('RGB')).astype(float) / 255
    bot = r == slot
    mx, mn = a.max(2), a.min(2)
    sat = (mx - mn) / np.maximum(mx, 1e-6)
    body = np.median(sat[bot & (layers[:, :, 1] < 40)])
    cuff = bot & (sat < body - 0.12) & (sat > 0.12) & (mx > np.median(mx[bot]) - 0.02)
    cuff = binary_closing(binary_opening(cuff, iterations=1), iterations=3) & bot
    cc, n = label(cuff)
    sizes = np.bincount(cc.ravel())
    keep = [i for i in range(1, n + 1) if sizes[i] >= 250]
    cuff = np.isin(cc, keep)
    # Take in the stitching and inner edge of the band, but leave the outer
    # contour of the trousers on the leg colour so the outline stays continuous.
    cuff = (cuff | binary_dilation(cuff, iterations=2)) & bot & (layers[:, :, 2] < 128)
    assert 600 <= cuff.sum() <= 6000, (key, int(cuff.sum()))
    ys = np.where(cuff)[0]
    assert ys.min() > np.where(bot)[0].max() - 120, (key, 'cuff must sit at the hem')
    r[cuff] = slot + INSIDE_OFFSET
    buf = io.BytesIO()
    Image.fromarray(layers).save(buf, format='PNG')
    path.write_bytes(buf.getvalue())
    return int(cuff.sum())


if __name__ == '__main__':
    for key in sys.argv[1:] or DENIM_CUFFS:
        print(key, mark_cuffs(key))
