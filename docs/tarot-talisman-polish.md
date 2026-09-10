# Tarot and talisman presentation — 2026-09-10

## Card introductions

The reading now starts with a short explanation of the card's depicted scene
and general meaning, before the existing symbolism, daily reading and action
guide. The current deck contains the Fool and Magician; this change adds
descriptions for both and does not expand the deck. Consecutive draws within
the running session avoid returning the same card.

Primary references: A. E. Waite, *The Pictorial Key to the Tarot*,
[The Fool](https://sacred-texts.com/tarot/pkt/pktar00.htm) and
[The Magician](https://sacred-texts.com/tarot/pkt/pktar01.htm). The scene descriptions
are paraphrased; their application to daily choices is editorial interpretation.

## Selecting an additional card

The first selection opens the free card. For an additional card, the user chooses
a card back and sees a confirmation immediately below the cards: current balance,
the fixed 10-coin price, and the balance after spending. Selecting or cancelling
does not spend coins. Previously opened cards can be read again without charging.
After three cards, shuffling opens a fresh selection without spending coins.

Insufficient funds lead to the existing top-up surface. Completing or cancelling
the top-up returns to the selected card. A successful top-up does not draw or
spend automatically: the user still confirms the 10-coin draw.

The draw now uses POST. The old GET endpoint is read-only and rejects paid draws.
The backend checks the fixed price, returns the authoritative balance and caches
the result by account, Korea date and request ID. Duplicate clicks are disabled;
retrying a lost response uses the same request ID. A free request made after a
free card was already opened returns a confirmation-required response, never an
automatic charge. Wallet mutations for tarot, report spending and top-ups share
a lock in the existing process.

The browser stores opened cards and pending requests by account and Korea date.
This supports rereading after a refresh and separates accounts. The existing
wallet and server receipts remain in memory: this is a draw-flow improvement,
not a persistent wallet migration or a real payment-gateway integration. A
server restart clears server receipts, so exactly-once recovery across restarts
is not guaranteed. No production card purchase or top-up is used for testing.

## Artwork

The existing SVG approach is retained. The navy tarot back adds a gold rosette,
moon, stars and corner ornaments. All gradient IDs are unique across the three
cards. Keyboard selection and reduced-motion behavior are supported.

The talisman uses a muted paper color, dark red strokes and a small seal. Its
central glyph now follows the selected wood, fire, earth, metal or water type;
the previous renderer ignored that parameter. The UI removes the unsupported
handmade/secret-manual/cinnabar-material claims and uses quieter wording. The
preview and enlarged drawing have distinct SVG IDs. The saved image preserves
the artwork's 7:12 ratio and needs no external raster image or CJK font.

## Checks

Backend tests cover free and paid draws, fixed price, insufficient funds,
separate accounts/dates, request validation, duplicate and concurrent requests,
receipt conflicts and draw failures before spending. DOM tests cover selecting,
cancelling, rereading, double-click prevention, authoritative balances, uncertain
response retry, insufficient funds, top-up return without an automatic draw,
account restoration, a free-card conflict across tabs, descriptions and SVG IDs.
The existing interface, wardrobe, outfit and food-image checks remain enabled.
Tarot backs and all five talismans are rendered and inspected before publishing.
