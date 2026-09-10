# Shoes and accessory matching — 2026-09-11

Male casual looks previously appended white sneakers unconditionally. Casual
shoes now follow the actual trouser color and the rendered top's brightness,
using white, gray, black, navy, beige or brown. Both genders use this restrained
range while retaining their existing sneaker/loafer illustrations. Business
casual loafers use brown with navy and warm/light trousers, or black with black
and gray trousers. Formal shoes remain black.

The daily Wada colors and element still determine the accent and supporting
trousers. Shoes complete that outfit; they are not a new lucky-color reading.
Identical outfits can legitimately repeat a shoe color. No calendar rotation or
random anti-repeat rule is added.

Accessory matching remains limited to owned wardrobe items. Category, material,
selected clothing context and the daily palette must all qualify. Leather and
rubber watches and casual sneakers remain supported; rubber watches and sneakers
still cannot bypass the stricter business rules. Empty results hide the entire
panel without replacement text. The independent lucky-item recommendation is
unchanged.

Normalize only equivalent color spellings (`옐로우/옐로`,
`머스타드/머스터드`) and surrounding whitespace before matching. Silver is not
gray, gold is not mustard, and pink is not red. Supporting neutral outfit colors
do not automatically make every neutral accessory eligible.

Verification covers every Wada duo, both genders and all five elements: shoe
range, variation, context, sprite and caption agreement, plus existing accent
and trouser rules. DOM regressions cover the retained accessory types, color
aliases, mismatches, context restrictions and empty-panel behavior. Wardrobe
persistence and both public design-comparison variants also pass. No wardrobe
records or account settings are rewritten by this change.
