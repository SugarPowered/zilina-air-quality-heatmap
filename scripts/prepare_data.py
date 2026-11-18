"""Prepare air-quality data for the Žilina hotspot heatmap.

Sources
  local : archived exports in docs/ (Oct 2023 – 25 Mar 2026), no network needed
  api   : Žilina Open Data Portal (Invipo platform), https://opendata.zilina.sk

Outputs (data/)
  stations.csv          all environmental sensors + coordinates + status
  pm_hourly.csv.gz      cleaned hourly PM1/PM2.5/PM4/PM10 (+NO2/SO2/CO where measured)
  heatmap_points.csv    one row per sensor: location + aggregated metrics + QC flag
                        -> direct input for the heatmap (use rows with qc_ok == True)

Usage
  python scripts/prepare_data.py                                   # local archive
  python scripts/prepare_data.py --source api --start 2025-10-08 --end 2026-11-01
  python scripts/prepare_data.py --window 2025-10-08 2026-03-25    # aggregation window
  python scripts/prepare_data.py --update        # append only new hours from the API to data/
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS_DATA = ROOT / "docs/KLIMA_24/PROJEKT_25/Dáta"
LOCAL_STATIONS = DOCS_DATA / "udaje o staniciach + miesto.xlsx"
LOCAL_HISTORY = DOCS_DATA / "Enviromentalne_stanice/Enviromentalne Stanice Data/AirPollutionSensorsData.csv"

API = "https://opendata.zilina.sk/api/datasets"
API_STATIONS = f"{API}/v1/core/geojson/items"            # POST {"classes": "EnvironmentalSensor"}
API_HISTORY = f"{API}/v2/environment-monitoring/history"  # POST {"itemId": [...], "type": "hourly", "from", "to"}

POLLUTANTS = {"airPm1": "pm1", "airPm25": "pm25", "airPm4": "pm4", "airPm10": "pm10",
              "airNo2": "no2", "airSo2": "so2", "airCo": "co"}
BBOX = dict(lat=(49.13, 49.30), lon=(18.62, 18.86))       # Žilina city + surroundings
VALID_RANGE = (0, 1000)                                    # µg/m³, outside -> NaN
VALID_MAX = {"co": 30000}                                  # CO is legitimately > 1000 µg/m³
# Overlap of both networks (Agdata since 2023-10, Lightnet since 2025-10) in the local archive.
DEFAULT_WINDOW = ("2025-10-08", "2026-03-25")
GZIP = {"method": "gzip", "mtime": 0}   # deterministic bytes -> no git diff when data is unchanged
MIN_COVERAGE = 0.30        # share of hours with PM10 inside the window
PLAUSIBLE_MEAN_PM10 = (2, 150)
WHO_24H = {"pm25": 15, "pm10": 45}   # WHO 2021 daily guideline
EU_24H_PM10 = 50                       # EU / SK daily limit (35 exceedances/yr allowed)


# ---------------------------------------------------------------- stations
def _station_row(f: dict) -> dict:
    p = f.get("properties", {}).get("item", f.get("properties", {}))
    lon, lat = (f.get("geometry") or {}).get("coordinates", [None, None])[:2]
    meas = (p.get("meta") or {}).get("measurements") or []
    return dict(id=p.get("id"), name=p.get("name"), producer=p.get("producer"),
                lat=lat, lon=lon, measurements=",".join(meas),
                operating_status=p.get("operatingStatus"),
                system_status=(p.get("systemStatus") or {}).get("status"),
                address=p.get("address"))


def stations_api() -> pd.DataFrame:
    r = requests.post(API_STATIONS, json={"classes": "EnvironmentalSensor"}, timeout=60)
    r.raise_for_status()
    feats = r.json()
    feats = feats.get("features", feats) if isinstance(feats, dict) else feats
    rows = [_station_row(f) for f in feats]
    return pd.DataFrame([x for x in rows if x["id"]])


def stations_local() -> pd.DataFrame:
    x = pd.read_excel(LOCAL_STATIONS)
    coords = x["geometry_coordinates"].map(json.loads)
    return pd.DataFrame(dict(
        id=x["properties_id"], name=x["properties_item_name"], producer=x["properties_item_producer"],
        lat=coords.str[1], lon=coords.str[0],
        measurements=x["properties_item_meta_measurements"].fillna("[]").map(lambda s: ",".join(json.loads(s))),
        operating_status=x["properties_item_operatingStatus"],
        system_status=x["properties_item_systemStatus_status"],
        address=x["Adresa, Mesto"]))


def classify(st: pd.DataFrame) -> pd.DataFrame:
    st = st.copy()
    has_pm = st["measurements"].str.contains("airPm10", na=False)
    st["kind"] = "meteo_only"
    st.loc[has_pm & (st["producer"] == "Lightnet"), "kind"] = "lightnet_pm"      # low-cost PM on lamp posts
    st.loc[has_pm & (st["producer"] != "Lightnet"), "kind"] = "agdata_full"      # PM + NO2/SO2/CO + meteo
    st["in_bbox"] = st["lat"].between(*BBOX["lat"]) & st["lon"].between(*BBOX["lon"])
    st["dup_coord"] = st.duplicated(["lat", "lon"], keep=False)
    return st


# ---------------------------------------------------------------- history
EXIT_API_UNAVAILABLE = 75   # EX_TEMPFAIL: the daily job treats this as "skip quietly", not as an error


def check_api(sid: str) -> None:
    """Fail fast with a clear message instead of retrying 145 stations against a dead API.
    Exits with EXIT_API_UNAVAILABLE so callers can tell an outage from a real error."""
    now = datetime.now(timezone.utc)
    body = {"itemId": [sid], "type": "hourly",
            "from": (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S.000Z"),
            "to": now.strftime("%Y-%m-%d %H:%M:%S.000Z")}
    try:
        r = requests.post(API_HISTORY, json=body, timeout=60)
        r.raise_for_status()
        if not isinstance(r.json(), list):
            raise ValueError(f"unexpected response: {r.text[:200]}")
    except (requests.RequestException, ValueError) as e:
        print(f"Open Data API is not available ({e}). Existing data left unchanged.")
        raise SystemExit(EXIT_API_UNAVAILABLE)


def history_api(ids: list[str], start: str, end: str, chunk_days: int = 30) -> pd.DataFrame:
    """One request per station per chunk (the response carries no station id)."""
    out = []
    t0 = datetime.fromisoformat(start).replace(tzinfo=timezone.utc)
    t_end = datetime.fromisoformat(end).replace(tzinfo=timezone.utc)
    for i, sid in enumerate(ids, 1):
        t = t0
        while t < t_end:
            t2 = min(t + timedelta(days=chunk_days), t_end)
            body = {"itemId": [sid], "type": "hourly",
                    "from": t.strftime("%Y-%m-%d %H:%M:%S.000Z"), "to": t2.strftime("%Y-%m-%d %H:%M:%S.000Z")}
            for attempt in range(3):
                try:
                    r = requests.post(API_HISTORY, json=body, timeout=120)
                    r.raise_for_status()
                    rows = r.json()
                    break
                except requests.RequestException as e:
                    if attempt == 2:
                        print(f"  ! {sid} {body['from']}: {e}")
                        rows = []
                    time.sleep(2 * (attempt + 1))
            if rows:
                df = pd.DataFrame(rows)
                df["station_id"] = sid
                out.append(df)
            t = t2
        print(f"  [{i}/{len(ids)}] {sid}")
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def history_local() -> pd.DataFrame:
    return pd.read_csv(LOCAL_HISTORY, low_memory=False).rename(columns={"properties_id": "station_id"})


def clean_hourly(h: pd.DataFrame, pm_ids: set[str]) -> pd.DataFrame:
    h = h[h["station_id"].isin(pm_ids)].copy()
    h["timestamp"] = pd.to_datetime(h["timestamp"], utc=True)
    cols = [c for c in POLLUTANTS if c in h.columns]
    h = h[["timestamp", "station_id", *cols]].rename(columns=POLLUTANTS)
    vals = [POLLUTANTS[c] for c in cols]
    h[vals] = h[vals].apply(pd.to_numeric, errors="coerce")
    for v in vals:
        h[v] = h[v].where(h[v].between(VALID_RANGE[0], VALID_MAX.get(v, VALID_RANGE[1])))
    return h.dropna(subset=vals, how="all").drop_duplicates(["station_id", "timestamp"]).sort_values(
        ["station_id", "timestamp"])


# ---------------------------------------------------------------- aggregation
def aggregate(h: pd.DataFrame, st: pd.DataFrame, window: tuple[str, str]) -> pd.DataFrame:
    w0, w1 = (pd.Timestamp(d, tz="UTC") for d in window)
    w1 = w1 + pd.Timedelta(days=1)
    hw = h[(h["timestamp"] >= w0) & (h["timestamp"] < w1)]
    hours = (w1 - w0) / pd.Timedelta(hours=1)

    g = hw.groupby("station_id")
    agg = pd.DataFrame({
        "n_hours": g["pm10"].count(),
        "pm25_mean": g["pm25"].mean(), "pm10_mean": g["pm10"].mean(),
        "pm10_median": g["pm10"].median(), "pm10_p95": g["pm10"].quantile(0.95),
        "no2_mean": g["no2"].mean() if "no2" in hw else None,
    })
    agg["coverage"] = agg["n_hours"] / hours

    # daily means (>= 18 valid hours) -> exceedance days
    d = (hw.assign(day=hw["timestamp"].dt.floor("D"))
         .groupby(["station_id", "day"])
         .agg(pm25=("pm25", "mean"), pm25_n=("pm25", "count"), pm10=("pm10", "mean"), pm10_n=("pm10", "count"))
         .reset_index())
    ok10, ok25 = d[d["pm10_n"] >= 18], d[d["pm25_n"] >= 18]
    agg["valid_days"] = ok10.groupby("station_id").size()
    agg["days_pm10_gt_50_eu"] = ok10[ok10["pm10"] > EU_24H_PM10].groupby("station_id").size()
    agg["days_pm25_gt_15_who"] = ok25[ok25["pm25"] > WHO_24H["pm25"]].groupby("station_id").size()
    agg[["valid_days", "days_pm10_gt_50_eu", "days_pm25_gt_15_who"]] = (
        agg[["valid_days", "days_pm10_gt_50_eu", "days_pm25_gt_15_who"]].fillna(0).astype(int))
    agg["share_days_pm10_gt_50"] = agg["days_pm10_gt_50_eu"] / agg["valid_days"].replace(0, pd.NA)

    out = st[st["kind"] != "meteo_only"].merge(agg, left_on="id", right_index=True, how="left")
    reasons = []
    for _, r in out.iterrows():
        why = []
        if not r["in_bbox"]: why.append("outside_zilina")
        if pd.isna(r["coverage"]) or r["coverage"] < MIN_COVERAGE: why.append("low_coverage")
        elif not PLAUSIBLE_MEAN_PM10[0] <= r["pm10_mean"] <= PLAUSIBLE_MEAN_PM10[1]: why.append("implausible_values")
        reasons.append(";".join(why))
    out["qc_reason"] = reasons
    out["qc_ok"] = out["qc_reason"] == ""
    out["window"] = f"{window[0]}..{window[1]}"
    num = out.select_dtypes("float").columns
    out[num] = out[num].round(3)
    return out.sort_values("pm10_mean", ascending=False)


# ---------------------------------------------------------------- incremental update
RECENT_WINDOW_DAYS = 180   # heatmap_points window after an update: the last ~6 months


def update_recent() -> None:
    """Append hours newer than the committed data/ from the API. Needs no docs/ archive,
    so it also runs in GitHub Actions. Leaves data/ untouched if the API is down."""
    hourly_path, st_path = DATA / "pm_hourly.csv.gz", DATA / "stations.csv"
    if not hourly_path.exists() or not st_path.exists():
        raise SystemExit("data/ is empty. Run a full prepare first (local or --source api).")

    old_st = pd.read_csv(st_path)
    pm_ids = sorted(old_st.loc[old_st["kind"] != "meteo_only", "id"])
    check_api(pm_ids[0])

    try:   # refresh the station list (new sensors, status); keep known addresses
        st = classify(stations_api())
        st["address"] = st["address"].fillna(st["id"].map(old_st.set_index("id")["address"]))
        print(f"stations <- api ({len(st)})")
    except (requests.RequestException, ValueError) as e:
        print(f"  ! station list not refreshed ({e}), keeping data/stations.csv")
        st = old_st
    pm_ids = sorted(set(st.loc[st["kind"] != "meteo_only", "id"]))

    old = pd.read_csv(hourly_path, parse_dates=["timestamp"])
    start = (old["timestamp"].max() - pd.Timedelta(days=1)).strftime("%Y-%m-%d")   # 1-day overlap
    end = (datetime.now(timezone.utc) + timedelta(hours=1)).strftime("%Y-%m-%dT%H:00:00")
    print(f"history <- api {start} .. {end} ({len(pm_ids)} PM sensors)")
    new = clean_hourly(history_api(pm_ids, start, end, chunk_days=15), set(pm_ids))
    if new.empty:   # not an error: nothing new yet
        print("API returned no new measurements. Existing data left unchanged.")
        return

    h = (pd.concat([old, new], ignore_index=True)
         .drop_duplicates(["station_id", "timestamp"], keep="last")   # newer API values win
         .sort_values(["station_id", "timestamp"]))
    st.to_csv(st_path, index=False)
    h.to_csv(hourly_path, index=False, compression=GZIP)
    added = len(h) - len(old)
    print(f"hourly rows: {len(h):,} (+{added:,})  range: {h['timestamp'].min()} .. {h['timestamp'].max()}")

    last = h["timestamp"].max()
    window = ((last - pd.Timedelta(days=RECENT_WINDOW_DAYS)).strftime("%Y-%m-%d"), last.strftime("%Y-%m-%d"))
    pts = aggregate(h, st, window)
    pts.to_csv(DATA / "heatmap_points.csv", index=False)
    print(f"heatmap points: {pts['qc_ok'].sum()} usable / {len(pts)}  (window {window[0]}..{window[1]})")


# ---------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", choices=["local", "api"], default="local")
    ap.add_argument("--update", action="store_true",
                    help="append only new hours from the API to existing data/ (used by the daily job)")
    ap.add_argument("--start", default=DEFAULT_WINDOW[0], help="API download start (UTC date)")
    ap.add_argument("--end", default=datetime.now(timezone.utc).strftime("%Y-%m-%d"), help="API download end")
    ap.add_argument("--window", nargs=2, metavar=("FROM", "TO"), help="aggregation window (default: overlap)")
    a = ap.parse_args()
    DATA.mkdir(exist_ok=True)
    if a.update:
        return update_recent()

    print(f"stations <- {a.source}")
    if a.source == "api":
        try:
            st = classify(stations_api())
        except (requests.RequestException, ValueError) as e:
            raise SystemExit(f"Open Data API is not available ({e}).")
        check_api(st.loc[st["measurements"].str.contains("airPm10", na=False), "id"].iloc[0])
    else:
        st = classify(stations_local())
    st.to_csv(DATA / "stations.csv", index=False)
    print(st.groupby("kind").size().to_string())

    pm_ids = set(st.loc[st["kind"] != "meteo_only", "id"])
    print(f"history <- {a.source} ({len(pm_ids)} PM sensors)")
    raw = history_api(sorted(pm_ids), a.start, a.end) if a.source == "api" else history_local()
    h = clean_hourly(raw, pm_ids)
    h.to_csv(DATA / "pm_hourly.csv.gz", index=False, compression=GZIP)
    print(f"hourly rows: {len(h):,}  range: {h['timestamp'].min()} .. {h['timestamp'].max()}")

    window = tuple(a.window) if a.window else (DEFAULT_WINDOW if a.source == "local" else (a.start, a.end))
    pts = aggregate(h, st, window)
    pts.to_csv(DATA / "heatmap_points.csv", index=False)
    print(f"heatmap points: {pts['qc_ok'].sum()} usable / {len(pts)}  (window {window[0]}..{window[1]})")
    print(pts["qc_reason"].replace("", "ok").value_counts().to_string())


if __name__ == "__main__":
    main()
