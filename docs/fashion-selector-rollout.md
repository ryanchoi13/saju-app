# Fashion selector rollout

PR-4B connects the reviewed selector to the existing two-look response without
removing the legacy builder. The server setting below is the rollout and rollback
control; the default is `off`.

| Stage | Environment |
|---|---|
| Disabled / rollback | `DALHA_FASHION_SELECTOR_ROLLOUT=off` |
| Test accounts | `DALHA_FASHION_SELECTOR_ROLLOUT=allowlist` and comma-separated full internal account IDs in `DALHA_FASHION_SELECTOR_ACCOUNTS` |
| Limited stable cohort | `DALHA_FASHION_SELECTOR_ROLLOUT=limited` and an integer 0–100 in `DALHA_FASHION_SELECTOR_PERCENT`; allowlisted accounts are always included |
| All signed-in members | `DALHA_FASHION_SELECTOR_ROLLOUT=all` |

The limited cohort uses a stable hash of the internal account ID, so a member does
not move in and out between requests. Guest or incomplete-account requests always
use the legacy result.

## Safety contract

- The browser still receives exactly two looks per TPO.
- The selector uses durable PostgreSQL in production and the application's local
  SQLite database only in local development. Render never falls back to an
  ephemeral file.
- A same-day result is reused. A stored role is changed only when a newer forecast
  breaks a hard rule; prior days provide exposure history.
- A selector error, storage error, or missing basic/trendy role returns the existing
  legacy pair for that TPO.
- The fleece review remains 7°C inclusive to 11°C exclusive and rain/snow
  unsuitable. A selected fleece look replaces the generic cold-band coat sentence
  with wording based on the look actually shown.

## Deployment sequence

1. Deploy with rollout `off`; confirm `/api/health/storage` reports `outfits` as
   `postgresql` and the existing fashion response is unchanged.
2. Set `allowlist` for the owner's test account. Check casual results at a valid
   7–11°C fixture or controlled test, same-day reload, both cards, illustration
   hydration, mobile modal and weather guidance.
3. Use `limited` with a small percentage. Watch selector fallback diagnostics and
   server warnings; raise the percentage only after stable results.
4. Set `all` after the limited cohort is accepted. Set `off` to roll back instantly;
   stored rows may remain because the legacy path ignores them.
