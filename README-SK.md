# 🗺️ zilina-air-quality-heatmap

[English](README.md) | **Slovensky**

Interaktívna mapa kvality ovzdušia v Žiline z otvorených dát mesta, porovnaná s odporúčaniami WHO.

🌐 **Online:** https://sugarpowered.github.io/zilina-air-quality-heatmap/

## 🗺️ Čo mapa ukazuje

- **7 znečisťujúcich látok** ako prepínateľné vrstvy: PM1, PM2.5, PM4, PM10, NO₂, SO₂, CO.
- **Farba = denný priemer ÷ 24-hodinová odporúčaná hodnota WHO 2021.** Modrá je pod odporúčaním, červená nad ním (horšia kvalita ovzdušia, vyššie zdravotné riziko). PM1 a PM4 nemajú hodnotu WHO, preto sa použijú hodnoty pre PM2.5 a PM10.
- **Posuvník dní** s prehrávaním, predchádzajúcim/nasledujúcim dňom a tlačidlom **Najnovší ⏭**. Panel ukazuje čas posledného merania.
- **Prepínač obdobia:** *Obe siete* (od 9. 10. 2025, predvolené) alebo *Celé obdobie* (od 6. 10. 2023). Pred októbrom 2025 meria len 8 mestských staníc.
- **Počet senzorov**, napr. „52 z 123 senzorov merajúcich PM10“: koľko senzorov meralo z tých, ktoré boli k danému dňu nainštalované.
- **Interpolovaná plocha** sa kreslí, len keď meria aspoň 20 senzorov. NO₂, SO₂ a CO meria len 8 mestských staníc, preto sa zobrazujú iba ako body.
- Po prejdení myšou nad senzorom sa zobrazí jeho hodnota. Panel obsahuje aj tabuľku všetkých hodnôt v daný deň a popis metodiky.

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

Na GitHube to beží automaticky každý deň o 05:15 UTC ([.github/workflows/update-data.yml](.github/workflows/update-data.yml)): nové dáta sa commitnú a mapa sa znova nasadí. Ak API nefunguje, beh skončí potichu s upozornením a nič nezmení. Ručné spustenie: **Actions → Update recent data → Run workflow**.

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
