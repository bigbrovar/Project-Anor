# Project Anor, Small plug-in kit

Part of [Project Anor](../../README.md). One EcoFlow DELTA 3 Classic power station (1.8 kW, 1.0 kWh) and one Jinko 650 W panel, for lights, a fan, a TV, a laptop, phones and short use of a blender. There is nothing to wire: the panel plugs into the unit through one solar cable, and appliances plug into the unit.

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
wrangler.jsonc     tells Cloudflare to serve dist/ as the site (Worker: anor-small)
```

## Building

```sh
python3 build.py
xdg-open dist/index.html
```

## Publishing on Cloudflare

Its own Worker, set up once:

- Project name: `anor-small` (matches `name` in `wrangler.jsonc`)
- Build command: `pip install pyyaml && python build.py`
- Deploy command: `npx wrangler deploy`
- Preview command: `npx wrangler versions upload`
- Path: `sites/ecoflow-small`
- Build watch paths: `sites/ecoflow-small/*`
- Custom domain: `small.anor.openculture.org.ng`

If the address changes, set `host` under `page` in `data/build.yaml`, and the kit's `url` in `sites/guide/data/guide.yaml`.

## License

The code is under the MIT License (see `LICENSE` at the repository root). The data and writing are under [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/).
