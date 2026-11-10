# Project Anor, 24 V essentials on one SRNE

Part of [Project Anor](../../README.md). A mid-small 24 V system for essential house loads, built around one SRNE HF2430S80-H 3.3 kW off-grid inverter: 5 Jinko 650 W panels (3.25 kWp; 590 to 650 W, depending on availability) on its built-in tracker, one FIRMAN 5 kWh LiFePO4 battery, and lights, fans, TV, Wi-Fi, laptops and a small fridge on its output.

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
  battery.yaml     the battery page: pack wiring, cables and the SRNE’s battery settings
template.html      the page design and code, with no data in it
build.py           checks the data and writes dist/index.html
wrangler.jsonc     tells Cloudflare to serve dist/ as the site (Worker: anor-srne)
```

## Building

```sh
python3 build.py
xdg-open dist/index.html
```

## Publishing on Cloudflare

Its own Worker, set up once:

- Project name: `anor-srne` (matches `name` in `wrangler.jsonc`)
- Build command: `pip install pyyaml && python build.py`
- Deploy command: `npx wrangler deploy`
- Preview command: `npx wrangler versions upload`
- Path: `sites/srne-24v`
- Build watch paths: `sites/srne-24v/*`
- Custom domain: `msmall.anor.openculture.org.ng`

## License

The code is under the MIT License (see `LICENSE` at the repository root). The data and writing are under [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/).
