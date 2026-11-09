# Home solar dashboard

Part of [Project Anor](../../README.md). An open, interactive write-up of my DIY 48 V home solar install: two Victron inverters on one shared battery bank, four panel arrays and grid backup. The page has a clickable wiring schematic, the wiring inside each combiner box, sizing checks worked out from the datasheet numbers, and the full parts list.

Everything on the page comes from four plain-text data files, so the build can be read, corrected and reused without touching any code.

## What's where

```
data/
  products.yaml    every product: specs, links and a one-line description
  build.yaml       this install: parts and quantities, panel strings, the
                   Sunny day / Night / Grid on views, battery-side check settings
  combiners.yaml   what's inside each combiner box and how it's wired
  layout.yaml      positions on the schematic, wire routes and cable sizes,
                   photo callouts
  battery.yaml     the battery page: pack wiring, cables, current share and
                   JK BMS settings
template.html      the page design and code, with no data in it
install.jpg        the equipment-room photo
busbar.jpg         the home-built busbar, shown on the battery page
build.py           checks the data and writes dist/index.html
wrangler.jsonc     tells Cloudflare to serve dist/ as the site
```

`build.py` combines the data, the template and the photo into a single `dist/index.html` with everything inside it. It works opened straight from disk, on Cloudflare or on any other host.

## Making changes

Most edits are a line or two in one YAML file. The sizing checks recalculate from the data on every build, so you never update them by hand.

**Fix or fill in a spec.** Find the product in `data/products.yaml` and change the value. Blank specs are `null`. They stay hidden on the page until you fill them in, and every build lists them.

**Swap a part.** Add the new product to `products.yaml`, then point the part in `build.yaml` (or the combiner in `combiners.yaml`) at its id. For example, to replace Combiner D's string breakers:

```yaml
# data/products.yaml, under products:
  string-breaker-30a:
    name: DC breaker, 1 pole, 30 A
    icon: mcb
    about: DC breaker. Switches one string off and trips on overload.
    specs:
      current_a: 30
      voltage_vdc: null

# data/combiners.yaml, under combiner-d:
  string_protection: string-breaker-30a
```

Then update that box's `inside` list and its `steps` text, which still describe the old breaker.

**Add a link.** Under the product's `links`, add a `buy` or `alternatives` entry with a `name` and `url`. Mark affiliate links with `affiliate: true` so the page labels them.

**Change wording.** Product descriptions are in `products.yaml`, combiner text is in `combiners.yaml`, and the Sunny day / Night / Grid on captions are in `build.yaml`. The intro, install and "layout at a glance" text is in `template.html`.

**Add or move something on the drawing.** Edit `layout.yaml`. Each block has `at: [x, y, width, height]` and each wire has an SVG `path`; the comments at the top of the file explain both. This is the fiddliest kind of edit, so rebuild and look at the drawing after each change.

**Add a cable size.** On a power wire in `layout.yaml`, add `size` and `length`, for example `size: 35 mm², length: 2.5 m`. They show when someone hovers the wire and under "Wired to" in the detail panel. Leave them off where you don't know them yet.

**Update the battery page.** Everything on `index.html#battery` comes from `data/battery.yaml`: the pack links and runs, the current share and the BMS settings. Voltages are entered per cell; the page works out the 16S pack figure.

**Mark a new version.** Change `version` and `updated` at the top of `build.yaml`. Both show in the footer.

## Building on your computer

On Fedora, Python 3 is already installed and PyYAML is in the Fedora repos:

```sh
sudo dnf install python3-pyyaml
python3 build.py
xdg-open dist/index.html
```

On other systems, install PyYAML with `python3 -m pip install pyyaml` instead (inside a virtual environment if pip refuses).

A normal run looks like this:

```
Read 25 products, 24 parts, 3 combiners, 32 wires
16 specs are blank and will be hidden on the page:
  jinko-tiger-neo-590: max_fuse_a
  ...
Wrote dist/index.html (305 KB)
```

If something doesn't line up, nothing is written and the build names the file and entry to fix:

```
Nothing was built. Fix this problem first:
  build.yaml part pv-d: product `cs-hiku7-60` isn't in products.yaml
```

Lines starting with `Note:` are worth a look but don't stop the build.

## Publishing on Cloudflare

The site runs as a Cloudflare Worker that serves `dist/` as static files; `wrangler.jsonc` holds that setting. Cloudflare watches this repository: every push to `main` makes it run `build.py`, then publish the result, usually within a minute or two. If a build fails, the live page stays as it was and the Worker's **Deployments** list shows why.

One-time setup in the Cloudflare dashboard:

1. Open **Workers & Pages**, click **Create application**, connect GitHub and pick this repository.
2. Set:
   - Project name: `project-anor` (it must match `name` in `wrangler.jsonc`)
   - Build command: `pip install pyyaml && python build.py`
   - Deploy command: `npx wrangler deploy`
   - Path (under Advanced settings): `sites/home-solar`
3. Click **Deploy**. The page is at `https://project-anor.bigbrovar-k3s.workers.dev/`.
4. In the Worker's **Settings → Build → Build watch paths**, set the include path to `sites/home-solar/*`, so changes elsewhere in the repository don't rebuild this site.

## License

The code (`template.html` and `build.py`) is under the MIT License; see `LICENSE` at the repository root. The data, writing and photos are under [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/): reuse them freely, with credit.

This is a write-up of one build, not an installation guide. Have your own design checked by a qualified installer.
