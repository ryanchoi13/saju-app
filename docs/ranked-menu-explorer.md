# Ranked daily menus — 2026-09-11

The current agreement replaces lunch/dinner assignments with ranked food ideas.
Breakfast and snack entries are eligible. General food and diet-only catalogs
remain separate; each view shows two menus and the next request exposes the next
two ranks without reusing an already exposed menu in that mode.

- General: first pair plus nine additional pairs, at most 20 menus.
- Diet: first pair plus four additional pairs, at most 10 menus.
- The limit button opens a dialog containing only previously exposed items,
  sorted by rank. No likes or preference learning is connected.
- Opening another mode exposes its first pair if needed. Reload/resume restores
  the first pair of the last selected mode, preserving both counters and histories.
- The server uses KST dates. At midnight a stale next request opens the new day's
  first pair instead of also spending an additional pair.

## Ranking basis

The existing core's confirmed favorable/caution directions and timing exposure
produce the primary element score. Negative directions are excluded. Ranking
uses that score first, then everyday popularity, familiarity, accessibility,
season and a stable profile/day tie break. There is no random refresh and no
liking, click, calorie, or diet-intensity inference.

Diet catalog v2 reviews elements per dish and expands the pool to 90. Only for
diet menus, equal element scores first spread culinary families and cuisines,
then use the existing everyday keys. Lower element scores still cannot pass a
higher one. General ordering is unchanged. See [diet expansion](diet-menu-expansion.md).

The core can legitimately leave its favorable direction unconfirmed. In that
case, reuse the existing daily-stem symbolic fallback with a small priority and
explicitly display “오늘의 일진을 참고해…”. Never overwrite a caution/conflicting
direction, alter the core's confidence, or claim a confirmed personal remedy.
If only caution guidance is available, retain that basis instead. Scores remain
internal service rules, not measured dietary benefit or medical advice.

## Durable state and request semantics

`menu_recommendation_days` is created additively in the existing Postgres on
startup, with an advisory lock for concurrent schema initialization. It stores
one snapshot per hashed account identity and KST day, an unguessable token,
separate mode counters, and the last selected mode. It contains no raw birth
profile. Existing snapshots remain fixed through profile edits and deployments
for that day so changes cannot reset quotas. Future dates use the current profile.

Next requests require the account's snapshot token and expected counter. A row
lock serializes writes and only the matching counter can advance. A retry with
the old counter returns the already advanced pair. Counts never depend on browser
storage. Storage failures return errors without claiming a successful change;
other app sections remain usable. Render cannot fall back to ephemeral SQLite.
The app's existing login/profile flow establishes the account context; this work
does not replace that authentication system.

## Presentation and checks

A remains the default design, with the shared dialog typography and keyboard
behavior. Public design examples exercise the same menu UI with fictional local
data and no account/API writes. Dishes with no exact thumbnail use a neutral
place-setting icon; another dish's image is never substituted.

Tests cover element priority and fallback honesty, breakfast eligibility,
determinism, mode caps, concurrent/retried requests, account/token isolation,
process restart, snapshot stability, midnight and API binding. DOM tests cover
next-pair display, failed requests, the 20/10-item dialog, first-pair restoration,
mode switching, stale account responses and the absence of likes. Existing
wardrobe, image, style and A/B preview checks remain in place.
