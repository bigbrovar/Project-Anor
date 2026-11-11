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
STATES = {"live", "pending", "scope"}
errors = []


def problem(where, msg):
    errors.append(f"{where}: {msg}")


def is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


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
        prices[pid] = {"n": str(p["name"]), "p": p["price"], "range": str(p.get("range", "")),
                       "note": str(p.get("note", "")), "src": sources}

    systems, ids = [], []
    for i, s in enumerate(doc.get("systems") or [], 1):
        where = f"systems, entry {i}"
        if not isinstance(s, dict) or not s.get("id") or not s.get("name"):
            problem(where, "needs an id and a name")
            continue
        where = f"systems.{s['id']}"
        if s.get("state") not in STATES:
            problem(where, "state should be live, pending or scope")
        out = {"id": str(s["id"]), "n": str(s["name"]), "tag": str(s.get("tag", "")), "state": s.get("state"),
               "sys": str(s.get("sys", "")), "good": str(s.get("good", "")), "url": str(s.get("url", "")), "parts": []}
        if s.get("state") != "scope":
            for key in ("cont_w", "surge_w", "kwh_day", "max_ac"):
                if not is_num(s.get(key)):
                    problem(where, f"`{key}` should be a number")
            for key in ("ac_at_once", "max_ac_2hp"):
                if s.get(key) is not None and not is_num(s[key]):
                    problem(where, f"`{key}` should be a number")
            out.update({"cont": s.get("cont_w"), "surge": s.get("surge_w"), "kwh": s.get("kwh_day"), "ac": s.get("max_ac"),
                        "acAt": s.get("ac_at_once", s.get("max_ac")), "ac2": s.get("max_ac_2hp", 0)})
        if s.get("state") == "live":
            if not out["url"].startswith("https://"):
                problem(where, "a live system needs its https:// url")
            if not s.get("parts"):
                problem(where, "a live system needs parts, for its reference price")
        for part in s.get("parts") or []:
            if not isinstance(part, dict) or part.get("price") not in prices or not is_num(part.get("qty")):
                problem(where, "each part needs price (an id from prices) and qty")
                continue
            out["parts"].append({"p": part["price"], "q": part["qty"]})
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

    updated = doc.get("updated", "")
    if isinstance(updated, datetime.date):
        updated = f"{updated.day} {updated.strftime('%b %Y')}"
    data = {"prices": prices, "systems": systems, "apps": apps, "bos": doc["allowance_pct"],
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
    # the link preview image (og:image) sits beside the page
    if (ROOT / "og.png").exists():
        shutil.copyfile(ROOT / "og.png", OUT.parent / "og.png")
    live = [s for s in systems if s["state"] == "live"]
    print(f"Read {len(systems)} systems ({len(live)} live), {len(prices)} prices, {len(apps)} appliances")
    for s in live:
        parts = sum(prices[p["p"]]["p"] * p["q"] for p in s["parts"])
        print(f"  {s['n']}: about ₦{round(parts * (1 + doc['allowance_pct'] / 100)):,}")
    print(f"Wrote {OUT.relative_to(ROOT)} ({round(OUT.stat().st_size / 1024)} KB)")


if __name__ == "__main__":
    main()
