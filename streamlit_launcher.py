#!/usr/bin/env python3
"""
Streamlit Launcher - Közvetlen indítás binárisban
"""

import streamlit as st
import sys
from pathlib import Path

# Python path beállítása
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

def main():
    """Streamlit alkalmazás indítása"""
    try:
        # Közvetlen import és indítás
        from src.chat import FlagChatInterface
        
        # Chat interface létrehozása és indítása
        chat_interface = FlagChatInterface()
        chat_interface.run_streamlit_app()
        
    except Exception as e:
        st.error(f"Hiba a Streamlit indításakor: {e}")
        import traceback
        st.error(f"Részletek: {traceback.format_exc()}")

if __name__ == "__main__":
    main() 