# Project Anor on one Growatt

Part of [Project Anor](../../README.md). The entry-level alternative to the home solar system, built around one Growatt SPF 6000 ES Plus off-grid inverter: 8 Jinko 650 W panels (5.2 kWp; 590 to 650 W, depending on availability) on its two built-in MPPTs, one Deriy 14.7 kWh pack, and light loads plus one air conditioner on its single output.

Built the same way as `sites/home-solar/`: the YAML files in `data/` hold everything, `template.html` holds the design, and `build.py` checks the data and writes `dist/index.html`.

## What's where

```
data/
  products.yaml    every product and maker: specs, links, a one-line
                   description and why it was picked
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
- Custom domain: `medium.anor.openculture.org.ng`

## License

The code is under the MIT License (see `LICENSE` at the repository root). The data and writing are under [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/).
