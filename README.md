# Project Anor

Open schematics and interactive write-ups of solar and power builds, by [bigbrovar](https://x.com/bigbrovar).

Each site lives in its own folder under `sites/`, with its own data, build script and Cloudflare config, and publishes as its own Cloudflare Worker.

Start at the guide, [project.anor.openculture.org.ng](https://project.anor.openculture.org.ng) (`sites/guide/`): pick your appliances and budget, and it points to the dashboard that fits.

## What's here

```
sites/
  guide/           the planner: pick appliances and a budget, get pointed to a design
  home-solar/      my DIY 48 V Victron home install
  deye-parallel/   the same house on two Deye 8 kW in parallel
  deye-single/     a smaller build on one Deye 8 kW
  growatt-single/  an entry build on one Growatt SPF 6000
  srne-24v/        24 V essentials on one SRNE HF 3.3 kW
diagrams/          source wiring diagrams (.drawio), opened with draw.io
```

| Site | Folder | Worker | Live |
| --- | --- | --- | --- |
| Guide | `sites/guide/` | `anor-guide` | [project.anor.openculture.org.ng](https://project.anor.openculture.org.ng) |
| Home build: two Victrons, 58.8 kWh, 18.3 kWp | `sites/home-solar/` | `project-anor` | [home.anor.openculture.org.ng](https://home.anor.openculture.org.ng) |
| Large: two Deye 8 kW, 58.8 kWh, 20.8 kWp | `sites/deye-parallel/` | `anor-deye-parallel` | [large.anor.openculture.org.ng](https://large.anor.openculture.org.ng) |
| Big little: one Deye 8 kW, 29.4 kWh, 10.4 kWp | `sites/deye-single/` | `anor-deye` | [biglittle.anor.openculture.org.ng](https://biglittle.anor.openculture.org.ng) |
| Medium: one Growatt SPF 6000, 14.7 kWh, 5.2 kWp | `sites/growatt-single/` | `anor-growatt` | [medium.anor.openculture.org.ng](https://medium.anor.openculture.org.ng) |
| Medium small: one SRNE HF 3.3 kW, 5.1 kWh, 3.25 kWp | `sites/srne-24v/` | `anor-srne` | [msmall.anor.openculture.org.ng](https://msmall.anor.openculture.org.ng) |

The files in `diagrams/` open with [draw.io](https://app.diagrams.net/). They are reference drawings of what connects to what; the sites draw their own schematics from their data.

## Building

Each site builds on its own, from its folder, into one self-contained `dist/index.html`:

```
cd sites/home-solar
python3 build.py
```

It needs Python 3 with PyYAML. Cloudflare runs the same build on every push to `main`, for the sites whose folder changed.

## Adding a new site

1. Create a folder for it under `sites/`, with its own `build.py`, `data/` and `wrangler.jsonc`. Copying an existing site is the quickest start.
2. Give it a unique `name` in its `wrangler.jsonc`.
3. In Cloudflare, create a new Worker from this repository, set **Path** to the folder, and set its build watch path to that folder followed by `/*`.
4. Add it to `sites/guide/data/guide.yaml` so the guide points to it, and to the table above.

Sites don't share code. An improvement made in one folder is copied into another only when that site needs it, so changing one site never breaks another.

## License

Code is under the MIT License (see `LICENSE`). Data, writing and photos are under [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/).
