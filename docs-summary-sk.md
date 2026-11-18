# Zhrnutie podkladov: príprava heatmapy ohnísk znečistenia ovzdušia v Žiline

[English](docs-summary.md) | **Slovensky**

> Zdroj pravdy: `docs/KLIMA_24/` (študentský projekt KLIMA na FRI UNIZA, 2024 až 2026).
> Pripravené dáta: `data/` pomocou [scripts/prepare_data.py](scripts/prepare_data.py).

## 1. Čo je v `docs/`

| Priečinok | Obsah | Využitie pre heatmapu |
|---|---|---|
| `PROJEKT_24/` (2024/25) | Rešerše, správy Projekt 1–3, Kalmanovo dopĺňanie dát (R), SARIMA/ARIMAX pre Košickú, prvý článok | Metodika a kontext. **Dáta sú staré (8 staníc, týždenné ručné exporty).** |
| `PROJEKT_24/Dáta mesto/` | `data_doplnene.csv`, `LEGENDA_DATA.xlsx` (kódy stĺpcov), `referencne_udaje.xlsx` (pásma SHMÚ), `kalman.R` | Limity a legenda |
| `PROJEKT_25/Dáta/` (2025/26) | **Hlavný dataset.** Zoznam staníc, hodinová história 155 senzorov, skripty pre Open Data API, zhlukovanie hluchých miest (`hluche_miesta/`) | **Primárny vstup** |
| `PROJEKT_25/PUBLIKOVANIE_LETO 2026/` | Analytický článok (EAQI pre 20 mestských častí), prehľadový článok (Danko/Mikuš/Šubert) | Metodika |
| `PROJEKT_25/Zápisy zo stretnutí/` | Zápisy zo stretnutí vrátane priorít mesta | Rozsah a ohniská na overenie |
| `PROJEKT_26/` | Návrh článku o priestorovom zhlukovaní sietí PM2.5 (k-means, Voronoi, CSI) | Nápady na metódy |
| PDF v koreni | Diplomové práce (Benešová, Pinková), správa SHMÚ AG/MMSKO 2024–25 | Pozadie |

## 2. Zdroje dát

**API** (platforma Invipo, Open Data portál mesta Žilina, v prevádzke od konca roka 2025):

| Dataset | Endpoint | Telo požiadavky |
|---|---|---|
| Zoznam staníc (GeoJSON) | `POST https://opendata.zilina.sk/api/datasets/v1/core/geojson/items` | `{"classes":"EnvironmentalSensor"}` |
| Hodinová história | `POST https://opendata.zilina.sk/api/datasets/v2/environment-monitoring/history` | `{"itemId":[id],"type":"hourly","from":"YYYY-MM-DD HH:MM:SS.000Z","to":…}` |

Odpoveď s históriou **neobsahuje id stanice**, preto treba pýtať jednu stanicu na jednu požiadavku. Ďalšie užitočné datasety na portáli: počty vozidiel (`pocet-vozidiel-za-hodinu`, zaťaženie detektorov), denné priemery počasia, počet obyvateľov podľa ulíc (`pocet-obcanov-podla-ulic`), školy.

**Sieť senzorov** (155 zariadení):

| Typ | Počet | Meria | Od | Poznámka |
|---|---|---|---|---|
| Plná stanica Agdata | 8 | PM1/2.5/4/10, NO₂, SO₂, CO + meteo | 4. 10. 2023 | Chrbtica siete, blízka referenčným meraniam |
| Agdata len meteo | 10 | vietor, teplota, tlak, vlhkosť, zrážky | 10/2023 | Bez znečisťujúcich látok |
| **Lightnet SMART** (stĺpy osvetlenia) | 137 | PM1/2.5/4/10, hluk, teplota, vlhkosť | **7. 10. 2025** | Nízkonákladové optické, hustá sieť |

8 plných staníc: autobusová stanica, Košická/Nemocničná, Kuzmányho, park Ľ. Štúra, Hájik, Vlčince, Brodno, Žilinská Lehota.
**Ozón (O₃) sa nikde nemeria.**

**Lokálny archív:** `AirPollutionSensorsData.csv` (všetky senzory, 4. 10. 2023 až 25. 3. 2026, hodinovo), `udaje o staniciach + miesto.xlsx` (súradnice a spätne dohľadaná adresa a mestská časť), `ALL_snimace_summary.xlsx` (štatistika chýbajúcich dát).

## 3. Hlavné zistenia z predchádzajúcej práce

- **Doprava:** Košická ulica a križovatky majú vyššie NO₂ a PM. NO₂ vrcholí v dopravných špičkách.
- **Vykurovanie:** PM10 je vysoké v zimné večery a cez víkendy kvôli kúreniu tuhým palivom. **Brodno a okolie nemajú plynovod** (informácia od mesta), ale mapa takýchto oblastí zatiaľ neexistuje. Práve to je hlavný dôvod pre heatmapu.
- **Meteorológia:** inverzie a bezvetrie spôsobujú epizódy znečistenia. Dážď PM znižuje.
- **Portál Smart Žilina** zobrazuje jeden nepriehľadný index pre celé mesto a len niekoľko staníc. Navrhované riešenie: **EAQI pre 20 mestských častí** (rozhoduje najhoršia látka).
- **Výpadky dát:** pravidelne chýbajúca hodina (23:00, niekedy 19:00) a výpadky na dni až týždne kvôli kalibrácii, krádeži, poruchám alebo servisu. Časom niektoré senzory skresľujú stromy a nové budovy. Medzery sa dopĺňali Kalmanovým filtrom (`imputeTS::na_kalman`, heuristika auto.arima/StructTS).
- **Doterajšie modely:** SARIMA(1,0,3)(1,0,0)₇ pre zrážky, log-SARIMA pre dopravu, SARIMA(1,0,1)(2,1,2)₂₄ pre NO₂, ARIMAX a kauzálne modely pre vzťah počasie → doprava.
- **Prioritné lokality mesta** (stretnutia 12. 11. 2025 a 18. 3. 2026): križovatka Košická a smer Strážov (tunel Višňové), Solinky/Hájik (parkovacia politika, diaľničný privádzač), podjazd Kysucká, školské zóny (ZŠ Kráľovnej pokoja, Predmestská, Na Závaží), železničná stanica a nový most, Brodno (tuhé palivo).
- **Hluché miesta:** `hluche_miesta/` obsahuje mapy pokrytia (k-means, DBSCAN, aglomeratívne zhlukovanie) a návrhy nových umiestnení senzorov.

⚠️ Článok z PROJEKT_24 *„Kvalita ovzdušia mesta Žilina“* uvádza výsledky pre O₃ („ozónový paradox“), „päť zón“ a pokrytie celého roka 2024. Senzory O₃ nemerajú, preto **tieto tvrdenia necitovať**.

## 4. Limitné a odporúčané hodnoty (µg/m³)

| | PM2.5 | PM10 | NO₂ |
|---|---|---|---|
| Limit EÚ/SR, 24 h | – | 50 (max. 35 dní/rok) | 200 (1 h) |
| Limit EÚ/SR, ročný | 25 | 40 | 40 |
| WHO 2021, 24 h / ročný | 15 / 5 | 45 / 15 | 25 / 10 |
| Index SHMÚ, 1 h („dobrá“ do) | 25 | 40 | 40 |
| Pásma EAQI | 0-5-15-50-90-140 | 0-15-45-120-195-270 | 0-10-25-60-100-150 |

## 5. Pripravené dáta

```bash
pip install -r requirements.txt
python scripts/prepare_data.py                                         # z archívu v docs/
python scripts/prepare_data.py --source api --start 2025-10-08 --end 2026-11-18   # čerstvé dáta
```

| Súbor | Obsah |
|---|---|
| `data/stations.csv` | 155 senzorov: id, názov, typ, súradnice, adresa, stav, `in_bbox`, `dup_coord` |
| `data/pm_hourly.csv.gz` | 414 tis. vyčistených hodinových záznamov (PM1/2.5/4/10, NO₂/SO₂/CO). Hodnoty mimo 0–1000 µg/m³ (CO: 0–30 000) sú nahradené prázdnou hodnotou. |
| `data/heatmap_points.csv` | **Vstup pre heatmapu.** Jeden riadok na PM senzor: priemer/medián/p95 PM, dni nad limitom EÚ/WHO, pokrytie, `qc_ok`, `qc_reason` |

**Predvolené obdobie: 8. 10. 2025 až 25. 3. 2026.** Je to jediné obdobie, keď merajú obe siete, a zároveň vykurovacia sezóna, takže výsledky sú posunuté smerom k zime.

Výsledok kontroly kvality: **102 zo 145 senzorov je použiteľných.** Vyradené: 41 s pokrytím pod 30 %, 1 s nereálnymi hodnotami (priemer ≈ 780), 1 mimo Žiliny (Handlová). Medián pokrytia je 66 %.

**Prvé ohniská** (priemer za obdobie):

| Senzor | Lokalita | PM10 | PM2.5 | Dni PM10 > 50 |
|---|---|---|---|---|
| LN 43 #16 | Zvolenská, Vlčince | 91 | 86 | 66/83 |
| LN 42 #2 | Dolná Trnovská, Trnové | 87 | 83 | 69/85 |
| LN 41 #6 | Rajčianska, Strážov | 78 | 76 | 43/83 |
| LN 31 #2 | Daxnerova, Hliny VIII | 65 | 64 | 34/75 |
| LN 27 #3/#4/#6 | Budatín | 55–64 | 53–61 | ~40 % dní |
| LN 37 #1 | Bytčianska, Považský Chlmec | 59 | 54 | 48/107 |
| autobusová stanica (Agdata) | Staré mesto | 56 | 51 | **72/132** |

Najčistejšie senzory sú v Zádubní, Zástraní a Bytčici (PM10 5–10). Spomedzi staníc Agdata majú najnižšie hodnoty Kuzmányho a Brodno (28 a 30). Väčšina ohnísk je v okrajových častiach s rodinnými domami (Trnové, Strážov, Budatín, Považský Chlmec), čo zodpovedá vysvetleniu kúrením tuhým palivom. Je to hypotéza, ktorú treba overiť.

## 6. Obmedzenia pre heatmapu

1. **Senzory Lightnet sú nekalibrované nízkonákladové optické senzory.** PM2.5 ≈ PM10 (frakcie sa reálne nerozlišujú) a merania ovplyvňuje vlhkosť. 3 senzory majú p95 nad 250. Treba ich buď kalibrovať podľa najbližšej stanice Agdata, alebo zobraziť obe siete ako samostatné vrstvy.
2. **Súradnice:** 14 duplicitných súradníc a 1 senzor mimo Žiliny. Tím plánoval súradnice opraviť (úloha z 11. 3. 2026), preto ich pred interpoláciou skontroluj.
3. **Sezónne skreslenie:** dáta Lightnet začínajú v októbri 2025. Pre porovnanie s letom alebo celým rokom treba stiahnuť dáta z API po marci 2026.
4. **Interpolácia:** pri približne 100 bodoch použi IDW alebo kriging v rámci hraníc mesta. Nekresli hodnoty mimo oblasti pokrytej senzormi ani cez riečne údolia. Robustnou alternatívou je EAQI po mestských častiach.

## 7. Heatmapa

```bash
python scripts/prepare_data.py && python scripts/build_heatmap.py
python -m http.server -d heatmap 8000      # otvor http://localhost:8000 (dlaždice OSM potrebujú http, nie file://)
```

- [heatmap/index.html](heatmap/index.html) používa Leaflet, dlaždice OpenStreetMap a `heatmap/data.js` s dennými priemermi pre 143 senzorov za 814 dní.
- Každá znečisťujúca látka je samostatná prepínateľná vrstva. Farba ukazuje denný priemer ÷ 24-hodinová odporúčaná hodnota WHO 2021 na divergentnej logaritmickej škále od 0,25× do 4×, so stredom v 1× (modrá pod, červená nad).
- Deň sa vyberá posuvníkom s prehrávaním. Mapa zobrazuje body senzorov, popis po prejdení myšou a tabuľku hodnôt v daný deň.
- PM1 a PM4 nemajú odporúčanú hodnotu WHO, preto sa ako náhrada použijú hodnoty pre PM2.5 a PM10. V rozhraní je to vyznačené.
- Plocha je IDW na log₂(pomeru), zobrazená do 1,2 km od senzorov (3 km, keď merajú len 8 mestských staníc).
- Online: https://sugarpowered.github.io/zilina-air-quality-heatmap/

## 8. Ďalšie kroky

1. Spustiť `--source api`, aby dáta siahali až po súčasnosť a zahŕňali aj nevykurovaciu sezónu.
2. Kalibrovať Lightnet podľa Agdata (dvojice senzorov pri sebe, lineárny model s členom pre vlhkosť).
3. Rozšíriť heatmapu (hotová: §7) o vrstvu EAQI po mestských častiach a prepínanie vykurovacej a nevykurovacej sezóny.
4. Pridať kontext: sčítače dopravy (`docs/.../hluche_miesta/merace.csv`), oblasti bez plynovodu (Brodno) a prioritné lokality mesta (§3).
