# Fashion v2 rolling board review

## Status

This is an owner-review layer, not a live board replacement. Thirty-six warm-transition
boards cover three age preferences, both genders, all three TPOs, and Daily/Trend.
They establish the approved editorial floor-flat-lay composition.
The existing reviewed production boards remain unchanged until visual approval.

## One-month coverage model

The rolling window is 35 days and is based on apparent-temperature families,
not calendar month names. The first review batch covers a hot or warm daytime
with a cooler evening; the next covers thin-long-sleeve weather; the last covers
light-jacket through knit weather. Rain and wind alter material suitability and
footwear rather than creating a fake seasonal label.

The review matrix contains 108 deterministic complete-look candidates:

- 2 genders
- 3 soft age preferences: 19–34, 35–49, 50+
- 3 weather families
- 3 TPOs
- Daily and Trend

These are complete candidates, not item pools. Age changes editorial priority
and silhouette, never eligibility. Business formal never substitutes shorts,
sandals, denim, or a carried jacket for the complete formal outfit.

## Visual approval gate

No candidate can enter the live exact-image map until its image has been made,
its item order and material have been checked against the candidate, and the
owner has approved it. This prevents a text recommendation from silently using
a different image. Static assets are prepared ahead of a thermal transition;
the already deployed Gyeongju forecast continues to select the current day's
thermal profile automatically.

## Review cadence

1. Current batch: warm daytime and cooler evening.
2. Seven days later: review thin-long-sleeve candidates before their expected
   coverage window.
3. Eighteen days later: review light-jacket and knit candidates before the end
   of the 35-day window.
4. Weekly owner reminders summarize approved, pending, and next-due batches.

Image generation itself is intentionally not performed inside a user request or
inside the production server. Only pre-generated, reviewed static assets may be
published. Automatic update means selecting a pre-approved board from forecast,
age preference and TPO; it does not mean publishing unreviewed AI imagery.

## Editorial layout rules

- Use an overhead editorial floor flat-lay, never an invisible mannequin or body-shaped hollow silhouette.
- Place the outer first, then naturally overlap the top or dress and bottom. Keep shoes readable below the clothing.
- Shoes may be 15–30% larger than literal scale for mobile readability.
- Use zero or one optional accessory only when it improves the complete look; it must never dominate the outfit.
- Select a low-saturation, high-value background for contrast from warm ivory, light blue-gray, soft warm gray, or clean off-white.
- Background color follows garment readability rather than a single fixed color or a strong copy of the outfit's main color.
