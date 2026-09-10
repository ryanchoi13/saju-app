# Readability and design comparison

The service strategy deck, `달하_서비스방향_사업전략_v3.pptx`, slide 13, sets the direction: modern screens with traditional depth, cards and space, moonlit navy and hanji ivory, gold only for emphasis, and expressive color in everyday styling and food results.

- `/` keeps the clear design with the shared readability/dialog improvements.
- `/design/clear` and `/design/moonlight` use the same application, account and features. Design is scoped to the URL; it never writes a theme preference.
- Add `?sample=1` for the same fictional example content in either design. The comparison control preserves the selected main tab and saju section when switching versions.
- The comparison routes are excluded from indexing. No separate infrastructure is required.

## Shared improvements

Reading text uses dark ink, 16px body text and generous line height. Stored reports are normalized at display time, including their old inline colors and pale green panels. Element charts and clothing/food colors retain their meaning. Month selection has explicit white text on its selected background.

All eight dialogs share titles, close controls, panels, inputs, primary/secondary actions and spacing. Existing close handlers remain authoritative, including the payment busy guard. Smaller dialogs gain Escape, focus containment and focus return; the report reader retains its existing back/history behavior.

The alternative uses a navy masthead, ivory surfaces, restrained gold section markers, a segmented saju selector and grouped reading links. Both versions keep Pretendard for legibility; the deck does not prescribe a font family.

## Preview isolation

The optional preview contains only fictional data, marked as examples. It substitutes an in-memory storage object before application startup, skips authentication, blocks fetch, intercepts state-changing actions, and disables final payment. Existing browser storage and account data remain untouched. It does not grant access to real reports.

## Verification

`scripts/test_design_comparison.cjs` loads the real HTML, CSS and scripts from local resources and checks both previews, identical contents, month selection, report reading, modal choices, disabled payment, no network requests and preservation of original storage. Existing business interface, styling, wardrobe and tarot regressions pass. An in-process ASGI smoke check covers the main page, both design routes, unknown-variant 404 and the four new assets. Visual verification and deployment status are recorded in the pull request.
