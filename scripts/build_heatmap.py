"""Build heatmap/data.js (daily means per sensor) for heatmap/index.html.

Run after scripts/prepare_data.py:
  python scripts/build_heatmap.py
Then serve the folder (OpenStreetMap tiles need an http Referer):
  python -m http.server -d heatmap 8000   ->  http://localhost:8000
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "heatmap" / "data.js"

MIN_HOURS_PER_DAY = 18           # a daily mean needs >= 75 % of hours
EXCLUDE_QC = ("implausible_values", "outside_zilina")   # low coverage is fine: valid days still count

# WHO 2021 Air Quality Guidelines, 24-hour (99th percentile) values, µg/m³.
# PM1 and PM4 have no WHO guideline -> proxy = guideline of the smallest regulated fraction that
# contains them (PM1 ⊂ PM2.5, PM4 ⊂ PM10). Flagged as proxy in the UI.
GUIDELINES = {
    "pm1":  {"label": "PM1",   "who": 15,   "proxy": "odporúčaná hodnota pre PM2.5 (PM1 je súčasťou PM2.5)"},
    "pm25": {"label": "PM2.5", "who": 15,   "proxy": None},
    "pm4":  {"label": "PM4",   "who": 45,   "proxy": "odporúčaná hodnota pre PM10 (PM4 je súčasťou PM10)"},
    "pm10": {"label": "PM10",  "who": 45,   "proxy": None},
    "no2":  {"label": "NO₂",   "who": 25,   "proxy": None},
    "so2":  {"label": "SO₂",   "who": 40,   "proxy": None},
    "co":   {"label": "CO",    "who": 4000, "proxy": None},
}


def main() -> None:
    pts = pd.read_csv(DATA / "heatmap_points.csv", keep_default_na=False)
    bad = pts["qc_reason"].str.contains("|".join(EXCLUDE_QC))
    st = pts[~bad].reset_index(drop=True)
    st["area"] = st["address"].str.split(", ").map(
        lambda a: ", ".join([x for x in a if x and not x[0].isdigit() and x != "Žilina"][:2]))
    idx = {sid: i for i, sid in enumerate(st["id"])}

    h = pd.read_csv(DATA / "pm_hourly.csv.gz", parse_dates=["timestamp"])
    h = h[h["station_id"].isin(idx)]
    # Daily mean in local time (Europe/Bratislava), so a "day" matches what residents experience.
    h["day"] = h["timestamp"].dt.tz_convert("Europe/Bratislava").dt.strftime("%Y-%m-%d")

    long = h.melt(id_vars=["station_id", "day"], value_vars=list(GUIDELINES), var_name="p").dropna()
    d = long.groupby(["p", "station_id", "day"])["value"].agg(["mean", "count"]).reset_index()
    d = d[d["count"] >= MIN_HOURS_PER_DAY]

    days = sorted(d["day"].unique())
    day_i = {x: i for i, x in enumerate(days)}
    values = {p: [] for p in GUIDELINES}
    for r in d.itertuples(index=False):
        values[r.p].append([day_i[r.day], idx[r.station_id], round(float(r.mean), 1)])

    payload = {
        "generated_from": "Žilina Open Data Portal (Invipo), hourly history -> daily means",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        "last_measurement": h["timestamp"].max().strftime("%Y-%m-%dT%H:%MZ"),
        "min_hours_per_day": MIN_HOURS_PER_DAY,
        "guidelines": GUIDELINES,
        "days": days,
        "stations": [
            {"name": r.name, "kind": r.kind, "lat": round(r.lat, 6), "lon": round(r.lon, 6), "area": r.area}
            for r in st.itertuples(index=False)
        ],
        "values": values,   # pollutant -> [[dayIndex, stationIndex, dailyMean µg/m³], ...]
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("window.AQ_DATA = " + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n",
                   encoding="utf-8")
    print(f"{OUT.relative_to(ROOT)}: {len(st)} sensors, {len(days)} days ({days[0]} .. {days[-1]}), "
          f"{sum(len(v) for v in values.values()):,} sensor-days, {OUT.stat().st_size / 1e6:.1f} MB")
    for p, v in values.items():
        print(f"  {p:5s} {len(v):7,} sensor-days")


if __name__ == "__main__":
    main()
