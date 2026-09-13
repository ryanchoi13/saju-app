# Fashion v2 stage 3

The deployed `daily_fortune.fashion_v2` payload now drives the today screen. The main card keeps one recommended-color palette, shows the Daily outfit as a concise text summary, and defers the large garment presentation behind `오늘의 코디 보기`.

Inside the viewer, each Daily or Trend recommendation is presented as one editorial complete-look board: a connected hero outfit, a narrow supporting-item rail, and HTML-rendered titles. The former equal-size garment tile grid is intentionally not used. The board remains data-driven so Stage 2 A/B colors can be reflected without baking a fixed palette into a raster image.

Reviewed boards are now rolled out as pre-generated static WebP assets rather than assembled in the browser. A board is shown only when the complete template ID and applied color-name sequence match its reviewed asset; unmatched scopes keep the text recommendation but hide the viewer button instead of reusing a misleading image. Approved pairs currently cover the female autumn casual sample and Choi Jeong-o's male autumn casual Daily and Trend recommendations for Wada Duo #11 (light camel and mineral gray).

The entry button opens a mobile bottom sheet with exactly two complete looks: Daily and Trend. Users can switch with the segmented controls or native horizontal swipe. The sheet has no top-right X, repeats no color palette, locks background scrolling while open, supports Escape and arrow keys, and ends with one full-width `닫기` button. Garment artwork uses the existing generated atlas as a temporary stage-3 visual; each asset is contained rather than cropped. Final complete-look imagery remains stage 4.

The connection is progressive: if `fashion_v2` is absent or incomplete, the existing outfit cards remain the fallback. Existing TPO persistence and wardrobe matching are unchanged.

## Stage 4 garment layering requirement

Complete-look artwork must use template-specific dressing order instead of one fixed category z-index. The default visual stack is bottom garment behind the visible top hem, cardigan or jacket above the top, and coat above all inner layers. Tucked shirts are the exception: the shirt sits behind the skirt or trouser waistband. Shoes remain spatially below the hem and must not cover the lower garment. Each template must declare tucked/untucked and layer order before its final image is approved.
