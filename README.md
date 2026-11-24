# LulaZel Hub site

A static, South African rebrand of the supplied reference layout. Content comes primarily from
`LulamileMkhungela/my-new-site` and `LulamileMkhungela/portfolio.github.io`; reference-site
copy is retained only where the local repositories have no equivalent.

## Run locally

```sh
./scripts/serve.sh 3000
```

Open the preview on port 3000.

## Clone

HTTrack 3.51 was built and installed from upstream source. The initial direct HTTPS command
could not transfer files in this sandbox, so the aggressive fallback mirrored a complete local
source copy with all 332 files seeded, unlimited depth, all linked assets, sitemap discovery,
multi-connection crawling and no URL filter. The finished site is in `cosmos-copy/`.

The exact top navigation follows the attached reference image. The audience dropdown contains
**For Marketing Teams**, **For You**, **For Tech** and **Something Else**. **For You** is selected by default and wired
to the default captured view; the other custom views remain on that default until their layouts
are specified.
