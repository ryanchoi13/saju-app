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
    assert set(np.unique(mask[:, :, 0])) == {0, 1, 2, 3, 4}, path
    assert all(np.count_nonzero(mask[:, :, 0] == i) > 100 for i in range(1, 5)), path

# Reported red bomber / blue jeans / burgundy sneakers screenshot.
mask = np.asarray(Image.open(root / 'm-casual-b-layers.png'))[:, :, 0]
assert mask[433, 618] == 0, 'Trouser cast shadow must retain the original neutral colour'
assert mask[591, 159] == 0, 'Ivory sneaker sole must not receive leather colour'
assert np.count_nonzero(mask[500:] == 1) == 0, 'No jacket colour below the jacket'
assert mask[300, 200] == 1, 'Keep jacket recolour coverage'
assert mask[600, 500] == 3, 'Keep denim recolour coverage'
assert mask[610, 270] == 4, 'Keep shoe upper recolour coverage'
print('PASS: 12 source/mask pairs and reported shadow/sole colour-spill regressions')
