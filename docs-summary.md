# Docs summary: prep for the Žilina air-pollution hotspot heatmap

> Source of truth: `docs/KLIMA_24/` (FRI UNIZA student project KLIMA, 2024 to 2026).
> Prepared data: `data/` via [scripts/prepare_data.py](scripts/prepare_data.py).

## 1. What is in `docs/`

| Folder | Content | Use for heatmap |
|---|---|---|
| `PROJEKT_24/` (2024/25) | Literature reviews, Projekt 1–3 reports, Kalman imputation (R), SARIMA/ARIMAX on Košická, first article | Methods and context. **Data is old (8 stations, weekly manual exports).** |
| `PROJEKT_24/Dáta mesto/` | `data_doplnene.csv`, `LEGENDA_DATA.xlsx` (column codes), `referencne_udaje.xlsx` (SHMÚ bands), `kalman.R` | Limits and legend |
| `PROJEKT_25/Dáta/` (2025/26) | **Main dataset.** Station list, hourly history of 155 sensors, Open Data API scripts, blind-spot clustering (`hluche_miesta/`) | **Primary input** |
| `PROJEKT_25/PUBLIKOVANIE_LETO 2026/` | Analytical article (EAQI per 20 city districts), review article (Danko/Mikuš/Šubert) | Methodology |
| `PROJEKT_25/Zápisy zo stretnutí/` | Meeting notes, including city priorities | Scope and hotspots to check |
| `PROJEKT_26/` | Draft about spatial clustering of PM2.5 networks (k-means, Voronoi, CSI) | Method ideas |
| Root PDFs | Theses (Benešová, Pinková), SHMÚ AG/MMSKO 2024–25 report | Background |

## 2. Data sources

**API** (Invipo platform, Žilina Open Data Portal, live since end of 2025):

| Dataset | Endpoint | Body |
|---|---|---|
| Station list (GeoJSON) | `POST https://opendata.zilina.sk/api/datasets/v1/core/geojson/items` | `{"classes":"EnvironmentalSensor"}` |
| Hourly history | `POST https://opendata.zilina.sk/api/datasets/v2/environment-monitoring/history` | `{"itemId":[id],"type":"hourly","from":"YYYY-MM-DD HH:MM:SS.000Z","to":…}` |

The history response has **no station id**, so request one station per call. Other relevant datasets on the portal: traffic counts (`pocet-vozidiel-za-hodinu`, detector loads), daily weather averages, population by street (`pocet-obcanov-podla-ulic`), schools.

**Sensor network** (155 devices):

| Kind | # | Measures | Since | Note |
|---|---|---|---|---|
| Agdata full station | 8 | PM1/2.5/4/10, NO₂, SO₂, CO + meteo | 2023-10-04 | Reference-like backbone |
| Agdata meteo-only | 10 | wind, T, p, RH, rain | 2023-10 | No pollutants |
| **Lightnet SMART** (lamp posts) | 137 | PM1/2.5/4/10, noise, T, RH | **2025-10-07** | Low-cost optical, dense |

8 full stations: autobusová stanica, Košická/Nemocničná, Kuzmányho, park Ľ. Štúra, Hájik, Vlčince, Brodno, Žilinská Lehota.
**No O₃ is measured anywhere.**

**Local archive:** `AirPollutionSensorsData.csv` (all sensors, 2023-10-04 to 2026-03-25, hourly), `udaje o staniciach + miesto.xlsx` (coordinates plus reverse-geocoded address and district), `ALL_snimace_summary.xlsx` (missing-data stats).

## 3. Key findings from previous work

- **Traffic:** Košická street and junctions have higher NO₂ and PM. NO₂ peaks at rush hours.
- **Heating:** PM10 is high on winter evenings and weekends because of solid-fuel heating. **Brodno and its surroundings have no gas pipeline** (city input), but no map of these areas exists yet. That gap is the main motivation for a heatmap.
- **Meteorology:** inversions and low wind cause pollution episodes. Rain lowers PM.
- **Smart Žilina portal** shows one opaque index for the whole city and only a few stations. Proposed fix: **EAQI per 20 city districts** (worst pollutant wins).
- **Data gaps:** a periodic missing hour (23:00, also 19:00) and multi-day/week outages caused by calibration, theft, faults or service. Over the years, trees and new buildings bias some sensors. Gaps were filled with Kalman imputation (`imputeTS::na_kalman`, auto.arima/StructTS heuristic).
- **Earlier models:** SARIMA(1,0,3)(1,0,0)₇ for rain, log-SARIMA for traffic, SARIMA(1,0,1)(2,1,2)₂₄ for NO₂, ARIMAX and causal models for weather → traffic.
- **City priority locations** (meetings 12.11.2025 and 18.03.2026): Košická junction and the Strážov direction (Višňové tunnel), Solinky/Hájik (parking policy, motorway feeder), Kysucká underpass, school zones (ZŠ Kráľovnej pokoja, Predmestská, Na Závaží), the railway station and new bridge, Brodno (solid fuel).
- **Blind spots:** `hluche_miesta/` has k-means, DBSCAN and agglomerative coverage maps plus proposed new sensor sites.

⚠️ The PROJEKT_24 article *"Kvalita ovzdušia mesta Žilina"* claims O₃ results ("ozone paradox"), "five zones" and full-2024 coverage. The sensors measure no O₃, so **do not cite those claims**.

## 4. Thresholds (µg/m³)

| | PM2.5 | PM10 | NO₂ |
|---|---|---|---|
| EU/SK limit, 24 h | – | 50 (max 35 days/yr) | 200 (1 h) |
| EU/SK limit, annual | 25 | 40 | 40 |
| WHO 2021, 24 h / annual | 15 / 5 | 45 / 15 | 25 / 10 |
| SHMÚ index, 1 h ("dobrá" up to) | 25 | 40 | 40 |
| EAQI bands | 0-5-15-50-90-140 | 0-15-45-120-195-270 | 0-10-25-60-100-150 |

## 5. Prepared data

```bash
pip install -r requirements.txt
python scripts/prepare_data.py                                         # from docs/ archive
python scripts/prepare_data.py --source api --start 2025-10-08 --end 2026-11-18   # fresh data
```

| File | Content |
|---|---|
| `data/stations.csv` | 155 sensors: id, name, kind, lat/lon, address, status, `in_bbox`, `dup_coord` |
| `data/pm_hourly.csv.gz` | 414k cleaned hourly rows (PM1/2.5/4/10, NO₂/SO₂/CO). Values outside 0–1000 are set to NaN. |
| `data/heatmap_points.csv` | **Heatmap input.** One row per PM sensor: mean/median/p95 PM, EU/WHO exceedance days, coverage, `qc_ok`, `qc_reason` |

**Default window: 2025-10-08 to 2026-03-25.** This is the only period where both networks overlap, and it is the heating season, so results are biased toward winter.

QC result: **102 of 145 sensors usable.** Excluded: 41 with coverage under 30 %, 1 with implausible values (mean ≈ 780), 1 outside Žilina (Handlová). Median coverage is 66 %.

**First hotspots** (mean over the window):

| Sensor | Area | PM10 | PM2.5 | Days PM10 > 50 |
|---|---|---|---|---|
| LN 43 #16 | Zvolenská, Vlčince | 91 | 86 | 66/83 |
| LN 42 #2 | Dolná Trnovská, Trnové | 87 | 83 | 69/85 |
| LN 41 #6 | Rajčianska, Strážov | 78 | 76 | 43/83 |
| LN 31 #2 | Daxnerova, Hliny VIII | 65 | 64 | 34/75 |
| LN 27 #3/#4/#6 | Budatín | 55–64 | 53–61 | ~40 % of days |
| LN 37 #1 | Bytčianska, Považský Chlmec | 59 | 54 | 48/107 |
| autobusová stanica (Agdata) | Staré mesto | 56 | 51 | **72/132** |

The cleanest sensors are in Zádubnie, Zástranie and Bytčica (PM10 5–10). Among the Agdata stations, Kuzmányho and Brodno are the lowest (28 and 30). Most hotspots are in family-house outskirts (Trnové, Strážov, Budatín, Považský Chlmec), which fits the solid-fuel heating explanation. Treat this as a hypothesis to test.

## 6. Caveats for the heatmap

1. **Lightnet sensors are uncalibrated low-cost optical sensors.** PM2.5 ≈ PM10 (no real size separation) and readings are humidity-sensitive. 3 sensors have p95 above 250. Either calibrate them against the nearest Agdata station or show the two networks as separate layers.
2. **Coordinates:** 14 duplicate coordinates and 1 sensor outside Žilina. The team planned to fix coordinates (task from 11.03.2026), so check them before interpolating.
3. **Season bias:** Lightnet data starts in Oct 2025. Pull data from the API after 03/2026 to get a summer or full-year comparison.
4. **Interpolation:** with about 100 points, use IDW or kriging inside the city boundary. Do not draw values beyond the sensor hull or across the river valleys. District-level EAQI is the robust alternative.

## 7. Heatmap

```bash
python scripts/prepare_data.py && python scripts/build_heatmap.py
python -m http.server -d heatmap 8000      # open http://localhost:8000 (OSM tiles need http, not file://)
```

- [heatmap/index.html](heatmap/index.html) uses Leaflet, OpenStreetMap tiles, and `heatmap/data.js`, which holds daily means for 143 sensors over 814 days.
- Each pollutant is a switchable layer. The colour shows the daily mean ÷ the WHO 2021 24-h guideline, on a diverging log scale from 0.25× to 4×, centred at 1× (blue below, red above).
- A day slider with play controls picks the day. The map shows the sensor points, a hover tooltip, and a table of that day's values.
- PM1 and PM4 have no WHO guideline, so they use the PM2.5 and PM10 guidelines as a proxy, flagged in the UI.
- The surface is IDW on log₂(ratio), masked to 1.2 km around sensors (3 km when only the 8 city stations report).

## 8. Next steps

1. Run `--source api` to extend data to the present and get the non-heating season.
2. Calibrate Lightnet against Agdata (collocated pairs, linear plus humidity term).
3. Build the heatmap: points from `heatmap_points.csv` (`qc_ok`) → IDW/kriging grid, plus a district EAQI layer, with heating and non-heating toggles.
4. Overlay context: traffic counters (`docs/.../hluche_miesta/merace.csv`), the gas-network gap (Brodno), and the city priority sites (§3).
