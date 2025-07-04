"""
Demo script - Egyszerű tesztelés a világzászló alkalmazáshoz
"""

import asyncio
from pathlib import Path


async def demo_download():
    """Demo: Zászlók letöltése"""
    print("🏳️ Demo: Zászlók letöltése")
    print("=" * 30)
    
    from src.downloader import FlagDownloader
    
    downloader = FlagDownloader("data")
    
    # Országkódok lekérése
    print("📋 Országkódok lekérése...")
    countries = downloader.get_country_codes()
    print(f"✅ {len(countries)} ország kódja letöltve")
    
    # Első 5 zászló letöltése tesztként
    print("\n📥 Első 5 zászló letöltése tesztként...")
    test_countries = list(countries.items())[:5]
    
    # Aszinkron session létrehozása a letöltéshez
    import aiohttp
    
    async with aiohttp.ClientSession() as session:
        for code, name in test_countries:
            print(f"  Letöltés: {name} ({code})")
            try:
                result = await downloader.download_flag(session, code, name)
                if result[1]:
                    print(f"    ✅ Sikeres")
                else:
                    print(f"    ❌ Sikertelen")
            except Exception as e:
                print(f"    ❌ Hiba: {e}")
    
    print(f"\n📊 Letöltött zászlók: {len(downloader.get_downloaded_flags())}")


def demo_search():
    """Demo: Keresési funkciók"""
    print("\n🔍 Demo: Keresési funkciók")
    print("=" * 30)
    
    from src.search import FlagSearchEngine
    
    search_engine = FlagSearchEngine("data")
    
    # Teszt kérések
    test_queries = [
        "piros zászlók",
        "kék és fehér zászlók", 
        "európai zászlók",
        "csillagos zászlók"
    ]
    
    print("🧪 Teszt kérések:")
    for query in test_queries:
        print(f"\n  Kérés: '{query}'")
        
        # Színek kinyerése
        colors = search_engine.extract_colors(query)
        if colors:
            print(f"    Színek: {colors}")
        
        # Mintázatok kinyerése
        patterns = search_engine.extract_patterns(query)
        if patterns:
            print(f"    Mintázatok: {patterns}")
        
        # Kontinensek kinyerése
        continents = search_engine.extract_continents(query)
        if continents:
            print(f"    Kontinensek: {continents}")


def demo_analyzer():
    """Demo: Elemzési funkciók"""
    print("\n🔍 Demo: Elemzési funkciók")
    print("=" * 30)
    
    from src.analyzer import FlagAnalyzer
    
    analyzer = FlagAnalyzer("data")
    
    # Letöltött zászlók ellenőrzése
    flags_dir = Path("data/flags")
    if not flags_dir.exists():
        print("❌ Nincsenek letöltött zászlók!")
        print("   Először futtasd: python demo.py download")
        return
    
    flag_files = list(flags_dir.glob("*.png"))
    print(f"📁 Elérhető zászló fájlok: {len(flag_files)}")
    
    if flag_files:
        # Első zászló elemzése
        test_flag = flag_files[0]
        print(f"\n🧪 Teszt elemzés: {test_flag.name}")
        
        try:
            features = analyzer.analyze_flag(str(test_flag))
            if features:
                print("✅ Elemzés sikeres!")
                print(f"  Színek: {features.get('unique_colors', [])}")
                print(f"  Színek száma: {features.get('color_count', 0)}")
                print(f"  Komplexitás: {features.get('complexity_score', 0)}")
                
                stripes = features.get('stripes', {})
                if stripes.get('has_horizontal_stripes'):
                    print("  Vízszintes csíkok: ✅")
                if stripes.get('has_vertical_stripes'):
                    print("  Függőleges csíkok: ✅")
                
                shapes = features.get('shapes', {})
                if shapes.get('stars', 0) > 0:
                    print(f"  Csillagok: {shapes['stars']} db")
            else:
                print("❌ Elemzés sikertelen")
                
        except Exception as e:
            print(f"❌ Hiba az elemzés során: {e}")


def main():
    """Főprogram"""
    import sys
    
    if len(sys.argv) < 2:
        print("🏳️ Világzászló Alkalmazás Demo")
        print("=" * 35)
        print("\nHasználat:")
        print("  python demo.py download   - Zászlók letöltése demo")
        print("  python demo.py search     - Keresési funkciók demo")
        print("  python demo.py analyze    - Elemzési funkciók demo")
        print("  python demo.py all        - Minden demo futtatása")
        return
    
    command = sys.argv[1].lower()
    
    try:
        if command == "download":
            asyncio.run(demo_download())
        elif command == "search":
            demo_search()
        elif command == "analyze":
            demo_analyzer()
        elif command == "all":
            asyncio.run(demo_download())
            demo_search()
            demo_analyzer()
        else:
            print(f"❌ Ismeretlen parancs: {command}")
            
    except KeyboardInterrupt:
        print("\n👋 Demo leállítva")
    except Exception as e:
        print(f"❌ Hiba: {e}")


if __name__ == "__main__":
    main() 