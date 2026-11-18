# 🗺️ zilina-air-quality-heatmap

[English](README.md) | **Slovensky**

Interaktívna mapa kvality ovzdušia v Žiline z otvorených dát mesta, porovnaná s odporúčaniami WHO.

🌐 **Online:** https://sugarpowered.github.io/zilina-air-quality-heatmap/

## 🚀 Spustenie

🐍 Potrebuješ Python 3.10 alebo novší. Príkazy spúšťaj v priečinku projektu.

**1. Inštalácia (iba prvýkrát)**

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
```

**2. Príprava dát a mapy**

```bash
python scripts/prepare_data.py
python scripts/build_heatmap.py
```

**3. Otvorenie mapy**

```bash
python -m http.server -d heatmap 8000
```

V prehliadači otvor **http://localhost:8000**. Server zastavíš klávesmi `Ctrl+C`.

⚠️ Súbor `index.html` neotváraj priamo dvojklikom, lebo by sa nenačítala mapa OpenStreetMap.

## 🔄 Aktuálne dáta

Bez ďalších parametrov sa použijú archivované dáta z `docs/` (do 25. 3. 2026). Ak chceš pridať novšie merania z Open Data API mesta, v kroku 2 spusti namiesto prvého príkazu:

```bash
python scripts/prepare_data.py --update
```

Stiahne len hodiny novšie, než aké už sú v `data/`, takže archív `docs/` nepotrebuje. Ak API nie je dostupné, skončí so správou a `data/` nezmení.

Na GitHube to beží automaticky každý deň ([.github/workflows/update-data.yml](.github/workflows/update-data.yml)): nové dáta sa commitnú a mapa sa znova nasadí. Mapa zobrazuje čas posledného merania a tlačidlo **Najnovší ⏭** preskočí na najnovší deň.

## 📁 Čo kde je

| Cesta | Obsah |
|---|---|
| 📚 `docs/` | Archív podkladov z predchádzajúcich projektov (nie je v repozitári) |
| 📝 `docs-summary-sk.md` | Zhrnutie podkladov a zistení ([anglická verzia](docs-summary.md)) |
| 🛠️ `scripts/` | Skripty na prípravu dát a mapy |
| 📊 `data/` | Pripravené dáta (generované) |
| 🗺️ `heatmap/` | Mapa (`index.html` + generovaný `data.js`) |

## 🚢 Nasadenie

Každý push do vetvy `main`, ktorý mení priečinok `heatmap/`, sa automaticky zverejní na GitHub Pages pomocou [.github/workflows/pages.yml](.github/workflows/pages.yml).
