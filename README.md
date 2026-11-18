# 🗺️ zilina-air-quality-heatmap

**English** | [Slovensky](README-SK.md)

Interactive air-quality map of Žilina built from the city's open data and compared with WHO guidelines.

🌐 **Online:** https://sugarpowered.github.io/zilina-air-quality-heatmap/

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

## 🔄 Fresh data from the city API (optional)

By default the scripts use the archived data in `docs/` (up to 25 March 2026). For current data, replace the first command in step 2 with:

```bash
python scripts/prepare_data.py --source api --start 2025-10-08 --end 2026-11-18
```

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
