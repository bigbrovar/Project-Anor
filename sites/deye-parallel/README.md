# Project Anor on two Deyes

Part of [Project Anor](../../README.md). The direct alternative to the home Victron system: two Deye SUN-8K-SG06LP1-EU-CM3 hybrid inverters in parallel, 36 Jinko 590 W panels on their six built-in MPPTs, the same four Deriy packs, light loads on the joined backup outputs and heavy loads on the GEN ports as a smart load.

Built the same way as `sites/home-solar/`: the YAML files in `data/` hold everything, `template.html` holds the design, and `build.py` checks the data and writes `dist/index.html`.

## What's where

```
data/
  products.yaml    every product: specs, links and a one-line description
  build.yaml       parts, panel strings, the page text, the three energy-flow
                   views and the battery-side check settings
  combiners.yaml   what's inside each PV box and how it's wired
  layout.yaml      positions on the schematic, wire routes and cable sizes
  battery.yaml     the battery page: pack wiring, cables and JK BMS settings
template.html      the page design and code, with no data in it
build.py           checks the data and writes dist/index.html
wrangler.jsonc     tells Cloudflare to serve dist/ as the site (Worker: anor-deye-parallel)
```

## Building

```sh
python3 build.py
xdg-open dist/index.html
```

## Publishing on Cloudflare

Its own Worker, set up once:

- Project name: `anor-deye-parallel` (matches `name` in `wrangler.jsonc`)
- Build command: `pip install pyyaml && python build.py`
- Deploy command: `npx wrangler deploy`
- Preview command: `npx wrangler versions upload`
- Path: `sites/deye-parallel`
- Build watch paths: `sites/deye-parallel/*`
- Custom domain: `deye-parallel.anor.openculture.org.ng`

## License

The code is under the MIT License (see `LICENSE` at the repository root). The data and writing are under [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/).
