# Fashion v2 stage 3

The deployed `daily_fortune.fashion_v2` payload now drives the today screen. The main card keeps one recommended-color palette, shows the Daily outfit as a concise text summary, and defers the large garment presentation behind `오늘의 코디 보기`.

Inside the viewer, each Daily or Trend recommendation is presented as one editorial complete-look board: a connected hero outfit, a narrow supporting-item rail, and HTML-rendered titles. The former equal-size garment tile grid is intentionally not used. The board remains data-driven so Stage 2 A/B colors can be reflected without baking a fixed palette into a raster image.

The entry button opens a mobile bottom sheet with exactly two complete looks: Daily and Trend. Users can switch with the segmented controls or native horizontal swipe. The sheet has no top-right X, repeats no color palette, locks background scrolling while open, supports Escape and arrow keys, and ends with one full-width `닫기` button. Garment artwork uses the existing generated atlas as a temporary stage-3 visual; each asset is contained rather than cropped. Final complete-look imagery remains stage 4.

The connection is progressive: if `fashion_v2` is absent or incomplete, the existing outfit cards remain the fallback. Existing TPO persistence and wardrobe matching are unchanged.
