# Project Anor, Tiny plug-in kit

Part of [Project Anor](../../README.md). The smallest design: one EcoFlow DELTA 3 1000 Air power station (500 W, 0.96 kWh) and one Jinko 650 W panel, for lights, a fan, a TV, a laptop and phones. There is nothing to wire: the panel plugs into the unit through one solar cable, and appliances plug into the unit.

Built the same way as the other dashboards: the YAML files in `data/` hold everything, `template.html` holds the design, and `build.py` checks the data and writes `dist/index.html`. A kit has no combiner box, AC boards or separate battery, so it has no `combiners.yaml`, `boards.yaml` or `battery.yaml`.

## What's where

```
data/
  products.yaml    the panel, the solar cable and the power station: specs,
                   links, a one-line description and why each was picked
  build.yaml       parts, the page text, the three energy-flow views and
                   the check settings
  layout.yaml      positions on the schematic and the wire routes
template.html      the page design and code, with no data in it
build.py           checks the data and writes dist/index.html
wrangler.jsonc     tells Cloudflare to serve dist/ as the site (Worker: anor-tiny)
```

## Building

```sh
python3 build.py
xdg-open dist/index.html
```

## Publishing on Cloudflare

Its own Worker, set up once:

- Project name: `anor-tiny` (matches `name` in `wrangler.jsonc`)
- Build command: `pip install pyyaml && python build.py`
- Deploy command: `npx wrangler deploy`
- Preview command: `env -u WRANGLER_CI_MATCH_TAG npx wrangler versions upload`
- Path: `sites/ecoflow-tiny`
- Build watch paths: `sites/ecoflow-tiny/*`
- Custom domain: `tiny.anor.openculture.org.ng`

The preview command is longer than on the other sites because of a Cloudflare fault. On this Worker, preview builds were given an ID that matches no Worker, and failed with "The name in your wrangler.jsonc file (anor-tiny) must match the name of your Worker", although the name was right. `env -u WRANGLER_CI_MATCH_TAG` skips that check for previews. Production builds are not affected. The fault is tracked at [cloudflare/workers-sdk#15682](https://github.com/cloudflare/workers-sdk/issues/15682); once it is fixed, the plain `npx wrangler versions upload` can go back.

If the address changes, set `host` under `page` in `data/build.yaml`, and the kit's `url` in `sites/guide/data/guide.yaml`.

## License

The code is under the GNU Affero General Public License, version 3 (see `LICENSE` at the repository root). The data and writing are under [Creative Commons Attribution-ShareAlike 4.0](https://creativecommons.org/licenses/by-sa/4.0/): credit bigbrovar, and share anything you build on them under the same licence.
