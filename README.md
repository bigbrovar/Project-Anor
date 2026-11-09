# Project Anor

Open schematics and interactive write-ups of solar and power builds, by [Bigbrovar](https://x.com/bigbrovar).

Each site lives in its own folder under `sites/`, with its own data, build script and Cloudflare config, and publishes as its own Cloudflare Worker.

## What's here

```
sites/
  home-solar/    interactive dashboard of my DIY 48 V Victron home install
diagrams/        source wiring diagrams (.drawio), opened with draw.io
```

| Site | Folder | Live |
| --- | --- | --- |
| Home solar dashboard | `sites/home-solar/` | [project-anor.bigbrovar-k3s.workers.dev](https://project-anor.bigbrovar-k3s.workers.dev/) |

The files in `diagrams/` open with [draw.io](https://app.diagrams.net/). They are reference drawings of what connects to what; the sites draw their own schematics from their data.

## Alternative designs

Sketches of how the home system could be built today. Each is its own site and Worker.

| Design | Folder | Live |
| --- | --- | --- |
| Victron replacement: two Deye 8 kW in parallel | `sites/deye-parallel/` | [deye-parallel.anor.openculture.org.ng](https://deye-parallel.anor.openculture.org.ng) |
| Budget alternative: one Deye 8 kW, two packs, 10 kWp | `sites/deye-single/` | [deye.anor.openculture.org.ng](https://deye.anor.openculture.org.ng) |
| Entry alternative: one Growatt SPF 6000, one pack, 5 kWp | `sites/growatt-single/` | [growatt.anor.openculture.org.ng](https://growatt.anor.openculture.org.ng) |

## Adding a new site

1. Create a folder for it under `sites/`, for example `sites/solar-guide/`, with its own `build.py`, `data/` and `wrangler.jsonc`. Copying `sites/home-solar/` is the quickest start.
2. Give it a unique `name` in its `wrangler.jsonc`.
3. In Cloudflare, create a new Worker from this repository, set **Path** to the folder (`sites/solar-guide`), and set its build watch path to `sites/solar-guide/*`.

Sites don't share code. An improvement made in one folder is copied into another only when that site needs it, so changing one site never breaks another.

## License

Code is under the MIT License (see `LICENSE`). Data, writing and photos are under [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/).
