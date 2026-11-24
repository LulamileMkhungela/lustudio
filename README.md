# Cosmos Studio static clone

This workspace is a strict static clone of `https://www.cosmos.studio/`, built from exact live HTML, styles, scripts, wording, projects, and media references.

- All 112 canonical sitemap routes and every internal route discovered from those pages have local pages with the exact Cosmos shell.
- Original Webflow CSS, runtime JavaScript, GSAP interactions, fonts, images, Lottie files, posters and media are preserved.
- Referenced static assets are localized under `cosmos-copy/assets/`; any oversized remote media that exceeds the repository size budget is listed in `scripts/cosmos-remaining-remote-assets.json` and keeps its exact Cosmos URL.
- HTTP redirects observed on the live site are recorded in `scripts/cosmos-redirects.json` and implemented by `scripts/serve.py`.
- The only intentional UI change is a light Cosmos-styled audience dropdown beside the logo: `For Marketing Teams`, `For You` (default), `For Tech`, and `Something Else`.
- Custom views for non-default dropdown options are intentionally not implemented.

## Refresh the source

`scripts/fetch_live_cosmos.py` is run by `.github/workflows/fetch-cosmos.yml` on a machine with access to Cosmos and its CDNs. It fetches the live sitemap and route HTML, localizes assets, applies the dropdown, validates the result, captures browser screenshots, and commits the generated site to the current branch.

## Preview

```bash
./scripts/serve.sh 3000
```
