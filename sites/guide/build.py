#!/usr/bin/env python3
"""Build the Project Anor guide.

Reads data/guide.yaml, checks it, and writes dist/index.html: one
self-contained page with the data baked in.

    python3 build.py

Needs Python 3.8+ and PyYAML (on Fedora: sudo dnf install python3-pyyaml).
"""

import datetime
import json
import pathlib
import shutil
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
OUT = ROOT / "dist" / "index.html"
MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December")
STATES = {"kit", "live", "pending", "scope"}
SHOWN = {"kit", "live"}   # priced, and picked by the planner
errors = []


def problem(where, msg):
    errors.append(f"{where}: {msg}")


def is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def planner(block):
    """Check the planner settings and return them in the shape the page reads."""
    if not isinstance(block, dict):
        problem("planner", "is missing. It holds the states, price bands and sizing rules")
        return {}
    rules = block.get("rules") or {}
    limits = {"inverter_load": (0.3, 1), "battery_use": (0.3, 1), "battery_loss": (0, 0.3),
              "panel_losses": (0.4, 1), "own_surge": (1, 10), "days_in_month": (28, 31)}
    for key, (low, high) in limits.items():
        if not is_num(rules.get(key)) or not low <= rules[key] <= high:
            problem(f"planner.rules.{key}", f"should be a number from {low} to {high}")
    for key in rules:
        if key not in limits:
            problem(f"planner.rules.{key}", "isn't a rule the planner uses. Check the spelling")
    bands = []
    for i, band in enumerate(block.get("bands") or [], 1):
        if not isinstance(band, dict) or not band.get("name") or not is_num(band.get("price")) or band["price"] < 0:
            problem(f"planner.bands, entry {i}", "needs a name and a price (a number)")
            continue
        bands.append({"name": str(band["name"]), "price": band["price"]})
    when, when_ids = [], []
    for i, choice in enumerate(block.get("when") or [], 1):
        if (not isinstance(choice, dict) or not choice.get("id") or not choice.get("label")
                or not is_num(choice.get("night")) or not 0 <= choice["night"] <= 1):
            problem(f"planner.when, entry {i}", "needs an id, a label and night (a number from 0 to 1)")
            continue
        when.append({"id": str(choice["id"]), "label": str(choice["label"]), "night": choice["night"]})
        when_ids.append(str(choice["id"]))
    if not when:
        problem("planner.when", "needs at least one choice")
    states = block.get("states") or {}
    if not isinstance(states, dict) or not states:
        problem("planner.states", "should list each state with its sun hours")
        states = {}
    for name, s in states.items():
        if not (isinstance(s, dict) and all(is_num(s.get(k)) and 2 <= s[k] <= 8 for k in ("low", "yearly"))
                and s.get("month") in MONTHS and s["low"] <= s["yearly"]):
            problem(f"planner.states.{name}", "needs `low` and `yearly` (numbers from 2 to 8, low not above yearly) and `month` (a month name)")
    defaults = block.get("defaults") or {}
    if defaults.get("state") not in states:
        problem("planner.defaults.state", f"`{defaults.get('state')}` isn't in the states list")
    if not is_num(defaults.get("price")) or defaults["price"] < 0:
        problem("planner.defaults.price", "should be a number")
    if defaults.get("when") not in when_ids:
        problem("planner.defaults.when", f"`{defaults.get('when')}` isn't one of the ids under when")
    if not str(block.get("sun_note", "")).strip():
        problem("planner.sun_note", "is missing")
    return {"rules": {"invLoad": rules.get("inverter_load"), "batUse": rules.get("battery_use"),
                      "batLoss": rules.get("battery_loss"), "pvLoss": rules.get("panel_losses"),
                      "ownSurge": rules.get("own_surge"), "days": rules.get("days_in_month")},
            "bands": bands, "bandNote": str(block.get("band_note", "")), "when": when,
            "states": [[str(name), s.get("low"), s.get("month"), s.get("yearly")] for name, s in states.items() if isinstance(s, dict)],
            "sunNote": str(block.get("sun_note", "")),
            "defaults": {"state": defaults.get("state"), "price": defaults.get("price"), "when": defaults.get("when")}}


TICK = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" '
        'stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>')


def privacy_page(updated):
    """Write dist/privacy.html from data/privacy.yaml. Returns False if the page can't be built."""
    path, template = ROOT / "data" / "privacy.yaml", ROOT / "privacy.html"
    if not path.exists() or not template.exists():
        problem("privacy", "needs data/privacy.yaml and privacy.html. Every site's footer links to this page")
        return None
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        problem("data/privacy.yaml", f"isn't valid YAML: {e}")
        return None
    for key in ("title", "lead", "short", "sections"):
        if not doc.get(key):
            problem("data/privacy.yaml", f"`{key}` is missing")
    parts = ['  <ul class="short">' + "".join(f"<li>{TICK}<span>{line}</span></li>" for line in doc.get("short") or []) + "</ul>"]
    table = doc.get("table") or {}
    if table.get("rows"):
        head = "".join(f"<th scope=\"col\">{h}</th>" for h in table.get("head") or [])
        rows = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in table["rows"])
        parts.append(f'  <div class="tscroll"><table><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>')
    for i, s in enumerate(doc.get("sections") or [], 1):
        if not isinstance(s, dict) or not s.get("h") or not s.get("p"):
            problem(f"data/privacy.yaml sections, entry {i}", "needs a heading (h) and paragraphs (p)")
            continue
        parts.append(f"  <section><h2>{s['h']}</h2>" + "".join(f"<p>{para}</p>" for para in s["p"]) + "</section>")
    html = template.read_text(encoding="utf-8")
    plain = str(doc.get("lead", "")).replace('"', "&quot;")
    for key, value in {"__TITLE__": str(doc.get("title", "")), "__DESC__": plain, "__LEAD__": str(doc.get("lead", "")),
                       "__BODY__": "\n".join(parts), "__UPDATED__": str(updated)}.items():
        if key not in html:
            problem("privacy.html", f"should contain {key}")
        html = html.replace(key, value)
    return html


def main():
    path = ROOT / "data" / "guide.yaml"
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        sys.exit(f"data/guide.yaml isn't valid YAML, so nothing was built:\n{e}")

    prices = {}
    for pid, p in (doc.get("prices") or {}).items():
        where = f"prices.{pid}"
        if not isinstance(p, dict) or not p.get("name") or not is_num(p.get("price")):
            problem(where, "needs a name and a price (a number)")
            continue
        sources = [{"n": str(s["name"]), "u": str(s["url"])} for s in p.get("sources") or []
                   if isinstance(s, dict) and s.get("name") and s.get("url")]
        if not sources:
            problem(where, "needs at least one source with a name and a url")
        prices[pid] = {"n": str(p["name"]), "plain": str(p.get("plain", "")), "p": p["price"], "range": str(p.get("range", "")),
                       "note": str(p.get("note", "")), "src": sources}

    systems, ids = [], []
    for i, s in enumerate(doc.get("systems") or [], 1):
        where = f"systems, entry {i}"
        if not isinstance(s, dict) or not s.get("id") or not s.get("name"):
            problem(where, "needs an id and a name")
            continue
        where = f"systems.{s['id']}"
        if s.get("state") not in STATES:
            problem(where, "state should be kit, live, pending or scope")
        out = {"id": str(s["id"]), "n": str(s["name"]), "tag": str(s.get("tag", "")), "state": s.get("state"),
               "sys": str(s.get("sys", "")), "good": str(s.get("good", "")), "url": str(s.get("url", "")), "parts": []}
        if s.get("state") != "scope":
            for key in ("cont_w", "surge_w", "max_ac"):
                if not is_num(s.get(key)):
                    problem(where, f"`{key}` should be a number")
            sized = is_num(s.get("battery_kwh")) and is_num(s.get("pv_kwp"))
            if s.get("state") in SHOWN and not sized:
                problem(where, "a live system or kit needs `battery_kwh` and `pv_kwp`, both numbers")
            if not sized and not is_num(s.get("kwh_day")):
                problem(where, "needs `battery_kwh` and `pv_kwp`, or `kwh_day` for a design that isn't sized yet")
            for key in ("ac_at_once", "max_ac_2hp"):
                if s.get(key) is not None and not is_num(s[key]):
                    problem(where, f"`{key}` should be a number")
            out.update({"cont": s.get("cont_w"), "surge": s.get("surge_w"), "kwh": s.get("kwh_day"), "ac": s.get("max_ac"),
                        "acAt": s.get("ac_at_once", s.get("max_ac")), "ac2": s.get("max_ac_2hp", 0),
                        "idle": s.get("idle_w", 0) if is_num(s.get("idle_w", 0)) else 0})
            if sized:
                out.update({"bat": s["battery_kwh"], "pv": s["pv_kwp"]})
        if s.get("state") in SHOWN and not out["url"].startswith("https://"):
            problem(where, "a live system or kit needs the https:// url of its dashboard")
        if s.get("state") in SHOWN and not s.get("parts"):
            problem(where, "a live system or kit needs parts, for its reference price")
        if s.get("allowance_pct") is not None:
            if not is_num(s["allowance_pct"]) or not str(s.get("allowance_text", "")).strip():
                problem(where, "`allowance_pct` should be a number, with an `allowance_text` saying what it covers")
            else:
                out.update({"bosPct": s["allowance_pct"], "bosText": str(s["allowance_text"])})
        if s.get("state") == "kit":
            kit = s.get("kit") or {}
            notes = [str(n) for n in kit.get("notes") or [] if str(n).strip()]
            if not notes:
                problem(where, "a kit needs `kit.notes`: how it goes together and its limits")
            if not str(kit.get("manual", "")).startswith("https://"):
                problem(where, "a kit needs `kit.manual`, the https:// address of the maker's manual")
            out["kit"] = {"notes": notes, "alt": str(kit.get("alt", "")), "manual": str(kit.get("manual", ""))}
        for part in s.get("parts") or []:
            if not isinstance(part, dict) or part.get("price") not in prices or not is_num(part.get("qty")):
                problem(where, "each part needs price (an id from prices) and qty")
                continue
            out["parts"].append({"p": part["price"], "q": part["qty"]})
            area = (doc.get("prices") or {}).get(part["price"], {}).get("area_m2")
            if is_num(area):   # panels: count them and add up their area
                out["panels"] = out.get("panels", 0) + part["qty"]
                out["roof"] = round(out.get("roof", 0) + part["qty"] * area, 1)
        systems.append(out)
        ids.append(out["id"])
    if not any(s["state"] == "live" for s in systems):
        problem("systems", "needs at least one live system")

    apps = []
    for i, a in enumerate(doc.get("appliances") or [], 1):
        where = f"appliances, entry {i}"
        if not isinstance(a, dict) or not a.get("id") or not a.get("name") or not is_num(a.get("watts")):
            problem(where, "needs id, name and watts")
            continue
        where = f"appliances.{a['id']}"
        if not is_num(a.get("kwh_day")) and not is_num(a.get("hours")):
            problem(where, "needs hours, or kwh_day for something that cycles on and off")
        if a.get("needs") is not None and a["needs"] not in ids:
            problem(where, f"needs `{a['needs']}`, which isn't a system id")
        out = {"g": str(a.get("group", "")), "id": str(a["id"]), "i": str(a.get("icon", "zap")), "n": str(a["name"]),
               "w": a["watts"], "q": a.get("qty", 1), "on": bool(a.get("selected"))}
        for src, dst in (("surge_w", "s"), ("hours", "h"), ("kwh_day", "kd")):
            if is_num(a.get(src)):
                out[dst] = a[src]
        if a.get("ac"):
            out["ac"] = True
        if a.get("ac_2hp"):
            out["big"] = True
        if a.get("needs"):
            out["min"] = ids.index(a["needs"])
            out["why"] = str(a.get("why", ""))
        apps.append(out)

    plan = planner(doc.get("planner"))

    updated = doc.get("updated", "")
    if isinstance(updated, datetime.date):
        updated = f"{updated.day} {updated.strftime('%b %Y')}"
    privacy = privacy_page(updated)

    ref = doc.get("reference") or {}
    if not str(ref.get("url", "")).startswith("https://"):
        problem("reference", "needs its https:// url")
    if not is_num(doc.get("allowance_pct")):
        problem("allowance_pct", "should be a number")

    if errors:
        print(f"\nNothing was built. Fix {'this problem' if len(errors) == 1 else f'these {len(errors)} problems'} first:", file=sys.stderr)
        for msg in errors:
            print(f"  {msg}", file=sys.stderr)
        sys.exit(1)

    data = {"prices": prices, "systems": systems, "apps": apps, "plan": plan, "bos": doc["allowance_pct"],
            "bosText": str(doc.get("allowance_text", "")),
            "ref": {k: str(ref.get(k, "")) for k in ("name", "url", "sys", "text")},
            "audit": str(doc.get("audit_url", "")),
            "consult": {k: str((doc.get("consult") or {}).get(k, "")) for k in ("url", "label", "card", "tip")},
            "reading": [{k: str(r.get(k, "")) for k in ("title", "url", "text")} for r in doc.get("reading") or [] if isinstance(r, dict)]}
    html = (ROOT / "template.html").read_text(encoding="utf-8")
    fills = {"/*__DATA__*/": "const G=" + json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + ";",
             "__UPDATED__": str(updated)}
    for key, value in fills.items():
        if key not in html:
            sys.exit(f"template.html should contain {key}.")
        html = html.replace(key, value)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    (OUT.parent / "privacy.html").write_text(privacy, encoding="utf-8")
    # the link preview image (og:image) sits beside the page
    if (ROOT / "og.png").exists():
        shutil.copyfile(ROOT / "og.png", OUT.parent / "og.png")
    live = [s for s in systems if s["state"] in SHOWN]
    kits = sum(s["state"] == "kit" for s in live)
    print(f"Read {len(systems)} systems ({len(live) - kits} live, {kits} kits), {len(prices)} prices, {len(apps)} appliances")
    for s in live:
        parts = sum(prices[p["p"]]["p"] * p["q"] for p in s["parts"])
        print(f"  {s['n']}: about ₦{round(parts * (1 + s.get('bosPct', doc['allowance_pct']) / 100)):,}")
    print(f"Wrote {OUT.relative_to(ROOT)} ({round(OUT.stat().st_size / 1024)} KB)")
    print("Wrote dist/privacy.html")


if __name__ == "__main__":
    main()
