# axellsdojo.com

The website of the Axell Signature suite - free, open-source audio plugins for Windows and Linux.

- `public/` - the site as served (static HTML, CSS, a little JavaScript; no framework).
- `src/` - the stylesheet, script and headers copied into `public/`.
- `build.py` - generates `public/` from the plugins' content (pitch, measured points, screenshots).

Hosted on Cloudflare Workers (static assets): `wrangler.jsonc` serves `public/`; every push to main deploys.
Text and code: AGPL-3.0, like the plugins. Audio examples: see `public/audio/CREDITS.md` (their own licences).
