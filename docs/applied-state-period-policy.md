# Applied State: period isolation and SAZU comparison

## Decision

Use SAZU's documented structure as a comparison aid, not a replacement engine or an accuracy oracle. Public docs: https://www.sazu.app/manse-api/docs (reviewed 2026-09-21). No live SAZU API comparison has been performed.

Core calculates and assesses relationships; Applied State projects confirmed, conditional and caution judgments without promoting observations to recommendations. Existing service readers remain compatible.

## Period contract

- Annual: natal + current decade + annual.
- Monthly: annual context + monthly.
- Daily: monthly context + daily.
- Lifetime: natal and the cycle timeline; no current daily/monthly activation is applied to the whole life.
- Reassess relationships, roots/supplies, seasonal context, overlaps, direction hypotheses and supporting shensha inside the selected scope. Filtering relation member labels after a full daily calculation is insufficient.
- Return scope-local evidence records with IDs. Relation IDs alone do not identify the scope of their premises.
- Keep unresolved effects unresolved; matching a requested operation is conditional, not realized fortune.

## Reproduced defect and validation

Synthetic female variant of the public birth sample, 1998-05-19 10:00: PR #115's annual strength summary changed from supportive on 2026-09-10 to mixed on 2026-09-11, despite unchanged natal/decade/annual/month pillars. The cause was reuse of full daily activation.

Regression coverage checks complete annual state invariance across dates and a solar-term month change; monthly invariance within the term; daily changes; scoped evidence and shensha; lifetime isolation; and no mutation of the original core.

A broad local run found an unrelated pre-existing failure in test_ranked_menu_explorer.py::MenuStoreTests::test_api_profile_binding_and_service_integration. Reproduced on main 9c16acf: the old menu-store fixture does not match the meal-set store used by the current route. It is outside this change.

## Deferred deliberately

- Birth city, longitude, true-solar-time and day-boundary conventions require an explicit comparison policy before changing natal calculations.
- Month reports currently use the 15th as a representative date; changing this UX requires separate validation.
- Do not invent rules to turn unresolved temporal effects into confirmed luck.
- This PR establishes the common query contract; it does not switch every fortune, food or fashion adapter to Applied State or claim all tab 2/3 narratives now read it.
- Before expanding narrative adapters, compare date/term/decade boundaries and unknown birth times, then obtain like-for-like live API outputs if needed.
