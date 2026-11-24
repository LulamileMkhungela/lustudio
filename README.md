# LulaZel Hub — exact light Cosmos UI

`cosmos-copy/` keeps the captured **original Cosmos/Webflow UI**: the off-white
page, white rounded navbar, black typography and buttons, Cosmos hero,
sections, cards, filters, footer and interactions. The later dark adaptation
CSS and generic text wordmark were removed.

Only the requested tweaks remain on top:

- the brand is **LulaZel Hub**, rebuilt with inline geometric `.logo-word` /
  `.logo-letter` vector forms in black;
- the light Cosmos navbar keeps the dropdown beside the logo, with
  **For You** selected by default;
- all navbar/list items are Cosmos items, including `Services`, `Industries`,
  `Works`, `About`, `Blog`, `Contacts`, the Cosmos services dropdown and the
  right-side `Contact Lulamile` / `Business Developer` / `Book a Call` block;
- Cosmos service labels remain in the hero: `UI/UX Product design`,
  `Web design`, `Branding`, `Development`;
- supplied South African contact details and owner project/testimonial content
  are used where they exist, with Cosmos copy retained elsewhere.

`For Marketing Teams`, `For Tech` and `Something Else` intentionally keep the
default Cosmos view; no extra views were invented.

## Run locally

```sh
./scripts/serve.sh 3000
```

## Rebuild

`scripts/rebuild_exact_cosmos.py` is idempotent within this workspace. It resets
`cosmos-copy/` from the complete local `/tmp/site-source` Cosmos fallback,
strips the non-Cosmos dark CSS, writes the light theme/tweaks and reapplies the
brand, navigation, wordmark and content changes.
