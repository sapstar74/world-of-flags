"""
Egyszerű Streamlit test - Világzászló Kereső
"""

import streamlit as st
from pathlib import Path
import sys
import json

# Import beállítások
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

try:
    from search import FlagSearchEngine
    
    st.set_page_config(
        page_title="🏳️ Világzászló Kereső",
        page_icon="🏳️",
        layout="wide"
    )
    
    st.title("🏳️ Világzászló Kereső - Teszt Verzió")
    
    # Keresési mező
    user_input = st.text_input("Keresés:", placeholder="Pl.: piros zászlók")
    
    if st.button("Keresés") and user_input:
        try:
            data_dir = Path(__file__).parent.parent / "data"
            search_engine = FlagSearchEngine(data_dir)
            
            results = search_engine.search_flags(user_input)
            
            if results and 'flag_details' in results:
                st.success(f"Találatok: {results['total_count']}")
                
                for detail in results['flag_details'][:10]:  # Első 10 eredmény
                    st.write(f"**{detail['country_name']}** ({detail['country_code']})")
                    if detail.get('colors'):
                        st.write(f"Színek: {', '.join(detail['colors'])}")
            else:
                st.warning("Nincs találat")
                
        except Exception as e:
            st.error(f"Hiba: {e}")
    
    st.write("---")
    st.write("Ez egy egyszerűsített teszt verzió.")
    
except ImportError as e:
    st.error(f"Import hiba: {e}")
    st.write("Ellenőrizd, hogy a search.py fájl elérhető-e!") 