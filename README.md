# 🗺️ zilina-air-quality-heatmap

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

## 🔄 Čerstvé dáta z API mesta (voliteľné)

Bez ďalších parametrov sa použijú archivované dáta z `docs/` (do 25. 3. 2026). Ak chceš aktuálne dáta, v kroku 2 spusti namiesto prvého príkazu:

```bash
python scripts/prepare_data.py --source api --start 2025-10-08 --end 2026-11-18
```

## 📁 Čo kde je

| Cesta | Obsah |
|---|---|
| 📚 `docs/` | Archív podkladov z predchádzajúcich projektov |
| 📝 `docs-summary.md` | Zhrnutie podkladov a zistení |
| 🛠️ `scripts/` | Skripty na prípravu dát a mapy |
| 📊 `data/` | Pripravené dáta (generované) |
| 🗺️ `heatmap/` | Mapa (`index.html` + generovaný `data.js`) |
