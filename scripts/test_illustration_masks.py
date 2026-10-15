"""Asset regressions for recolouring spill. Run with Python + Pillow + numpy."""
from pathlib import Path
from PIL import Image
import numpy as np

root = Path(__file__).resolve().parents[1] / 'assets/dalha-illustrations'
for path in root.glob('*-layers.png'):
    mask = np.asarray(Image.open(path).convert('RGB'))
    source = Image.open(path.with_name(path.name.replace('-layers.png', '.webp')))
    source.load()
    assert source.size == (mask.shape[1], mask.shape[0]) == (768, 768), path
    r = mask[:, :, 0]
    slots = r[r < 100]
    inside = set(np.unique(r[r > 100]) - 100)  # 100+n = lighter inside of slot n (jeans cuffs)
    assert set(np.unique(slots)) == set(range(int(slots.max()) + 1)), path
    assert all(np.count_nonzero(r == i) > 100 for i in range(1, int(slots.max()) + 1)), path
    assert inside <= set(range(1, int(slots.max()) + 1)), path
    assert not np.any(r == 100), path

# Reported red bomber / blue jeans / burgundy sneakers screenshot.
mask = np.asarray(Image.open(root / 'm-casual-b-layers.png'))[:, :, 0]
# 2026-10-14 running-shoe edit moved the trouser edge ~1px right; the cast-shadow strip is now x=619-621 on this row.
assert mask[433, 620] == 0, 'Trouser cast shadow must retain the original neutral colour'
assert mask[591, 159] == 0, 'Ivory sneaker sole must not receive leather colour'
assert np.count_nonzero(mask[500:] == 1) == 0, 'No jacket colour below the jacket'
assert mask[300, 200] == 1, 'Keep jacket recolour coverage'
assert mask[600, 500] == 3, 'Keep denim recolour coverage'
assert mask[610, 270] == 4, 'Keep shoe upper recolour coverage'
# 2026-10-15: rolled-up jeans cuffs carry the lighter inside label on every denim illustration.
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from mark_denim_cuffs import DENIM_CUFFS
for key in DENIM_CUFFS:
    r = np.asarray(Image.open(root / f'{key}-layers.png'))[:, :, 0]
    cuff = np.where(r > 100)
    assert 600 <= cuff[0].size <= 6000, key
    assert cuff[0].min() > np.where((r > 0) & (r < 100))[0].min() + 400, key
print('PASS: All source/mask pairs and reported shadow/sole colour-spill regressions')
