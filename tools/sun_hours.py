#!/usr/bin/env python3
"""Fetch good sun hours for every Nigerian state from NASA POWER.

For each state capital this asks NASA's POWER service for the long-term
average of sunlight reaching a flat surface (ALLSKY_SFC_SW_DWN), in kWh per
square metre a day. That is the same thing as "good sun hours a day".

It writes data/sun-hours.csv with the yearly average, each month, and the
lowest month. The planner's state list is filled in from that file by hand.

Run it with:  python3 tools/sun_hours.py
It needs only Python 3 and an internet connection. No account or key.
Source: https://power.larc.nasa.gov (NASA Langley Research Center, POWER project).
"""
import csv
import json
import pathlib
import sys
import time
import urllib.request

API = ("https://power.larc.nasa.gov/api/temporal/climatology/point"
       "?parameters=ALLSKY_SFC_SW_DWN&community=RE&longitude={lon}&latitude={lat}&format=JSON")
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "sun-hours.csv"

# state, capital, latitude, longitude of the capital
PLACES = [
    ("Abia", "Umuahia", 5.53, 7.49), ("Adamawa", "Yola", 9.21, 12.48), ("Akwa Ibom", "Uyo", 5.04, 7.91),
    ("Anambra", "Awka", 6.21, 7.07), ("Bauchi", "Bauchi", 10.31, 9.84), ("Bayelsa", "Yenagoa", 4.92, 6.26),
    ("Benue", "Makurdi", 7.73, 8.54), ("Borno", "Maiduguri", 11.85, 13.16), ("Cross River", "Calabar", 4.96, 8.33),
    ("Delta", "Asaba", 6.20, 6.73), ("Ebonyi", "Abakaliki", 6.32, 8.11), ("Edo", "Benin City", 6.34, 5.63),
    ("Ekiti", "Ado Ekiti", 7.62, 5.22), ("Enugu", "Enugu", 6.44, 7.50), ("FCT, Abuja", "Abuja", 9.06, 7.49),
    ("Gombe", "Gombe", 10.29, 11.17), ("Imo", "Owerri", 5.48, 7.03), ("Jigawa", "Dutse", 11.76, 9.34),
    ("Kaduna", "Kaduna", 10.52, 7.44), ("Kano", "Kano", 12.00, 8.52), ("Katsina", "Katsina", 12.99, 7.60),
    ("Kebbi", "Birnin Kebbi", 12.45, 4.20), ("Kogi", "Lokoja", 7.80, 6.74), ("Kwara", "Ilorin", 8.50, 4.55),
    ("Lagos", "Ikeja", 6.60, 3.35), ("Nasarawa", "Lafia", 8.49, 8.52), ("Niger", "Minna", 9.61, 6.56),
    ("Ogun", "Abeokuta", 7.16, 3.35), ("Ondo", "Akure", 7.25, 5.19), ("Osun", "Osogbo", 7.77, 4.56),
    ("Oyo", "Ibadan", 7.38, 3.90), ("Plateau", "Jos", 9.92, 8.89), ("Rivers", "Port Harcourt", 4.82, 7.03),
    ("Sokoto", "Sokoto", 13.06, 5.24), ("Taraba", "Jalingo", 8.89, 11.36), ("Yobe", "Damaturu", 11.75, 11.96),
    ("Zamfara", "Gusau", 12.17, 6.66),
]


def fetch(lat, lon, tries=4):
    """One place's monthly and yearly averages, or None if NASA doesn't answer."""
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(API.format(lat=lat, lon=lon), timeout=60) as reply:
                doc = json.load(reply)
            values = doc["properties"]["parameter"]["ALLSKY_SFC_SW_DWN"]
            if all(values.get(k, -1) >= 0 for k in MONTHS + ["ANN"]):   # NASA marks a gap as -999
                return values
        except Exception as error:   # a timeout or a busy server: wait and try again
            print(f"    try {attempt + 1} failed: {error}", file=sys.stderr)
        time.sleep(5 * (attempt + 1))
    return None


def main():
    rows, missing = [], []
    for state, capital, lat, lon in PLACES:
        values = fetch(lat, lon)
        if values is None:
            missing.append(state)
            continue
        low = min(MONTHS, key=lambda m: values[m])
        rows.append([state, capital, lat, lon, f"{values['ANN']:.2f}", low, f"{values[low]:.2f}"]
                    + [f"{values[m]:.2f}" for m in MONTHS])
        print(f"{state:13} {capital:13} yearly {values['ANN']:.2f}   lowest {low} {values[low]:.2f}")
        time.sleep(1)   # be gentle with a free service
    if missing:
        sys.exit("NASA did not answer for: " + ", ".join(missing) + ". Nothing was written. Run it again.")
    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        f.write("# Good sun hours a day (kWh per square metre a day on a flat surface) at each state capital.\n")
        f.write("# Long-term averages from NASA POWER, parameter ALLSKY_SFC_SW_DWN. Written by tools/sun_hours.py.\n")
        out = csv.writer(f)
        out.writerow(["state", "capital", "lat", "lon", "yearly", "lowest_month", "lowest"] + [m.lower() for m in MONTHS])
        out.writerows(rows)
    print(f"Wrote {OUT.relative_to(OUT.parent.parent)} with {len(rows)} states")


if __name__ == "__main__":
    main()
