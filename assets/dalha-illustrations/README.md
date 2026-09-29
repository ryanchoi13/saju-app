# DALHA illustration renderer

The existing recommendation engine and SVG renderer remain authoritative. The catalog selects an illustration only for an exact garment/accessory/tuck match. Unsupported items, cold-weather layers, carried outerwear, unlinked suit colours and unsupported patterns retain SVG. Male formal Derby variants currently retain SVG.

The client loads a 768px WebP and an opaque RGB PNG mask. Mask R is the 1-based colour slot (0 preserves the source), G is line coverage, B's high bit marks exterior contours and its low 7 bits encode shadow coverage. The pure renderer derives lighter coordinated outlines for pale palettes. No generation or external image API is called at runtime.

The canvas replaces the visible SVG only after both assets and pixel rendering succeed. Failed loads retain SVG; detached modal nodes cannot be painted. The existing recommendation's accessible label is preserved.

Sources: Higgsfield-generated production artwork, September 2026. `06` and `10` are the previously approved adult male formal sources; the other ten assets match the live autumn templates. See `provenance.json` for generation IDs.

Validation: `node scripts/test_fashion_illustrations.mjs` exercises the actual backend's 60 autumn recommendations across both genders and five ages (55 matches, five Derby fallbacks), unsupported shapes, deterministic colour/line rendering, asset failure and stale DOM handling. Run `python -m unittest backend.tests.test_fashion_svg_integration -q` for recommendation regressions. DOM tests use jsdom; they do not substitute for a physical mobile-device check.
