# Daily styling, wardrobe storage and interpretation — 2026-09-10

The wardrobe API had reverted to process dictionaries although the existing
Postgres database still contained 11 wardrobe records. Server restarts discarded
new dictionary entries and login initialized a fresh empty list.

## Changes

- Read and mutate the existing `users` / `wardrobe_items` tables using
  `DATABASE_URL`. Resolve the existing numeric owner through `users.kakao_id`;
  preserve IDs and both legacy comma-separated values and JSON arrays.
- Use database-generated item IDs, transactions and a per-account row lock.
  Writes modify individual rows and cannot overwrite another concurrent addition.
  Editing/deleting an item always includes its owner in the SQL predicate.
- Render cannot silently fall back to a local file or memory. Failures return
  503; login distinguishes an unavailable wardrobe (`null`) from a real empty
  one (`[]`). An account-specific browser cache preserves the last acknowledged
  list during a loading failure. Successful final-item deletion clears the cache.
- The existing user-ID-based API contract is preserved; this change is not a
  replacement of the application's authentication system.
- Hide the complete accessory panel when there is no eligible color/TPO match.
  Keep one labeled TPO selector that displays and saves the current choice.
- Replace uniform CSS atlas cells with 294 measured pixel rectangles. Nested SVG
  viewports clip every rectangle independently and center the full food crop.
  The seven original WebPs remain unchanged (532,124 bytes total). The catalog
  URL is versioned to avoid loading stale coordinate data.
- Biorhythm text describes each calculated phase and curve direction, followed
  by a small, practical suggestion. The explanation of the illustrative,
  non-measurement nature of birth-based cycles stays in a separate short note.

## Copy references

Reviewed [Biorhythm Calculator](https://www.biorhythm-calculator.net/) and
[BioCalendar](https://biocalendar.bg73.net/index.html) on 2026-09-10 for their
three-domain and phase-based presentation. These are presentation references,
not scientific validation. Their health, accident and performance predictions
are not adopted. Copy is original; the 23/28/33-day arithmetic and calendar
conversion remain unchanged.

## Validation and operating limits

- Backend tests cover legacy records, account isolation, parallel writes,
  a fresh Python process after add/edit and after deleting the last item,
  storage failure and the production no-fallback rule.
- DOM tests cover cache isolation, error preservation, deletion, duplicate save,
  the single TPO control, matched-to-unmatched transitions and all 294 crop paths.
- Existing nine interface scenarios and biorhythm/profile regressions pass.
- Visually reviewed all 294 crop previews. New artwork must have its crop
  rectangles reviewed again; old bounds must not be reused for a different grid.
- Existing Postgres is a free instance with an expiry of 2026-09-29. Continued
  server retention beyond that date requires upgrading/migrating the database.
  No plan or billing changes were made.
- Existing database records can be restored. Entries lost in past process-only
  deployments cannot be reconstructed without another surviving copy.
- `/api/health/storage` checks the deployed connection and expected columns
  without exposing credentials, account IDs or wardrobe contents.
