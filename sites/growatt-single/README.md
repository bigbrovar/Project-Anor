# Project Anor on one Growatt

Part of [Project Anor](../../README.md). An alternative design for the home solar system, rebuilt around one Deye SUN-8K-SG06LP1-EU-CM3 hybrid inverter: 21 Jinko 590 W panels on its three built-in MPPTs, the same four Deriy packs, light loads on backup and heavy loads on the grid side.

Built the same way as `sites/home-solar/`: the YAML files in `data/` hold everything, `template.html` holds the design, and `build.py` checks the data and writes `dist/index.html`.

## What's where

```
data/
  products.yaml    every product: specs, links and a one-line description
  build.yaml       parts, panel strings, the page text, the three energy-flow
                   views and the battery-side check settings
  combiners.yaml   what's inside the PV box and how it's wired
  layout.yaml      positions on the schematic, wire routes and cable sizes
  battery.yaml     the battery page: pack wiring, cables and JK BMS settings
template.html      the page design and code, with no data in it
build.py           checks the data and writes dist/index.html
wrangler.jsonc     tells Cloudflare to serve dist/ as the site (Worker: anor-growatt)
```

## Building

```sh
python3 build.py
xdg-open dist/index.html
```

## Publishing on Cloudflare

Its own Worker, set up once:

- Project name: `anor-growatt` (matches `name` in `wrangler.jsonc`)
- Build command: `pip install pyyaml && python build.py`
- Deploy command: `npx wrangler deploy`
- Preview command: `npx wrangler versions upload`
- Path: `sites/growatt-single`
- Build watch paths: `sites/growatt-single/*`
- Custom domain: `growatt.anor.openculture.org.ng`

## License

The code is under the MIT License (see `LICENSE` at the repository root). The data and writing are under [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/).
