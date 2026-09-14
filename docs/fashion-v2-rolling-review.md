# Fashion v2 rolling board review

## 2026-09 final-calibration samples (v4)

### Warm-weather correction (v5)

- Age comparison no longer binds each age to a different temperature band.
- All twelve Casual calibration boards use the same warm early-autumn weather.
- The short-sleeve daytime outfit is centered; a thin evening layer is shown
  separately at the side instead of appearing as mandatory worn layering.
- Ten revised boards strengthen teen Trend distinction, relax thirties Casual,
  and remove heavy fifty-plus clothing. The six already-approved boards remain.

### Fifty-plus Daily/Trend correction (v6)

- Female Daily is deliberately easy and ordinary: a cotton short-sleeve top,
  pull-on pants, plain walking shoes, and a carried cardigan. Female Trend uses
  a print blouse, below-knee A-line skirt, low flats, structured bag, and one
  restrained brooch so that the styling change is immediately visible.
- Male Daily removes headwear, prioritizes cotton chinos over denim, and uses a
  quiet low-profile walking shoe. Male Trend remains age-appropriate and gains
  distinction through texture, color, and ecru cotton rather than a loud
  technical runner.
- Initial female Casual form weights are editorial starting values, not
  observed market shares: thirties Daily is pants/skirt/dress 65/20/15;
  fifty-plus Daily is 75/15/10; fifty-plus Trend is 45/35/20. Re-estimate these
  weights from Dalha selection and owner-feedback data when sample sizes permit.

- Sixteen boards are prepared before production expansion to calibrate age,
  weather, TPO, and Daily/Trend differences.
- Twelve Casual boards compare Daily and Trend for teen, thirties, and
  fifty-plus users of both genders.
- Four boundary boards test Business Casual and Business Formal for users in
  their thirties through fifties.
- Business TPOs are not generated for teens because they are not useful as a
  default recommendation.
- Weather is split into warm early autumn, mild autumn (18–23 C), and cool
  autumn (12–17 C), rather than using a calendar season alone.
- Every board uses a dressed flat-lay, natural garment overlap, enlarged shoes
  for mobile readability, and no duplicate item catalog.
- Production of the next one-to-two-month bundle begins only after these
  samples are approved; the samples themselves are not connected to live
  recommendations.

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

## Next-generation age and TPO coverage

The existing 108-candidate catalog and its 36 warm-transition boards remain
preserved for regression review. The next image batch uses five age bands and
does not spend equal board volume on age-inappropriate business contexts:

- Teens: Casual only. A future interview or ceremony mode will be a separate
  occasion, not mislabeled as Business Casual or Business Formal.
- Twenties: Casual and Business Casual by default. Business Formal is a small,
  conditional set for interviews, conservative workplaces, client-facing work,
  or formal events. Men's default is a modern no-tie suit; a tie requires a
  strict context. Women's default is a modern tailored set or dress.
- Thirties, forties, and fifty-plus: all three TPOs are prepared by default.

Across both genders, three weather families, and Daily/Trend, this produces 144
standard board scopes. The optional twenties Business Formal set adds 12 more.
Age continues to be a soft preference for garment selection; TPO visibility is
treated separately as a relevance decision.

## Visual approval gate

No candidate can enter the live exact-image map until its image has been made,
its item order and material have been checked against the candidate, and the
owner has approved it. This prevents a text recommendation from silently using
a different image. Static assets are prepared ahead of a thermal transition;
the already deployed Gyeongju forecast continues to select the current day's
thermal profile automatically.

## Trend evidence gate

Publication date or product newness never qualifies a board as Trend. The same
seasonal signal must recur in at least two applicable core editorial sources:
Vogue Runway and Vogue Korea provide the collection and Korean translation;
W Korea is the fashion-forward women's styling source; GQ Korea is the men's
styling source. At least one Korean adoption source (Musinsa, 29CM, or Queenit)
and visible change on two of silhouette, material, color/pattern, and
shoe/styling are also required. Even then the board remains owner-review pending
until explicitly approved.

The next workwear comparison moves the overly casual shoe out of forties men's
Business Casual Daily and into Trend. Daily uses a dark suede loafer or minimal
dark leather sneaker. Men's Business Formal also compares thirties and
fifty-plus with age-weighted tie color and pattern: clearer blue/burgundy for a
younger impression, deeper burgundy/navy small patterns for restrained maturity.

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
