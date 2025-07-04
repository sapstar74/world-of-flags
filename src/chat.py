"""
Párbeszédes felület modul - Interaktív zászlókereső chat
"""

import streamlit as st
from pathlib import Path
from typing import Dict, List, Any
import json
from PIL import Image
import os
import time
import sys

# Aktuális fájl könyvtárának hozzáadása a Python path-hoz
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Egyszerű absolute import
try:
    from downloader import FlagDownloader
    from analyzer import FlagAnalyzer
    from search import FlagSearchEngine
except ImportError as e:
    st.error(f"Import hiba: {e}")
    st.error("Ellenőrizd, hogy a downloader.py, analyzer.py és search.py fájlok elérhetőek-e!")
    st.stop()

class FlagChatInterface:
    """Párbeszédes zászlókereső felület"""
    
    def __init__(self):
        """Inicializálás"""
        self.data_dir = Path(__file__).parent.parent / "data"
        
        # Komponensek inicializálása
        self.downloader = FlagDownloader(self.data_dir)
        self.analyzer = FlagAnalyzer(self.data_dir)
        self.search_engine = FlagSearchEngine(self.data_dir)
        
        # Országok betöltése
        with open(self.data_dir / "countries.json", 'r', encoding='utf-8') as f:
            self.countries = json.load(f)
        
        # Session state inicializálása
        if 'flags_downloaded' not in st.session_state:
            st.session_state.flags_downloaded = False
        if 'flags_analyzed' not in st.session_state:
            st.session_state.flags_analyzed = False
        if 'current_results' not in st.session_state:
            st.session_state.current_results = None
    
    def _is_territory(self, country_code: str) -> bool:
        """Meghatározza, hogy a kód egy független terület-e (nem független állam)"""
        # Független államok listája (nem teljes, de a főbb kategóriákat lefedi)
        independent_countries = {
            'ad', 'ae', 'af', 'ag', 'al', 'am', 'ao', 'ar', 'at', 'au', 'az',
            'ba', 'bb', 'bd', 'be', 'bf', 'bg', 'bh', 'bi', 'bj', 'bn', 'bo', 'br', 'bs', 'bt', 'bw', 'by', 'bz',
            'ca', 'cd', 'cf', 'cg', 'ch', 'ci', 'cl', 'cm', 'cn', 'co', 'cr', 'cu', 'cv', 'cy', 'cz',
            'de', 'dj', 'dk', 'dm', 'do', 'dz',
            'ec', 'ee', 'eg', 'er', 'es', 'et',
            'fi', 'fj', 'fm', 'fr',
            'ga', 'gb', 'gd', 'ge', 'gh', 'gm', 'gn', 'gq', 'gr', 'gt', 'gw', 'gy',
            'hn', 'hr', 'ht', 'hu',
            'id', 'ie', 'il', 'in', 'iq', 'ir', 'is', 'it',
            'jm', 'jo', 'jp',
            'ke', 'kg', 'kh', 'ki', 'km', 'kn', 'kp', 'kr', 'kw', 'kz',
            'la', 'lb', 'lc', 'li', 'lk', 'lr', 'ls', 'lt', 'lu', 'lv', 'ly',
            'ma', 'mc', 'md', 'me', 'mg', 'mh', 'mk', 'ml', 'mm', 'mn', 'mt', 'mu', 'mv', 'mw', 'mx', 'my', 'mz',
            'na', 'ne', 'ng', 'ni', 'nl', 'no', 'np', 'nr', 'nu', 'nz',
            'om',
            'pa', 'pe', 'pg', 'ph', 'pk', 'pl', 'pt', 'pw', 'py',
            'qa',
            'ro', 'rs', 'ru', 'rw',
            'sa', 'sb', 'sc', 'sd', 'se', 'sg', 'si', 'sk', 'sl', 'sm', 'sn', 'so', 'sr', 'ss', 'st', 'sv', 'sz',
            'td', 'tg', 'th', 'tj', 'tl', 'tm', 'tn', 'to', 'tr', 'tt', 'tv', 'tw', 'tz',
            'ua', 'ug', 'us', 'uy', 'uz',
            'va', 'vc', 've', 'vn', 'vu',
            'ws', 'xk',
            'ye',
            'za', 'zm', 'zw'
        }
        
        # Ha nem független állam és nem US állam, akkor független terület
        return country_code not in independent_countries and not country_code.startswith('us-')
    
    def _filter_by_territory_type(self, country_codes: List[str]) -> List[str]:
        """Szűrés terület típus alapján a checkbox beállítások szerint"""
        filtered_codes = []
        
        include_countries = st.session_state.get('include_countries', True)
        include_territories = st.session_state.get('include_territories', True)
        include_us_states = st.session_state.get('include_us_states', False)
        
        for code in country_codes:
            if code.startswith('us-'):
                # US államok
                if include_us_states:
                    filtered_codes.append(code)
            elif self._is_territory(code):
                # Független területek
                if include_territories:
                    filtered_codes.append(code)
            else:
                # Független államok
                if include_countries:
                    filtered_codes.append(code)
        
        return filtered_codes
    
    def _filter_by_continents(self, flag_details: List[Dict], search_query: str = "") -> List[Dict]:
        """Szűrés kontinensek alapján"""
        # Ellenőrizzük, hogy van-e explicit kontinens a keresési kifejezésben
        explicit_continents = self.search_engine.extract_continents(search_query.lower()) if search_query else []
        
        # Ha több kontinens van explicit megadva (pl. "európai szigetek"), 
        # azt használjuk az UI szűrők helyett
        if len(explicit_continents) > 1:
            continent_countries = self.search_engine.continent_countries
            
            # Metszet képzése a több kontinens között
            matching_flags = None
            for continent in explicit_continents:
                continent_flags = set(continent_countries.get(continent, []))
                if matching_flags is None:
                    matching_flags = continent_flags
                else:
                    matching_flags = matching_flags.intersection(continent_flags)
            
            # Szűrés az explicit kontinens kombináció alapján
            filtered_details = []
            for detail in flag_details:
                country_code = detail['country_code']
                if country_code in (matching_flags or set()):
                    filtered_details.append(detail)
            
            return filtered_details
        
        # Ha csak egy explicit kontinens van (pl. "szigetek"), kombináljuk az UI szűrőkkel
        # Ha nincs explicit kontinens, csak az UI checkbox szűrőket használjuk
        
        # UI checkbox szűrők betöltése
        include_europe = st.session_state.get('include_europe', True)
        include_asia = st.session_state.get('include_asia', True)
        include_africa = st.session_state.get('include_africa', True)
        include_north_america = st.session_state.get('include_north_america', True)
        include_central_america = st.session_state.get('include_central_america', True)
        include_south_america = st.session_state.get('include_south_america', True)
        include_oceania = st.session_state.get('include_oceania', True)
        include_islands = st.session_state.get('include_islands', True)
        
        # Kontinens országok adatainak betöltése
        continent_countries = self.search_engine.continent_countries
        
        # Ha van egy explicit kontinens (pl. "szigetek"), azt kombináljuk az UI szűrőkkel
        if len(explicit_continents) == 1:
            explicit_continent = explicit_continents[0]
            explicit_countries = set(continent_countries.get(explicit_continent, []))
            
            # UI alapján engedélyezett kontinensek
            ui_allowed_countries = set()
            
            if include_europe:
                ui_allowed_countries.update(continent_countries.get('europe', []))
            if include_asia:
                ui_allowed_countries.update(continent_countries.get('asia', []))
            if include_africa:
                ui_allowed_countries.update(continent_countries.get('africa', []))
            if include_north_america:
                ui_allowed_countries.update(continent_countries.get('north america', []))
            if include_central_america:
                ui_allowed_countries.update(continent_countries.get('central america', []))
            if include_south_america:
                ui_allowed_countries.update(continent_countries.get('south america', []))
            if include_oceania:
                ui_allowed_countries.update(continent_countries.get('oceania', []))
            if include_islands:
                ui_allowed_countries.update(continent_countries.get('islands', []))
            
            # Metszet képzése: explicit kontinens ÉS UI szűrők
            allowed_countries = explicit_countries.intersection(ui_allowed_countries)
            
        else:
            # Nincs explicit kontinens, csak UI checkbox szűrőket használjuk
            
            # Ha minden kontinens be van kapcsolva, nincs szűrés
            if all([include_europe, include_asia, include_africa, include_north_america, 
                    include_central_america, include_south_america, include_oceania, include_islands]):
                return flag_details
            
            # Engedélyezett országkódok gyűjtése UI alapján
            allowed_countries = set()
            
            if include_europe:
                allowed_countries.update(continent_countries.get('europe', []))
            if include_asia:
                allowed_countries.update(continent_countries.get('asia', []))
            if include_africa:
                allowed_countries.update(continent_countries.get('africa', []))
            if include_north_america:
                allowed_countries.update(continent_countries.get('north america', []))
            if include_central_america:
                allowed_countries.update(continent_countries.get('central america', []))
            if include_south_america:
                allowed_countries.update(continent_countries.get('south america', []))
            if include_oceania:
                allowed_countries.update(continent_countries.get('oceania', []))
            if include_islands:
                allowed_countries.update(continent_countries.get('islands', []))
        
        # Szűrés az engedélyezett országkódok alapján
        filtered_details = []
        for detail in flag_details:
            country_code = detail['country_code']
            if country_code in allowed_countries:
                filtered_details.append(detail)
        
        return filtered_details
    
    def display_flag_image(self, country_code: str, country_name: str) -> bool:
        """Zászló kép megjelenítése"""
        try:
            # Keressük meg a zászló fájlt
            flag_files = list(self.data_dir.glob(f"flags/{country_code}_*.png"))
            if flag_files:
                flag_path = flag_files[0]
                image = Image.open(flag_path)
                st.image(image, caption=f"{country_name} ({country_code.upper()})", width=200)
                return True
            else:
                st.write(f"🏳️ {country_name} ({country_code.upper()}) - Kép nem elérhető")
                return False
        except Exception as e:
            st.write(f"🏳️ {country_name} ({country_code.upper()}) - Hiba: {e}")
            return False
    
    def format_flag_details(self, detail: Dict) -> str:
        """Zászló részletek formázása"""
        info_parts = []
        
        # Színek
        if detail.get('colors'):
            colors_str = ", ".join(detail['colors'])
            info_parts.append(f"Színek: {colors_str}")
        
        # Mintázatok
        patterns = []
        if detail.get('has_stripes'):
            patterns.append("csíkos")
        if detail.get('has_bands'):
            patterns.append("sávos")
        if detail.get('has_stars'):
            patterns.append("csillagos")
        
        if patterns:
            info_parts.append(f"Mintázat: {', '.join(patterns)}")
        
        # Szimbolikus elemek
        symbolic_elements = []
        if detail.get('has_animal'):
            symbolic_elements.append("🦅")
        if detail.get('has_plant'):
            symbolic_elements.append("🌳")
        if detail.get('has_weapon'):
            symbolic_elements.append("⚔️")
        if detail.get('has_human'):
            symbolic_elements.append("👤")
        if detail.get('has_building'):
            symbolic_elements.append("🏛️")
        if detail.get('has_celestial'):
            symbolic_elements.append("☀️")
        if detail.get('has_union_jack'):
            symbolic_elements.append("🇬🇧")
        if detail.get('has_cross'):
            symbolic_elements.append("✝️")
        
        if symbolic_elements:
            info_parts.append(f"Szimbólumok: {' '.join(symbolic_elements)}")
        
        # Komplexitás
        complexity = detail.get('complexity_score', 0)
        if complexity > 0:
            info_parts.append(f"Komplexitás: {complexity}")
        
        return " | ".join(info_parts)
    
    def handle_user_query(self, query: str) -> Dict[str, Any]:
        """Felhasználói kérés feldolgozása"""
        if not query.strip():
            return {
                'type': 'error',
                'message': 'Kérlek, adj meg egy keresési kifejezést!'
            }
        
        # Speciális parancsok kezelése
        query_lower = query.lower()
        
        if 'letöltés' in query_lower or 'download' in query_lower:
            return {'type': 'download_request'}
        
        if 'elemzés' in query_lower or 'analyze' in query_lower:
            return {'type': 'analyze_request'}
        
        if 'help' in query_lower or 'segítség' in query_lower:
            return {'type': 'help'}
        
        if 'statisztika' in query_lower or 'stats' in query_lower:
            return {'type': 'stats'}
        
        # Zászló keresés
        try:
            results = self.search_engine.search_flags(query)
            
            if results and 'flag_details' in results:
                # Terület típus és szimbólum szűrés alkalmazása
                original_details = results['flag_details']
                original_count = len(original_details)
                
                # 1. Terület típus szűrés
                filtered_details = []
                for detail in original_details:
                    country_codes = [detail['country_code']]
                    filtered_codes = self._filter_by_territory_type(country_codes)
                    if filtered_codes:  # Ha a terület típus engedélyezett
                        filtered_details.append(detail)
                
                # 2. Kontinens szűrés
                filtered_details = self._filter_by_continents(filtered_details, query)
                
                # Eredmények frissítése
                results['flag_details'] = filtered_details
                results['total_count'] = len(filtered_details)
                
                # Ha a szűrés miatt nincs eredmény
                if len(filtered_details) == 0 and original_count > 0:
                    return {
                        'type': 'error',
                        'message': f'A keresés {original_count} találatot adott, de a szűrők miatt egyik sem jelenik meg. Módosítsd a terület típus vagy kontinens beállításokat a bal oldali sávban.'
                    }
            
            return {
                'type': 'search_results',
                'results': results,
                'query': query
            }
        except Exception as e:
            return {
                'type': 'error',
                'message': f'Hiba a keresés során: {str(e)}'
            }
    
    def display_search_results(self, results: Dict[str, Any], query: str):
        """Keresési eredmények megjelenítése"""
        total_count = results.get('total_count', 0)
        search_info = results.get('search_info', {})
        flag_details = results.get('flag_details', [])
        
        # Keresési információk
        st.write(f"**Keresés:** '{query}'")
        
        info_parts = []
        if search_info.get('colors'):
            info_parts.append(f"Színek: {', '.join(search_info['colors'])}")
        if search_info.get('patterns'):
            info_parts.append(f"Mintázatok: {', '.join(search_info['patterns'])}")
        if search_info.get('continents'):
            info_parts.append(f"Kontinensek: {', '.join(search_info['continents'])}")
        
        if info_parts:
            st.write(f"**Szűrők:** {' | '.join(info_parts)}")
        
        st.write(f"**Találatok:** {total_count} zászló")
        
        if total_count == 0:
            st.warning("Nincs találat a keresési kritériumoknak megfelelően.")
            st.write("**Javaslatok:**")
            st.write("- Próbálj más színeket vagy mintázatokat")
            st.write("- Használj egyszerűbb kifejezéseket")
            st.write("- Példák: 'piros zászlók', 'csillagos zászlók', 'európai zászlók'")
            return
        
        # Eredmények megjelenítése
        st.write("---")
        
        # Oszlopok létrehozása a képek megjelenítéséhez
        cols_per_row = 3
        for i in range(0, len(flag_details), cols_per_row):  # Összes eredmény
            cols = st.columns(cols_per_row)
            
            for j in range(cols_per_row):
                if i + j < len(flag_details):
                    detail = flag_details[i + j]
                    
                    with cols[j]:
                        # Zászló kép
                        self.display_flag_image(detail['country_code'], detail['country_name'])
                        
                        # Részletek
                        details_text = self.format_flag_details(detail)
                        if details_text:
                            st.caption(details_text)
        
        # Összes eredmény megjelenítve
        if total_count > 0:
            st.success(f"Minden {total_count} találat megjelenítve!")
    
    def display_help(self):
        """Súgó megjelenítése"""
        st.write("## 🤖 Zászlókereső Súgó")
        
        st.write("### Keresési példák:")
        examples = [
            "**Színek alapján:** 'piros és kék zászlók', 'zöld zászlók'",
            "**Mintázatok alapján:** 'csillagos zászlók', 'csíkos zászlók', 'sávos zászlók'",
            "**Kontinensek alapján:** 'európai zászlók', 'ázsiai zászlók'",
            "**Országnevek alapján:** 'magyarország zászló', 'amerika zászló', 'kína zászló'",
            "**Szimbolikus elemek:** 'állatos zászlók', 'növényes zászlók', 'fegyveres zászlók'",
            "**Kombinált:** 'piros csillagos zászlók', 'kék csíkos európai zászlók'",
            "**Speciális csillag keresések:** 'egy csillagos zászlók', 'sok csillagos zászlók'",
            "**Csillag pozíció:** 'sarokban csillag', 'középen csillag'",
            "**Csillag + szín:** 'piros csillagos zászlók', 'fehér csillagos zászlók'"
        ]
        
        for example in examples:
            st.write(f"- {example}")
        
        st.write("### Támogatott színek:")
        colors = [
            "piros/vörös", "kék", "világos kék/égkék", "sötét kék/tengerkék", 
            "zöld", "világos zöld", "sötét zöld", "sárga", "fehér", "fekete", 
            "narancs", "lila", "rózsaszín", "barna"
        ]
        st.write(", ".join(colors))
        
        st.write("### Támogatott mintázatok:")
        patterns = ["csillag/csillagos", "csík/csíkos", "sáv/sávos", "kereszt", "kör"]
        st.write(", ".join(patterns))
        
        st.write("### Szimbolikus elemek:")
        symbolic = ["állat/madár/sas/oroszlán", "növény/fa/levél/juhar", "fegyver/kard/lándzsa", 
                   "ember/emberi alak", "épület/torony/templom", "nap/hold/égi testek", "union jack/brit zászló", "kereszt/skandináv kereszt"]
        st.write(", ".join(symbolic))
        
        st.write("### Támogatott kontinensek és régiók:")
        continents = ["Európa", "Ázsia", "Afrika", "Amerika", "Észak-Amerika", "Közép-Amerika", "Dél-Amerika", "Óceánia", "Szigetek"]
        st.write(", ".join(continents))
    
    def display_stats(self):
        """Statisztikák megjelenítése"""
        features = self.analyzer.load_features()
        
        if not features:
            st.warning("Nincs elemzett adat. Először elemezd a zászlókat!")
            return
        
        st.write("## 📊 Zászló Statisztikák")
        
        # Alapstatisztikák
        total_flags = len(features)
        st.metric("Összesen elemzett zászló", total_flags)
        
        # Színstatisztikák
        all_colors = []
        for flag_data in features.values():
            all_colors.extend(flag_data.get('unique_colors', []))
        
        from collections import Counter
        color_counts = Counter(all_colors)
        
        st.write("### Leggyakoribb színek:")
        for color, count in color_counts.most_common(10):
            percentage = (count / total_flags) * 100
            st.write(f"- **{color}**: {count} zászló ({percentage:.1f}%)")
        
        # Mintázat statisztikák
        stripe_count = sum(1 for f in features.values() 
                          if f.get('stripes', {}).get('has_horizontal_stripes') or 
                             f.get('stripes', {}).get('has_vertical_stripes'))
        band_count = sum(1 for f in features.values() 
                        if f.get('stripes', {}).get('has_horizontal_bands') or 
                           f.get('stripes', {}).get('has_vertical_bands'))
        star_count = sum(1 for f in features.values() 
                        if f.get('shapes', {}).get('stars', 0) > 0)
        
        st.write("### Mintázatok:")
        st.write(f"- **Csíkos zászlók**: {stripe_count} ({stripe_count/total_flags*100:.1f}%)")
        st.write(f"- **Sávos zászlók**: {band_count} ({band_count/total_flags*100:.1f}%)")
        st.write(f"- **Csillagos zászlók**: {star_count} ({star_count/total_flags*100:.1f}%)")
    

    
    def run_streamlit_app(self):
        """Streamlit alkalmazás futtatása"""
        st.set_page_config(
            page_title="🏳️ Világzászló Kereső",
            page_icon="🏳️",
            layout="wide"
        )
        
        # CSS stílus a jobb UX-ért
        st.markdown("""
        <style>
        .search-container {
            background-color: #f0f2f6;
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 1rem;
            border: 2px solid #e6e9ef;
        }
        .stButton > button {
            width: 100%;
        }
        .back-to-top {
            text-align: center;
            margin: 1rem 0;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.title("🏳️ Világzászló Interaktív Kereső")
        st.write("Kérdezz rá a világ zászlóira természetes nyelven!")
        
        # Oldalsáv - Beviteli mező és rendszer állapot
        with st.sidebar:
            st.header("🔍 Keresés")
            
            # Chat input mező - Oldalsávban
            user_input = st.text_input(
                "Írd be a kérdésed:",
                value=st.session_state.get('example_query', ''),
                placeholder="Pl.: piros és kék csillagos zászlók",
                key="chat_input"
            )
            
            # Keresés gomb
            search_button = st.button("🔍 Keresés", type="primary")
            
            st.write("---")
            
            # Terület típus szűrők
            st.subheader("🌍 Terület típusok")
            
            # Checkbox-ok a terület típusokhoz
            include_countries = st.checkbox(
                "🏴 Országok",
                value=st.session_state.get('include_countries', True),
                help="Független államok (pl. Magyarország, Németország, USA)"
            )
            
            include_territories = st.checkbox(
                "🏝️ Független területek",
                value=st.session_state.get('include_territories', True),
                help="Autonóm területek, függőségek (pl. Grönland, Puerto Rico, Hong Kong)"
            )
            
            include_us_states = st.checkbox(
                "🇺🇸 US államok",
                value=st.session_state.get('include_us_states', False),
                help="Amerikai államok (pl. Kalifornia, Texas, New York)"
            )
            
            st.write("---")
            
            # Kontinens szűrők
            st.subheader("🌍 Kontinens szűrők")
            
            # Gyors választó gombok
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Mind", key="select_all_continents"):
                    st.session_state.include_europe = True
                    st.session_state.include_asia = True
                    st.session_state.include_africa = True
                    st.session_state.include_north_america = True
                    st.session_state.include_central_america = True
                    st.session_state.include_south_america = True
                    st.session_state.include_oceania = True
                    st.session_state.include_islands = True
                    st.rerun()
            
            with col2:
                if st.button("❌ Semmi", key="select_none_continents"):
                    st.session_state.include_europe = False
                    st.session_state.include_asia = False
                    st.session_state.include_africa = False
                    st.session_state.include_north_america = False
                    st.session_state.include_central_america = False
                    st.session_state.include_south_america = False
                    st.session_state.include_oceania = False
                    st.session_state.include_islands = False
                    st.rerun()
            
            include_europe = st.checkbox(
                "🇪🇺 Európa",
                value=st.session_state.get('include_europe', True),
                help="Európai országok (pl. Magyarország, Németország, Franciaország)"
            )
            
            include_asia = st.checkbox(
                "🇨🇳 Ázsia",
                value=st.session_state.get('include_asia', True),
                help="Ázsiai országok (pl. Kína, Japán, India)"
            )
            
            include_africa = st.checkbox(
                "🇿🇦 Afrika",
                value=st.session_state.get('include_africa', True),
                help="Afrikai országok (pl. Dél-Afrika, Egyiptom, Nigéria)"
            )
            
            include_north_america = st.checkbox(
                "🇺🇸 Észak-Amerika",
                value=st.session_state.get('include_north_america', True),
                help="Észak-amerikai országok (USA, Kanada, Mexikó)"
            )
            
            include_central_america = st.checkbox(
                "🇨🇺 Közép-Amerika & Karib",
                value=st.session_state.get('include_central_america', True),
                help="Közép-amerikai és karibi országok (pl. Kuba, Jamaica, Costa Rica)"
            )
            
            include_south_america = st.checkbox(
                "🇧🇷 Dél-Amerika",
                value=st.session_state.get('include_south_america', True),
                help="Dél-amerikai országok (pl. Brazília, Argentína, Chile)"
            )
            
            include_oceania = st.checkbox(
                "🇦🇺 Óceánia",
                value=st.session_state.get('include_oceania', True),
                help="Óceániai országok (pl. Ausztrália, Új-Zéland, Fiji)"
            )
            
            include_islands = st.checkbox(
                "🏝️ Szigetek",
                value=st.session_state.get('include_islands', True),
                help="Szigetországok és -területek (pl. Izland, Málta, Maldívek)"
            )
            

            
            # Állapotok mentése
            st.session_state.include_countries = include_countries
            st.session_state.include_territories = include_territories
            st.session_state.include_us_states = include_us_states
            st.session_state.include_europe = include_europe
            st.session_state.include_asia = include_asia
            st.session_state.include_africa = include_africa
            st.session_state.include_north_america = include_north_america
            st.session_state.include_central_america = include_central_america
            st.session_state.include_south_america = include_south_america
            st.session_state.include_oceania = include_oceania
            st.session_state.include_islands = include_islands
            
            # Számláló megjelenítése
            total_available = 0
            if include_countries:
                countries_count = sum(1 for code in self.countries.keys() if not code.startswith('us-') and not self._is_territory(code))
                total_available += countries_count
                st.caption(f"📊 Országok: {countries_count}")
            
            if include_territories:
                territories_count = sum(1 for code in self.countries.keys() if not code.startswith('us-') and self._is_territory(code))
                total_available += territories_count
                st.caption(f"📊 Független területek: {territories_count}")
            
            if include_us_states:
                us_states_count = sum(1 for code in self.countries.keys() if code.startswith('us-'))
                total_available += us_states_count
                st.caption(f"📊 US államok: {us_states_count}")
            
            # Kontinens statisztikák (ha nem minden van bekapcsolva)
            continent_filters = [include_europe, include_asia, include_africa, include_north_america, 
                               include_central_america, include_south_america, include_oceania, include_islands]
            if not all(continent_filters):
                continent_countries = self.search_engine.continent_countries
                continent_total = 0
                
                if include_europe:
                    continent_total += len(continent_countries.get('europe', []))
                if include_asia:
                    continent_total += len(continent_countries.get('asia', []))
                if include_africa:
                    continent_total += len(continent_countries.get('africa', []))
                if include_north_america:
                    continent_total += len(continent_countries.get('north america', []))
                if include_central_america:
                    continent_total += len(continent_countries.get('central america', []))
                if include_south_america:
                    continent_total += len(continent_countries.get('south america', []))
                if include_oceania:
                    continent_total += len(continent_countries.get('oceania', []))
                if include_islands:
                    continent_total += len(continent_countries.get('islands', []))
                
                st.caption(f"🌍 Kontinens szűrés aktív: {continent_total} terület")
            
            st.caption(f"**Összesen:** {total_available} terület")
            
            st.write("---")
            
            # Példa gombok (összecsukható)
            with st.expander("📋 Példa keresések"):
                st.write("**Alap:**")
                if st.button("🔴 Piros", key="ex_red"):
                    st.session_state.example_query = "piros zászlók"
                    st.rerun()
                
                if st.button("⭐ Csillagos", key="ex_star"):
                    st.session_state.example_query = "csillagos zászlók"
                    st.rerun()
                
                if st.button("🌍 Európai", key="ex_europe"):
                    st.session_state.example_query = "európai zászlók"
                    st.rerun()
                
                if st.button("🏝️ Szigetes", key="ex_islands"):
                    st.session_state.example_query = "szigetes zászlók"
                    st.rerun()
                
                if st.button("🌟 Egy csillag", key="ex_one_star"):
                    st.session_state.example_query = "egy csillagos zászlók"
                    st.rerun()
                
                st.write("**Speciális:**")
                if st.button("🔴⭐ Piros csillagos", key="ex_red_star"):
                    st.session_state.example_query = "piros csillagos zászlók"
                    st.rerun()
                
                if st.button("🌟🌟 Sok csillag", key="ex_many_stars"):
                    st.session_state.example_query = "sok csillagos zászlók"
                    st.rerun()
                
                if st.button("📍 Sarokban csillag", key="ex_corner_star"):
                    st.session_state.example_query = "sarokban csillag"
                    st.rerun()
                
                st.write("**Országok:**")
                if st.button("🇭🇺 Magyarország", key="ex_hungary"):
                    st.session_state.example_query = "magyarország zászló"
                    st.rerun()
                
                if st.button("🇺🇸 Amerika", key="ex_usa"):
                    st.session_state.example_query = "amerika zászló"
                    st.rerun()
                
                if st.button("🇨🇳 Kína", key="ex_china"):
                    st.session_state.example_query = "kína zászló"
                    st.rerun()
                
                st.write("**Szimbólumok:**")
                if st.button("🦅 Állatos", key="ex_animals"):
                    st.session_state.example_query = "állatos zászlók"
                    st.rerun()
                
                if st.button("🌳 Növényes", key="ex_plants"):
                    st.session_state.example_query = "növényes zászlók"
                    st.rerun()
                
                if st.button("⚔️ Fegyveres", key="ex_weapons"):
                    st.session_state.example_query = "fegyveres zászlók"
                    st.rerun()
            
            st.write("---")
            
            st.header("📋 Rendszer Állapot")
            
            # Zászlók letöltése
            flags_count = len(list(self.data_dir.glob("flags/*.png"))) if (self.data_dir / "flags").exists() else 0
            st.metric("Letöltött zászlók", flags_count)
            
            if st.button("🔄 Zászlók letöltése"):
                with st.spinner("Zászlók letöltése..."):
                    import asyncio
                    try:
                        results = asyncio.run(self.downloader.download_all_flags(size="w320", max_concurrent=5))
                        successful = sum(1 for success in results.values() if success)
                        st.success(f"✅ {successful} zászló letöltve!")
                        st.session_state.flags_downloaded = True
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Hiba: {e}")
            
            # Elemzés állapot
            features_exist = (self.data_dir / "flag_features.json").exists()
            st.write(f"**Elemzés:** {'✅ Kész' if features_exist else '❌ Hiányzik'}")
            
            if st.button("🔍 Zászlók elemzése"):
                if flags_count == 0:
                    st.warning("Először töltsd le a zászlókat!")
                else:
                    with st.spinner("Zászlók elemzése..."):
                        try:
                            features = self.analyzer.analyze_all_flags()
                            st.success(f"✅ {len(features)} zászló elemezve!")
                            st.session_state.flags_analyzed = True
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Hiba: {e}")
            
            st.write("---")
            
            # Gyors linkek
            st.header("⚡ Gyors Parancsok")
            if st.button("📊 Statisztikák"):
                st.session_state.show_stats = True
            
            if st.button("❓ Súgó"):
                st.session_state.show_help = True
        
        # Főterület - Keresési eredmények megjelenítése
        
        # Speciális megjelenítések (Súgó vagy Statisztikák)
        if st.session_state.get('show_help'):
            self.display_help()
            st.session_state.show_help = False
            return
        
        if st.session_state.get('show_stats'):
            self.display_stats()
            st.session_state.show_stats = False
            return
        
        # Kérés feldolgozása és eredmények megjelenítése
        if search_button or st.session_state.get('example_query'):
            if st.session_state.get('example_query'):
                user_input = st.session_state.example_query
                st.session_state.example_query = ""
            
            if user_input:
                # Input mező törlése a keresés után
                if 'chat_input' in st.session_state:
                    del st.session_state['chat_input']
                
                # Tiszta képernyő - csak az aktuális keresés eredményei
                st.write("---")
                
                # Válasz generálása
                response = self.handle_user_query(user_input)
                
                # Aktuális eredmények tárolása
                st.session_state.current_results = response
                
                # Vissza a tetejére gomb (eredmények előtt)
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if st.button("🔝 Vissza a tetejére", key="back_to_top_before"):
                        st.rerun()
                
                # Válasz megjelenítése
                if response.get('type') == 'search_results':
                    self.display_search_results(response['results'], response['query'])
                elif response.get('type') == 'error':
                    st.error(response['message'])
                elif response.get('type') == 'help':
                    self.display_help()
                elif response.get('type') == 'stats':
                    self.display_stats()
                elif response.get('type') == 'download_request':
                    st.info("Használd az oldalsávban a 'Zászlók letöltése' gombot!")
                elif response.get('type') == 'analyze_request':
                    st.info("Használd az oldalsávban a 'Zászlók elemzése' gombot!")
                
                # Vissza a tetejére gomb (eredmények után)
                st.write("---")
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if st.button("🔝 Vissza a tetejére", key="back_to_top_after"):
                        st.rerun()
        
        # Ha nincs aktív keresés, alapértelmezett üzenet
        elif not st.session_state.get('current_results'):
            st.write("## 🏳️ Üdvözöllek a Világzászló Keresőben!")
            st.write("Használd az oldalsávban található keresőmezőt vagy a példa gombokat egy keresés indításához.")
            st.write("---")
            
            # Gyors start példák
            st.write("### 🚀 Gyors Start:")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔴 Piros zászlók", key="quick_red"):
                    st.session_state.example_query = "piros zászlók"
                    st.rerun()
                
                if st.button("⭐ Csillagos zászlók", key="quick_star"):
                    st.session_state.example_query = "csillagos zászlók"
                    st.rerun()
            
            with col2:
                if st.button("🌍 Európai zászlók", key="quick_europe"):
                    st.session_state.example_query = "európai zászlók"
                    st.rerun()
                
                if st.button("🏝️ Szigetes zászlók", key="quick_islands"):
                    st.session_state.example_query = "szigetes zászlók"
                    st.rerun()
            
            with col3:
                if st.button("🌈 Tricolor zászlók", key="quick_tricolor"):
                    st.session_state.example_query = "tricolor zászlók"
                    st.rerun()
                
                if st.button("📊 Statisztikák", key="quick_stats"):
                    st.session_state.show_stats = True
                    st.rerun()


def main():
    """Főprogram"""
    chat_interface = FlagChatInterface()
    chat_interface.run_streamlit_app()


if __name__ == "__main__":
    main() 