# LulaZel Hub — Cosmos UI

The site keeps the captured **Cosmos/Webflow layout** as its base: Cosmos top navigation,
Cosmos sections, Cosmos typography and the large Cosmos-style wordmark treatment. The
earlier touchfoundry-style bar has been removed.

The wordmark is rebuilt as **LulaZel Hub** in the Cosmos condensed block-letter style.
Content is taken from `LulamileMkhungela/my-new-site` and
`LulamileMkhungela/portfolio.github.io` wherever those repositories have it; captured
Cosmos content remains in place wherever they do not.

The dropdown beside the logo contains **For Marketing Teams**, **For You**, **For Tech**
and **Something Else**. **For You** is selected by default and shows the Cosmos/default
view. The other options intentionally keep that same default view until their layouts
are specified — no extra views were invented.

## Run locally

```sh
./scripts/serve.sh 3000
```

## Clone note

HTTrack 3.51 was built and installed from upstream source. Direct HTTPS transfer to
`www.cosmos.studio` was blocked in this sandbox, so the aggressive fallback mirrored a
complete local Cosmos reference source with all files/assets and unlimited depth. The
finished site is in `cosmos-copy/`.
