# World Flags Interactive Application

## Projekt leírás
Interaktív világzászló alkalmazás, amely természetes nyelvi kérések alapján képes megkeresni és bemutatni a világ országainak zászlóit.

## Funkciók
1. **Zászlók letöltése** - Automatikus letöltés a flagpedia.net/flagcdn.com API-ról
2. **Képelemzés** - Színek, formák, ábrák automatikus felismerése
3. **Párbeszédes keresés** - Természetes nyelvi kérések feldolgozása
4. **Intelligens szűrés** - Kérések alapján releváns zászlók kiválasztása
5. **Adatbázis** - Országok, kontinensek, jellemzők tárolása

## Projekt struktúra
```
world_flags_project/
├── data/
│   ├── flags/              # Letöltött zászló képek
│   ├── countries.json      # Országok adatai
│   └── flag_features.json  # Zászlók elemzett jellemzői
├── src/
│   ├── downloader.py       # Zászlók letöltése
│   ├── analyzer.py         # Képelemzés modul
│   ├── search.py          # Keresés és szűrés
│   └── chat.py            # Párbeszédes felület
├── requirements.txt
└── main.py
```

## Technológiák
- **Képletöltés**: requests, aiohttp
- **Képelemzés**: OpenCV, PIL, numpy, scikit-image
- **Természetes nyelv**: NLTK, spaCy
- **Adatbázis**: JSON, SQLite
- **UI**: Streamlit vagy Gradio

## Telepítés és Használat

### 1. Függőségek telepítése
```bash
pip install -r requirements.txt
```

### 2. Alkalmazás inicializálása
```bash
# Zászlók letöltése és elemzése
python main.py --setup
```

### 3. Használati módok

#### Interaktív keresés (terminál)
```bash
python main.py --interactive
```

#### Webes felület (Streamlit)
```bash
python main.py --streamlit
```

#### Egyetlen keresés
```bash
python main.py --search "piros és kék zászlók"
```

#### Statisztikák
```bash
python main.py --stats
```

#### Demo futtatása
```bash
python demo.py all
```

## Webes alkalmazás

### Élő alkalmazás
🌐 **[Próbáld ki itt!](https://world-flags-search.streamlit.app/)** *(hamarosan)*

### Helyi futtatás
```bash
# Webes felület (Streamlit)
streamlit run streamlit_app.py
```

## Deployment
Az alkalmazás automatikusan telepíthető a Streamlit Community Cloud-on:
1. Fork-old ezt a repository-t
2. Látogasd meg a [streamlit.io](https://streamlit.io/) oldalt
3. Kattints "Deploy an app" gombra
4. Válaszd ki a fork-olt repository-t
5. Állítsd be a main file-t: `streamlit_app.py`

## API források
- Zászlók: https://flagcdn.com/{country_code}.png
- Országkódok: https://flagcdn.com/en/codes.json 