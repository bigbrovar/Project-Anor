# Project Anor guide

Part of [Project Anor](../../README.md). The front door at `project.anor.openculture.org.ng`: visitors tick their appliances and set a budget, and the planner points them to the dashboard that fits, with a reference price for each system.

## What's where

```
data/guide.yaml    reference prices and their sources, the systems, the
                   home build card and the planner's appliances
data/privacy.yaml  the text of the privacy page
template.html      the page design and code, with no data in it
privacy.html       the privacy page's design; build.py fills it and writes dist/privacy.html
build.py           checks the data and writes dist/index.html
wrangler.jsonc     tells Cloudflare to serve dist/ as the site (Worker: anor-guide)
```

## Common edits

**Update a price.** Change `price` under `prices` in `data/guide.yaml`, update its `range` and `sources`, and set `updated` at the top to today's date. Every total on the page is worked out from these.

**Add a system.** Add it to `systems` in size order, with the most it runs at once (`cont_w`), its surge (`surge_w`), its battery and panel sizes (`battery_kwh`, `pv_kwp`) and how many air conditioners it's designed for (`max_ac`). A `live` system also needs its dashboard `url` and its `parts`.

**Add a plug-in kit.** A kit is a power station with one panel. Give it `state: kit`, its dashboard `url`, its `parts`, and a `kit` block with `notes` (how it goes together and its limits), the maker's page or `manual` and, if there is one, an `alt`. Only list a unit whose maker publishes its solar limits. For a kit, `pv_kwp` is the most the unit accepts from the panel, and `allowance_pct` with `allowance_text` replaces the page-wide allowance.

**Keep the privacy page true.** Every site's footer says the site collects nothing and links to `/privacy`. If analytics, a form, a cookie or browser storage is ever added to any site, update `data/privacy.yaml` in the same change.

**Change the allowance.** `allowance_pct` is added to every system's parts for breakers, boards, cable and mounting. A system can set its own.

## Building

```sh
python3 build.py
xdg-open dist/index.html
```

The build prints each system's reference total.

## Publishing on Cloudflare

Its own Worker, set up once:

- Project name: `anor-guide` (matches `name` in `wrangler.jsonc`)
- Build command: `pip install pyyaml && python build.py`
- Deploy command: `npx wrangler deploy`
- Preview command: `npx wrangler versions upload`
- Path: `sites/guide`
- Build watch paths: `sites/guide/*`
- Custom domain: `project.anor.openculture.org.ng`

## License

The code is under the GNU General Public License, version 3 (see `LICENSE` at the repository root). The data and writing are under [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/).
