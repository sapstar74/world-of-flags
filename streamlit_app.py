#!/usr/bin/env python3
"""
Standalone Streamlit Application - Világzászló Kereső
"""

import streamlit as st
import sys
from pathlib import Path

# Python path beállítása
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Chat interface import
try:
    from src.chat import FlagChatInterface
    
    # Alkalmazás futtatása
    if __name__ == "__main__":
        chat_interface = FlagChatInterface()
        chat_interface.run_streamlit_app()
        
except Exception as e:
    st.error(f"Hiba a Streamlit alkalmazás betöltésekor: {e}")
    import traceback
    st.error(f"Részletek: {traceback.format_exc()}") 