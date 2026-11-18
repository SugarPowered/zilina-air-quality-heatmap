# 🗺️ zilina-air-quality-heatmap

**English** | [Slovensky](README-SK.md)

Interactive air-quality map of Žilina built from the city's open data and compared with WHO guidelines.

🌐 **Online:** https://sugarpowered.github.io/zilina-air-quality-heatmap/

## 🗺️ What the map shows

- **7 pollutants** as switchable layers: PM1, PM2.5, PM4, PM10, NO₂, SO₂, CO.
- **Colour = daily mean ÷ WHO 2021 24-hour guideline.** Blue is below the guideline, red is above it (poorer air quality, higher health risk). PM1 and PM4 have no WHO guideline, so they use the PM2.5 and PM10 values.
- **Day slider** with **Prehrať** (play) and **Najnovší ⏭** (latest) buttons. The ← / → arrow keys move one day.
- **Period toggle:** *Obe siete* (both networks, from 9 Oct 2025, default) or *Celé obdobie* (full period, from 6 Oct 2023). Before October 2025 only the 8 city stations measure.
- **Sensor count** such as "52 z 123 senzorov · 4 nad odporúčaním" (52 of 123 sensors, 4 above the guideline): reporting sensors out of those installed on that day.
- **Interpolated surface** only when at least 20 sensors report. NO₂, SO₂ and CO come from the 8 city stations only, so they show points only.
- Hover a sensor for its value. The collapsed **ℹ️ O dátach** (about the data) section holds the last-measurement time, a table of the day's values and a short methodology note.
- The surface crossfades between days. On a phone the panel is a bottom sheet you can collapse by tapping its handle.

The map interface is in Slovak.

## 🚀 Getting started

🐍 You need Python 3.10 or newer. Run all commands from the project folder.

**1. Install (first time only)**

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
```

**2. Prepare the data and the map**

```bash
python scripts/prepare_data.py
python scripts/build_heatmap.py
```

**3. Open the map**

```bash
python -m http.server -d heatmap 8000
```

Open **http://localhost:8000** in your browser. Stop the server with `Ctrl+C`.

⚠️ Don't open `index.html` by double-clicking it. The OpenStreetMap background won't load from a local file.

## 🔄 Recent data

By default the scripts use the archived data in `docs/` (up to 25 March 2026). To add newer measurements from the city's Open Data API, replace the first command in step 2 with:

```bash
python scripts/prepare_data.py --update
```

It downloads only the hours newer than the data already in `data/`, so the `docs/` archive isn't needed. If the API is unavailable, it stops with a message and leaves `data/` unchanged.

On GitHub this runs automatically every day at 05:15 UTC ([.github/workflows/update-data.yml](.github/workflows/update-data.yml)): new data is committed and the map is redeployed. If the API is down, the run finishes quietly with a notice and changes nothing. To run it manually: **Actions → Update recent data → Run workflow**.

## 📁 What's where

| Path | Content |
|---|---|
| 📚 `docs/` | Archive of materials from earlier projects (not in the repository) |
| 📝 `docs-summary.md` | Summary of the materials and findings ([Slovak version](docs-summary-sk.md)) |
| 🛠️ `scripts/` | Scripts that prepare the data and the map |
| 📊 `data/` | Prepared data (generated) |
| 🗺️ `heatmap/` | The map (`index.html` + generated `data.js`) |

## 🚢 Deployment

Every push to `main` that changes `heatmap/` is published to GitHub Pages automatically by [.github/workflows/pages.yml](.github/workflows/pages.yml).
