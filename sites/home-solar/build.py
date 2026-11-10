#!/usr/bin/env python3
"""Build the Project Anor page.

Reads the YAML files in data/, checks them, and writes dist/index.html: one
self-contained page with the data and the install photo baked in.

    python3 build.py

Needs Python 3.8+ and PyYAML (on Fedora: sudo dnf install python3-pyyaml).
"""

import base64
import datetime
import json
import pathlib
import sys

try:
    import yaml
except ImportError:
    sys.exit(
        "PyYAML isn't installed.\n"
        "  Fedora:         sudo dnf install python3-pyyaml\n"
        "  Other systems:  python3 -m pip install pyyaml"
    )

ROOT = pathlib.Path(__file__).resolve().parent
DATA = ROOT / "data"
OUT = ROOT / "dist" / "index.html"

# Names the page knows how to draw. A new one also needs adding to CI or ICONS in template.html.
PART_ICONS = {"pv", "inverter", "mppt", "battery", "combiner", "fuse", "mcb", "mccb", "spd",
              "busbar", "shunt", "gx", "db", "meter", "grid", "home", "earth"}
LOAD_ICONS = {"lightbulb", "fan", "tv", "router", "laptop", "refrigerator", "air-vent",
              "droplets", "microwave", "flame", "thermometer"}
CATEGORIES = {"solar", "batt", "grid", "load", "hub", "none"}
WIRE_TYPES = {"solar", "batt", "grid", "load", "none", "data"}
DATA_BUSES = {"can", "mk3"}
MODE_BUTTONS = ("day", "night", "grid")  # the three buttons above the schematic

errors, notes = [], []


def problem(where, msg):
    errors.append(f"{where}: {msg}")


def note(where, msg):
    notes.append(f"{where}: {msg}")


def load(name):
    path = DATA / name
    if not path.exists():
        sys.exit(f"data/{name} is missing.")
    try:
        with path.open(encoding="utf-8") as f:
            doc = yaml.safe_load(f)
    except yaml.YAMLError as e:
        sys.exit(f"data/{name} isn't valid YAML, so nothing was built:\n{e}")
    if not isinstance(doc, dict):
        sys.exit(f"data/{name} should contain `key: value` entries at the top level.")
    return doc


def check_fields(where, entry, allowed):
    for key in entry:
        if key not in allowed:
            note(where, f"unknown field `{key}` was ignored (check the spelling)")


def as_list(value, where, field):
    if value is None:
        return []
    if not isinstance(value, list):
        problem(where, f"`{field}` should be a list")
        return []
    return value


def numbers(value, where, field, count):
    if (isinstance(value, list) and len(value) == count
            and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in value)):
        return value
    problem(where, f"`{field}` should be [{', '.join(['number'] * count)}]")
    return [0] * count


def entry_id(entry, where, i):
    if isinstance(entry, dict) and entry.get("id"):
        return str(entry["id"])
    problem(f"{where}, entry {i}", "needs an id")
    return None


# ---------- products.yaml ----------

PRODUCT_FIELDS = {"name", "short", "icon", "about", "specs", "note", "advice", "links", "brand", "why"}


def text_lines(value, where, field):
    """A line of text or a list of lines, returned as a list of strings."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list) and value and all(isinstance(v, str) for v in value):
        return list(value)
    problem(where, f"`{field}` should be a line of text or a list of lines. Put quotes around any line with a colon in it")
    return []


def read_brands(doc):
    brands = {}
    entries = doc.get("brands") or {}
    if not isinstance(entries, dict):
        problem("products.yaml", "`brands` should list brand ids, each with a why")
        return brands
    for bid, b in entries.items():
        where = f"products.yaml brands.{bid}"
        if not isinstance(b, dict):
            problem(where, "needs a why")
            continue
        check_fields(where, b, {"why"})
        brands[bid] = text_lines(b.get("why"), where, "why")
        if not brands[bid]:
            problem(where, "needs a why")
    return brands


def read_products(doc):
    brands, used_brands, no_why = read_brands(doc), set(), []
    labels = {}
    for key, val in (doc.get("spec_labels") or {}).items():
        if isinstance(val, list) and 1 <= len(val) <= 2 and val[0]:
            labels[key] = [str(val[0]), "" if len(val) < 2 or val[1] is None else str(val[1])]
        else:
            problem(f"products.yaml spec_labels.{key}", "should be [label, unit], for example [Power, W]")

    products, about, blanks = {}, {}, []
    entries = doc.get("products") or {}
    if not isinstance(entries, dict):
        problem("products.yaml", "`products` should list product ids, each with its details")
        entries = {}
    for pid, p in entries.items():
        where = f"products.yaml {pid}"
        if not isinstance(p, dict):
            problem(where, "should have fields like name, icon and specs")
            continue
        check_fields(where, p, PRODUCT_FIELDS)
        if not p.get("name"):
            problem(where, "needs a name")
        if p.get("icon") not in PART_ICONS:
            problem(where, f"icon `{p.get('icon')}` isn't one of: {', '.join(sorted(PART_ICONS))}")
        specs = p.get("specs") or {}
        if not isinstance(specs, dict):
            problem(where, "specs should be `key: value` pairs")
            specs = {}
        for key, val in specs.items():
            if key not in labels:
                note(where, f"spec `{key}` has no label in spec_labels, so the page shows the raw key")
            if val is None:
                blanks.append(f"{pid}: {key}")

        links = p.get("links") or {}
        if not isinstance(links, dict):
            problem(where, "links should have datasheet, buy and alternatives")
            links = {}
        out = {"datasheet": links.get("datasheet") or None, "buy": [], "alts": [], "read": []}
        for i, r in enumerate(as_list(links.get("read"), where, "links.read"), 1):
            if isinstance(r, dict) and r.get("title") and r.get("url"):
                out["read"].append({"t": str(r["title"]), "u": str(r["url"])})
            else:
                problem(where, f"read link {i} needs a title and a url")
        for i, b in enumerate(as_list(links.get("buy"), where, "links.buy"), 1):
            if isinstance(b, dict) and b.get("name") and b.get("url"):
                out["buy"].append({"s": str(b["name"]), "u": str(b["url"]), "aff": bool(b.get("affiliate"))})
            else:
                problem(where, f"buy link {i} needs a name and a url")
        for i, a in enumerate(as_list(links.get("alternatives"), where, "links.alternatives"), 1):
            if isinstance(a, dict) and a.get("name") and a.get("url"):
                alt = {"n": str(a["name"]), "u": str(a["url"]), "aff": bool(a.get("affiliate"))}
                if a.get("note"):
                    alt["note"] = str(a["note"])
                out["alts"].append(alt)
            else:
                problem(where, f"alternative {i} needs a name and a url")

        product = {"name": str(p.get("name", pid)), "icon": p.get("icon"), "specs": specs, "links": out}
        for field in ("short", "note", "advice"):
            if p.get(field):
                product[field] = str(p[field])
        why = []
        if p.get("brand") is not None:
            if p["brand"] in brands:
                why += brands[p["brand"]]
                used_brands.add(p["brand"])
            else:
                problem(where, f"brand `{p['brand']}` isn't in brands")
        why += text_lines(p.get("why"), where, "why")
        if why:
            product["why"] = why
        else:
            no_why.append(pid)
        products[pid] = product
        if p.get("about"):
            about[pid] = str(p["about"])
    for bid in brands:
        if bid not in used_brands:
            note(f"products.yaml brands.{bid}", "isn't used by any product")
    return labels, products, about, blanks, no_why


# ---------- build.yaml ----------

PART_FIELDS = {"id", "product", "qty", "series", "parallel", "layout", "feeds", "note", "show_on", "opens"}


def read_parts(doc, products):
    parts, by_id = [], {}
    for i, p in enumerate(as_list(doc.get("parts"), "build.yaml", "parts"), 1):
        pid = entry_id(p, "build.yaml parts", i)
        if not pid:
            continue
        where = f"build.yaml part {pid}"
        check_fields(where, p, PART_FIELDS)
        if pid in by_id:
            problem(where, "this id is used twice")
            continue
        if p.get("product") not in products:
            problem(where, f"product `{p.get('product')}` isn't in products.yaml")
        qty = p.get("qty")
        if qty is not None and (not isinstance(qty, int) or isinstance(qty, bool) or qty < 1):
            problem(where, "qty should be a whole number, or null if it varies")
        if "series" in p or "parallel" in p:
            s, n = p.get("series"), p.get("parallel")
            if not all(isinstance(v, int) and not isinstance(v, bool) and v > 0 for v in (s, n)):
                problem(where, "a panel array needs whole numbers for series and parallel")
            elif isinstance(qty, int) and s * n != qty:
                note(where, f"series × parallel is {s * n}, but qty is {qty}")
            if not p.get("feeds"):
                problem(where, "a panel array needs `feeds`: the part its strings connect to")
        part = {"id": pid, "product": p.get("product"), "qty": qty}
        for key in ("series", "parallel", "layout", "feeds", "note", "show_on", "opens"):
            if p.get(key) is not None:
                part[key] = p[key]
        parts.append(part)
        by_id[pid] = part
    for part in parts:
        if "feeds" in part and part["feeds"] not in by_id:
            problem(f"build.yaml part {part['id']}", f"feeds `{part['feeds']}`, which isn't a part")
    return parts, by_id


OTHER_FIELDS = {"title", "icon", "category", "about", "rows"}


def read_other_blocks(doc):
    info = {}
    for bid, b in (doc.get("other_blocks") or {}).items():
        where = f"build.yaml other_blocks.{bid}"
        if not isinstance(b, dict):
            problem(where, "should have title, icon, category, about and rows")
            continue
        check_fields(where, b, OTHER_FIELDS)
        if b.get("icon") not in PART_ICONS:
            problem(where, f"icon `{b.get('icon')}` isn't one of: {', '.join(sorted(PART_ICONS))}")
        rows = []
        for row in as_list(b.get("rows"), where, "rows"):
            if isinstance(row, list) and len(row) == 2:
                rows.append([str(row[0]), str(row[1])])
            else:
                problem(where, "each row should be [label, value]")
        info[str(bid)] = {"t": str(b.get("title", bid)), "icon": b.get("icon"),
                          "cat": b.get("category", "none"), "d": str(b.get("about", "")), "rows": rows}
    return info


def read_modes(doc, wire_ids):
    entries = doc.get("modes") or {}
    modes = {}
    for m in MODE_BUTTONS:
        if m not in entries:
            problem("build.yaml modes", f"needs a `{m}` entry, since it has a button on the page")
    for m, v in entries.items():
        where = f"build.yaml modes.{m}"
        if not isinstance(v, dict):
            problem(where, "should have caption, flowing and reversed")
            continue
        if m not in MODE_BUTTONS:
            note(where, "has no button on the page; add one to template.html to use it")
        flowing = as_list(v.get("flowing"), where, "flowing")
        reverse = as_list(v.get("reversed"), where, "reversed")
        for wid in flowing + reverse:
            if wid not in wire_ids:
                problem(where, f"wire `{wid}` isn't in layout.yaml")
        for wid in reverse:
            if wid not in flowing:
                note(where, f"wire `{wid}` is reversed but not flowing, so it won't show")
        modes[str(m)] = {"on": flowing, "rev": reverse, "cap": str(v.get("caption", ""))}
    return modes


def read_groups(doc, parts):
    groups, listed = [], set()
    for i, g in enumerate(as_list(doc.get("groups"), "build.yaml", "groups"), 1):
        where = f"build.yaml groups, entry {i}"
        if not isinstance(g, dict):
            problem(where, "should have a title and cards")
            continue
        cards = []
        for card in as_list(g.get("cards"), where, "cards"):
            card = card if isinstance(card, list) else [card]
            for pid in card:
                if pid not in parts:
                    problem(where, f"part `{pid}` isn't in build.yaml")
                listed.add(pid)
            cards.append(card)
        groups.append({"t": str(g.get("title", "")), "cards": cards})
    for pid in parts:
        if pid not in listed:
            note("build.yaml groups", f"part `{pid}` isn't in any group, so it won't appear in the parts list")
    return groups


def read_checks(doc, parts):
    c = doc.get("checks") or {}
    where = "build.yaml checks"
    cfg = {
        "battery": c.get("battery"),
        "inverters": as_list(c.get("inverters"), where, "inverters"),
        "chargers": as_list(c.get("chargers"), where, "chargers"),
        "charger_breakers": c.get("charger_breakers") or {},
        "low_battery_v": c.get("low_battery_v", 48),
        "inverter_efficiency": c.get("inverter_efficiency", 0.94),
    }
    if not isinstance(cfg["charger_breakers"], dict):
        problem(where, "charger_breakers should be `breaker part: charger part` pairs")
        cfg["charger_breakers"] = {}
    for pid in [cfg["battery"], *cfg["inverters"], *cfg["chargers"],
                *cfg["charger_breakers"].keys(), *cfg["charger_breakers"].values()]:
        if pid not in parts:
            problem(where, f"`{pid}` isn't a part in build.yaml")
    return cfg


# ---------- combiners.yaml ----------

COMBINER_FIELDS = {"title", "short", "part", "kind", "arrays", "string_protection", "surge_protector",
                   "lead", "channels", "to", "inside", "steps"}


def read_combiners(doc, products, parts):
    combiners = {}
    for cid, c in doc.items():
        where = f"combiners.yaml {cid}"
        if not isinstance(c, dict):
            problem(where, "should have fields like part, kind and arrays")
            continue
        check_fields(where, c, COMBINER_FIELDS)
        part = c.get("part")
        if part in parts:
            parts[part]["box"] = cid  # the part's card and block open this wiring view
        else:
            problem(where, f"part `{part}` isn't in build.yaml")
        kind = c.get("kind")
        if kind not in ("pair", "par3"):
            problem(where, "kind should be pair (one channel per array) or par3 (three strings joined)")
        arrays = as_list(c.get("arrays"), where, "arrays")
        for a in arrays:
            if a not in parts or "series" not in parts[a]:
                problem(where, f"array `{a}` isn't a panel array in build.yaml")

        prot = spd = None
        sp = c.get("string_protection")
        if sp not in products:
            problem(where, f"string_protection `{sp}` isn't in products.yaml")
        else:
            specs = products[sp]["specs"]
            key = "fuse_a" if "fuse_a" in specs else "current_a" if "current_a" in specs else None
            if key:
                prot = {"p": sp, "k": key, "what": "fuses" if products[sp]["icon"] == "fuse" else "breakers"}
            else:
                problem(where, f"string_protection `{sp}` needs a fuse_a or current_a spec")
        su = c.get("surge_protector")
        if su not in products:
            problem(where, f"surge_protector `{su}` isn't in products.yaml")
        elif "spd_v" not in products[su]["specs"]:
            problem(where, f"surge_protector `{su}` needs an spd_v spec")
        else:
            spd = {"p": su, "k": "spd_v"}

        inside = []
        for i, it in enumerate(as_list(c.get("inside"), where, "inside"), 1):
            prod = it.get("product") if isinstance(it, dict) else it
            if prod not in products:
                problem(where, f"inside, entry {i}: product `{prod}` isn't in products.yaml")
                continue
            inside.append({"p": prod, "qty": it.get("qty"), "on": str(it.get("where", ""))})

        combo = {"part": part, "kind": kind, "arrays": arrays, "prot": prot, "spd": spd,
                 "title": str(c.get("title", cid)), "short": str(c.get("short", "")),
                 "lead": str(c.get("lead", "")), "inside": inside,
                 "steps": [str(s) for s in as_list(c.get("steps"), where, "steps")]}
        if kind == "pair":
            channels = []
            for i, ch in enumerate(as_list(c.get("channels"), where, "channels"), 1):
                if isinstance(ch, dict) and ch.get("array") in arrays:
                    channels.append({"pv": ch["array"], "to": str(ch.get("to", ""))})
                else:
                    problem(where, f"channel {i} needs `array` set to one of: {', '.join(map(str, arrays))}")
            combo["channels"] = channels
        else:
            combo["to"] = str(c.get("to", ""))
        combiners[str(cid)] = combo
    return combiners


# ---------- boards.yaml ----------

BOARD_FIELDS = {"title", "part", "line", "lead", "feed", "chain", "outputs", "to", "steps"}
DEVICE_TYPES = {"mcb", "rcbo", "spd", "run"}


def read_boards(doc, parts):
    """The AC boards: the devices on the rail, in the order the supply passes through them."""
    boards = {}
    for bid, b in (doc or {}).items():
        where = f"boards.yaml {bid}"
        if not isinstance(b, dict):
            problem(where, "should have fields like part, feed and chain")
            continue
        check_fields(where, b, BOARD_FIELDS)
        part = b.get("part")
        if part in parts:
            parts[part]["board"] = bid  # the part's detail panel links to this wiring view
        else:
            problem(where, f"part `{part}` isn't in build.yaml")
        if b.get("line") not in ("grid", "load"):
            problem(where, "line should be grid (supply side) or load (inverter output side)")

        def device(d, what, i):
            if not isinstance(d, dict) or d.get("type") not in DEVICE_TYPES:
                problem(where, f"{what}, entry {i}: needs type mcb, rcbo, spd or run")
                return None
            return {k: str(v) for k, v in d.items() if k in ("type", "label", "sub", "to", "to_sub")}
        chain = [x for x in (device(d, "chain", i) for i, d in enumerate(as_list(b.get("chain"), where, "chain"), 1)) if x]
        outs = [x for x in (device(d, "outputs", i) for i, d in enumerate(as_list(b.get("outputs"), where, "outputs"), 1)) if x]
        if not chain or chain[0]["type"] not in ("mcb", "rcbo"):
            problem(where, "chain should start with a breaker")
        feed = b.get("feed")
        boards[str(bid)] = {"part": part, "title": str(b.get("title", bid)), "line": b.get("line"), "lead": str(b.get("lead", "")),
                            "feed": [str(x) for x in (feed if isinstance(feed, list) else [feed or ""])][:2],
                            "chain": chain, "outs": outs, "to": str(b.get("to", "")),
                            "steps": [str(x) for x in as_list(b.get("steps"), where, "steps")]}
    return boards


# ---------- layout.yaml ----------

BLOCK_FIELDS = {"id", "part", "short", "at", "title", "subtitle", "icon", "category", "style",
                "photo_height", "opens", "panels", "packs", "loads", "ports"}
WIRE_FIELDS = {"id", "from", "to", "type", "path", "pole", "bus", "cable", "label", "earth_at", "size", "length"}


def read_layout(doc, parts, combiners, other_blocks):
    w, h = numbers(doc.get("canvas"), "layout.yaml", "canvas", 2)

    nodes, node_ids = [], set()
    for i, b in enumerate(as_list(doc.get("blocks"), "layout.yaml", "blocks"), 1):
        bid = entry_id(b, "layout.yaml blocks", i)
        if not bid:
            continue
        where = f"layout.yaml block {bid}"
        check_fields(where, b, BLOCK_FIELDS)
        if bid in node_ids:
            problem(where, "this id is used twice")
            continue
        node_ids.add(bid)
        x, y, bw, bh = numbers(b.get("at"), where, "at", 4)
        if b.get("icon") not in PART_ICONS:
            problem(where, f"icon `{b.get('icon')}` isn't one of: {', '.join(sorted(PART_ICONS))}")
        n = {"id": bid, "x": x, "y": y, "w": bw, "h": bh,
             "t": str(b.get("title", "")), "s": str(b.get("subtitle", "")), "ic": b.get("icon")}
        if b.get("part"):
            if b["part"] in parts:
                n["part"] = b["part"]
            else:
                problem(where, f"part `{b['part']}` isn't in build.yaml")
        elif bid not in other_blocks:
            problem(where, f"has no part, so build.yaml needs an other_blocks entry for `{bid}`")
        if b.get("short"):
            n["short"] = str(b["short"])
        if b.get("category"):
            if b["category"] in CATEGORIES:
                n["cat"] = b["category"]
            else:
                problem(where, f"category should be one of: {', '.join(sorted(CATEGORIES))}")
        style = b.get("style", "tile")
        if style == "side":
            n["side"] = True
        elif style == "stack":
            n["stack"] = True
        elif style != "tile":
            problem(where, "style should be tile, side or stack")
        if b.get("photo_height") is not None:
            n["ph"] = b["photo_height"]
        if b.get("opens"):
            if b["opens"] in combiners:
                n["open"] = b["opens"]
            else:
                problem(where, f"opens `{b['opens']}`, which isn't in combiners.yaml")
        if b.get("panels"):
            panels = b["panels"] if isinstance(b["panels"], dict) else {}
            for src, dst in (("count", "count"), ("cols", "cols"), ("size", "isz")):
                if panels.get(src) is not None:
                    n[dst] = panels[src]
            if "count" not in n:
                problem(where, "panels needs at least a count")
        if b.get("packs"):
            n["slabs"] = b["packs"]
        if b.get("loads"):
            for load_icon in b["loads"]:
                if load_icon not in LOAD_ICONS:
                    problem(where, f"load icon `{load_icon}` isn't one of: {', '.join(sorted(LOAD_ICONS))}")
            n["loads"] = list(b["loads"])
        if b.get("ports"):
            n["ports"] = [[str(pt[0]), str(pt[1])] for pt in b["ports"] if isinstance(pt, list) and len(pt) == 2]
        nodes.append(n)

    wires, wire_ids = [], set()
    for i, wi in enumerate(as_list(doc.get("wires"), "layout.yaml", "wires"), 1):
        wid = entry_id(wi, "layout.yaml wires", i)
        if not wid:
            continue
        where = f"layout.yaml wire {wid}"
        check_fields(where, wi, WIRE_FIELDS)
        if wid in wire_ids:
            problem(where, "this id is used twice")
            continue
        wire_ids.add(wid)
        for end in ("from", "to"):
            if wi.get(end) not in node_ids and wi.get(end) != "earth":
                problem(where, f"`{end}: {wi.get(end)}` isn't a block on the drawing (or earth)")
        kind = wi.get("type")
        if kind not in WIRE_TYPES:
            problem(where, f"type should be one of: {', '.join(sorted(WIRE_TYPES))}")
        if not wi.get("path"):
            problem(where, "needs a path")
        wire = {"id": wid, "from": wi.get("from"), "to": wi.get("to"), "type": kind, "d": str(wi.get("path", ""))}
        if wi.get("pole") is not None:
            wire["pole"] = str(wi["pole"])
        if kind == "data":
            if wi.get("bus") not in DATA_BUSES:
                problem(where, "a data wire needs bus: can or mk3")
            wire.update(bus=wi.get("bus"), cable=str(wi.get("cable", "")), label=str(wi.get("label", "")))
        for key, short in (("size", "size"), ("length", "len")):
            if wi.get(key) is not None:
                wire[short] = str(wi[key])
        if wi.get("earth_at") is not None:
            wire["sym"] = numbers(wi["earth_at"], where, "earth_at", 2)
        wires.append(wire)

    labels = []
    for i, lab in enumerate(as_list(doc.get("labels"), "layout.yaml", "labels"), 1):
        where = f"layout.yaml labels, entry {i}"
        if not isinstance(lab, dict) or lab.get("text") is None:
            problem(where, "needs text")
            continue
        x, y = numbers(lab.get("at"), where, "at", 2)
        out = {"t": str(lab["text"]), "x": x, "y": y}
        if lab.get("anchor"):
            if lab["anchor"] in ("start", "middle", "end"):
                out["a"] = lab["anchor"]
            else:
                problem(where, "anchor should be start, middle or end")
        if lab.get("color"):
            if lab["color"] in DATA_BUSES:
                out["c"] = lab["color"]
            else:
                problem(where, "color should be can or mk3")
        labels.append(out)

    pins = []
    for i, pin in enumerate(as_list(doc.get("photo_pins"), "layout.yaml", "photo_pins"), 1):
        where = f"layout.yaml photo_pins, entry {i}"
        if not isinstance(pin, dict):
            problem(where, "should have block, at, title, where, icon and category")
            continue
        if pin.get("block") not in node_ids:
            problem(where, f"block `{pin.get('block')}` isn't on the drawing")
        if pin.get("icon") not in PART_ICONS:
            problem(where, f"icon `{pin.get('icon')}` isn't one of: {', '.join(sorted(PART_ICONS))}")
        x, y = numbers(pin.get("at"), where, "at", 2)
        pins.append({"node": pin.get("block"), "x": x, "y": y, "t": str(pin.get("title", "")),
                     "w": str(pin.get("where", "")), "ic": pin.get("icon"), "cat": pin.get("category", "hub")})

    return {"w": w, "h": h}, nodes, node_ids, wires, wire_ids, labels, pins


# ---------- battery.yaml ----------

BATTERY_FIELDS = {"title", "lead", "packs", "links", "runs", "runs_note", "steps", "busbar", "balance", "bms"}


def read_battery(doc):
    if doc is None:
        return None
    where = "battery.yaml"
    check_fields(where, doc, BATTERY_FIELDS)
    packs = [int(p) for p in as_list(doc.get("packs"), where, "packs")]
    if len(packs) < 2:
        problem(where, "packs should list at least two packs, top to bottom")
    out = {"title": str(doc.get("title", "Battery bank")), "lead": str(doc.get("lead", "")), "packs": packs,
           "steps": [str(x) for x in as_list(doc.get("steps"), where, "steps")],
           "runs_note": str(doc.get("runs_note", "")), "links": [], "runs": []}
    for i, ln in enumerate(as_list(doc.get("links"), where, "links"), 1):
        pair = ln.get("between") if isinstance(ln, dict) else None
        if not (isinstance(pair, list) and len(pair) == 2 and all(p in packs for p in pair)):
            problem(f"{where} links, entry {i}", "between should name two packs from `packs`")
            continue
        out["links"].append({"a": pair[0], "b": pair[1], "size": str(ln.get("size", "")), "len": str(ln.get("length", ""))})
    for i, rn in enumerate(as_list(doc.get("runs"), where, "runs"), 1):
        if not isinstance(rn, dict) or rn.get("pack") not in packs or str(rn.get("pole")) not in ("+", "-"):
            problem(f"{where} runs, entry {i}", "needs pack (from `packs`) and pole (+ or -)")
            continue
        out["runs"].append({"pack": rn["pack"], "pole": str(rn["pole"]), "size": str(rn.get("size", "")), "len": str(rn.get("length", ""))})
    bb = doc.get("busbar") or {}
    out["busbar"] = {"title": str(bb.get("title", "")), "text": str(bb.get("text", ""))}
    bal = doc.get("balance")
    if bal:
        out["balance"] = {k: bal.get(k) for k in ("total_a", "min_a", "max_a")}
        out["balance"]["text"] = str(bal.get("text", ""))
    bms = doc.get("bms") or {}
    out["bms"] = {"name": str(bms.get("name", "")), "role": [str(x) for x in as_list(bms.get("role"), where, "bms role")],
                  "cells": int(bms.get("cells_in_series") or 16), "volts": [], "currents": []}
    for v in as_list(bms.get("volts"), where, "bms volts"):
        if not isinstance(v, dict) or not isinstance(v.get("cell_v"), (int, float)):
            problem(f"{where} bms volts", "each entry needs label and a number for cell_v")
            continue
        out["bms"]["volts"].append({"label": str(v.get("label", "")), "v": float(v["cell_v"])})
    for c in as_list(bms.get("currents"), where, "bms currents"):
        if not isinstance(c, dict) or not isinstance(c.get("a"), (int, float)):
            problem(f"{where} bms currents", "each entry needs label and a number for a")
            continue
        out["bms"]["currents"].append({"label": str(c.get("label", "")), "a": c["a"]})
    return out


# ---------- build ----------

def main():
    product_doc, build_doc, combiner_doc, layout_doc = (
        load(name) for name in ("products.yaml", "build.yaml", "combiners.yaml", "layout.yaml"))

    labels, products, about, blanks, no_why = read_products(product_doc)
    part_list, parts = read_parts(build_doc, products)
    combiners = read_combiners(combiner_doc, products, parts)
    boards = read_boards(load("boards.yaml") if (DATA / "boards.yaml").exists() else None, parts)
    other_blocks = read_other_blocks(build_doc)
    canvas, nodes, node_ids, wires, wire_ids, diagram_labels, pins = read_layout(
        layout_doc, parts, combiners, other_blocks)
    modes = read_modes(build_doc, wire_ids)
    battery = read_battery(load("battery.yaml") if (DATA / "battery.yaml").exists() else None)
    groups = read_groups(build_doc, parts)
    checks = read_checks(build_doc, parts)
    short_names = build_doc.get("short_names") or {}
    for pid in short_names:
        if pid not in parts:
            note("build.yaml short_names", f"`{pid}` isn't a part")
    for part in part_list:
        where = f"build.yaml part {part['id']}"
        if "show_on" in part and part["show_on"] not in node_ids:
            problem(where, f"show_on `{part['show_on']}` isn't a block on the drawing")
        if "opens" in part and part["opens"] not in combiners:
            problem(where, f"opens `{part['opens']}`, which isn't in combiners.yaml")

    version = str(build_doc.get("version", ""))
    updated = build_doc.get("updated", "")
    if isinstance(updated, datetime.date):
        updated = f"{updated.day} {updated.strftime('%b %Y')}"

    for msg in notes:
        print(f"Note: {msg}")
    if errors:
        count = len(errors)
        print(f"\nNothing was built. Fix {'this problem' if count == 1 else f'these {count} problems'} first:",
              file=sys.stderr)
        for msg in errors:
            print(f"  {msg}", file=sys.stderr)
        sys.exit(1)

    combiner_photo = ROOT / "combiner.png"
    template_path, photo, busbar_photo = ROOT / "template.html", ROOT / "install.jpg", ROOT / "busbar.jpg"
    for path in (template_path, photo):
        if not path.exists():
            sys.exit(f"{path.name} is missing.")
    html = template_path.read_text(encoding="utf-8")

    data = {"LABELS": labels, "PRODUCTS": products, "ABOUT": about, "PARTS": part_list, "GROUPS": groups,
            "SHORT": short_names, "COMBINERS": combiners, "WIRING": wires, "NODES": nodes, "INFO": other_blocks,
            "MODES": modes, "SPOTS": pins, "LABS": diagram_labels, "CANVAS": canvas, "CHECKCFG": checks,
            "BATTERY": battery, "BOARDS": boards}
    script = "\n".join(f"const {name}={json.dumps(value, ensure_ascii=False, separators=(',', ':'))};"
                       for name, value in data.items()).replace("</", "<\\/")
    fills = {"__VERSION__": version, "__UPDATED__": str(updated),
             "__CANVAS_W__": str(canvas["w"]), "__CANVAS_H__": str(canvas["h"]),
             "__INSTALL_IMG__": "data:image/jpeg;base64," + base64.b64encode(photo.read_bytes()).decode("ascii"),
             "__BUSBAR_IMG__": ("data:image/jpeg;base64," + base64.b64encode(busbar_photo.read_bytes()).decode("ascii"))
                               if busbar_photo.exists() else "",
             "__COMBINER_IMG__": ("data:image/png;base64," + base64.b64encode(combiner_photo.read_bytes()).decode("ascii"))
                                 if combiner_photo.exists() else "",
             "/*__DATA__*/": script}
    for key in fills:
        if html.count(key) != 1:
            sys.exit(f"template.html should contain {key} exactly once, but it appears {html.count(key)} times.")
    for key, value in fills.items():
        html = html.replace(key, value)

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    print(f"Read {len(products)} products, {len(part_list)} parts, {len(combiners)} combiners, {len(wires)} wires")
    if blanks:
        print(f"{len(blanks)} specs are blank and will be hidden on the page:")
        for blank in blanks:
            print(f"  {blank}")
    if no_why:
        print(f"{len(no_why)} products have no why yet:")
        for pid in no_why:
            print(f"  {pid}")
    print(f"Wrote {OUT.relative_to(ROOT)} ({round(OUT.stat().st_size / 1024)} KB)")


if __name__ == "__main__":
    main()
