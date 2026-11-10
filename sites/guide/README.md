# Project Anor guide

Part of [Project Anor](../../README.md). The front door at `project.anor.openculture.org.ng`: visitors tick their appliances and set a budget, and the planner points them to the dashboard that fits, with a reference price for each system.

## What's where

```
data/guide.yaml    reference prices and their sources, the systems, the
                   home build card and the planner's appliances
template.html      the page design and code, with no data in it
build.py           checks the data and writes dist/index.html
wrangler.jsonc     tells Cloudflare to serve dist/ as the site (Worker: anor-guide)
```

## Common edits

**Update a price.** Change `price` under `prices` in `data/guide.yaml`, update its `range` and `sources`, and set `updated` at the top to today's date. Every total on the page is worked out from these.

**Publish the small 12 V dashboard.** Change the `small` system's `state` from `pending` to `live`, and give it a `url` and `parts`.

**Add a system.** Add it to `systems` in size order, with the most it runs at once (`cont_w`), its surge (`surge_w`), the energy its panels make on a typical day (`kwh_day`) and how many air conditioners it's designed for (`max_ac`).

**Change the allowance.** `allowance_pct` is added to every system's parts for breakers, boards, cable and mounting.

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

The code is under the MIT License (see `LICENSE` at the repository root). The data and writing are under [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/).
