# LulaZel Hub static site

This workspace began as an exact static clone of the original source site and is now customized for LulaZel Hub. The exact Webflow HTML, CSS, JavaScript, GSAP interactions, fonts, animations, project pages, redirects and media references are preserved; only the requested rebrand and content changes were applied.

- 101 canonical routes remain. The 10 AI news-digest posts and the Clutch recognition post were removed; 12 practical blog guides remain on the blog index and in RSS.
- Visible source-site wording, alt/ARIA text, page titles, meta descriptions, structured data, RSS copy, the giant SVG wordmark and the small logo were renamed to `LulaZel Hub`.
- All visible US-dollar prices, project budgets and hourly rates were converted at **R18 per 1 USD** and presented in South African rand.
- Every visible recognition and competition mention was removed; the surrounding 500+ / 12 stats remain.
- Email is `mkhungela.l@gmail.com`. The visible WhatsApp number is `+27 83 719 5064`; the WhatsApp URL remains exactly `https://wa.me/380638324731`.
- Every contact form uses `POST https://formspree.io/f/xvkgqalq`. The Webflow form bridge was redirected from `/api/form` to Formspree.
- Every Book a Call link points to `https://calendly.com/lulamile_m/meet-lulamile?month=2026-10&date=2026-10-29`.
- Source-site URLs, filenames, CSS/JS classes and canonical links remain unchanged. The logo-adjacent dropdown still defaults to `For You` with `For Marketing Teams`, `For Tech`, and `Something Else`; no custom option views are implemented.

## Rebuild

Run `python3 scripts/fetch_live_cosmos.py`, then `python3 scripts/customize_cosmos_clone.py`, then `python3 scripts/validate_custom_clone.py`. The exact-clone workflow is manual only so customization commits are not overwritten. Serve locally with `python3 scripts/serve.py 3000`.
