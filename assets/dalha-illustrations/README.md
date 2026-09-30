# DALHA illustration renderer

The existing recommendation engine and SVG renderer remain authoritative. The catalog selects an illustration only for an exact garment/accessory/tuck match. Unknown items or patterns show an image-preparation message; legacy SVG is never displayed. The expanded catalog covers 63 current configurations across seasons, temperature bands, rain, carry layers, winter layers and special age/palette rules. The inventory includes denim-to-cotton alternatives evaluated during colour scoring.

The client loads a 768px WebP and an opaque RGB PNG mask. Mask R is the 1-based colour slot (0 preserves the source), G is line coverage, B's high bit marks exterior contours and its low 7 bits encode shadow coverage. The pure renderer derives lighter coordinated outlines for pale palettes. No generation or external image API is called at runtime.

The canvas replaces a loading message only after both assets and pixel rendering succeed. Failed loads offer a retry button; the SVG remains hidden for its accessible label. detached modal nodes cannot be painted. The existing recommendation's accessible label is preserved.

Sources: Higgsfield-generated production artwork, September 2026. `06` and `10` are the previously approved adult male formal sources; the other ten assets match the live autumn templates. See `provenance.json` for generation IDs.

Validation: `node scripts/test_fashion_illustrations.mjs` exercises the actual backend's 60 autumn recommendations across both genders and five ages, plus 86,085 structural candidate scenarios (63 distinct matches), plus 144 post-colour recommendations, unsupported shapes, deterministic colour/line rendering, asset failure and stale DOM handling. Run `python -m unittest backend.tests.test_fashion_svg_integration -q` for recommendation regressions. DOM tests use jsdom; they do not substitute for a physical mobile-device check.

Mask preparation: `python scripts/build_illustration_masks.py --sources /path/to/original-pngs` (Pillow, numpy, scipy). Neutral cast shadows and ivory sneaker soles are excluded from recolouring. Run `python scripts/test_illustration_masks.py` to check asset integrity and the red-jacket shadow/sole regression.

Expansion: `expansion-provenance.json` records 52 additional assets, prompts, source URLs and packed colour slots. Use `python scripts/build_expanded_illustration_masks.py --workdir /path/to/workdir` with original PNGs inside `originals/`. There are 63 geometry configurations and 64 source/mask pairs including two approved male formal age variants. All pants are full length, formal skirts/dresses knee length. Carry/worn mode, extra outer layers, turtlenecks, tie stripes, and separate watch dial/strap/case colours are supported. Bag handles are assigned to bag colour.
