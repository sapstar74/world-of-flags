"""
Világzászló Interaktív Alkalmazás - Főprogram
"""

import asyncio
import sys
from pathlib import Path
import argparse

# Helyi modulok importálása
from src.downloader import FlagDownloader
from src.analyzer import FlagAnalyzer
from src.search import FlagSearchEngine


class WorldFlagsApp:
    """Főalkalmazás osztály"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.downloader = FlagDownloader(data_dir)
        self.analyzer = FlagAnalyzer(data_dir)
        self.search_engine = FlagSearchEngine(data_dir)
    
    async def setup_data(self):
        """Adatok letöltése és elemzése"""
        print("🏳️ Világzászló Alkalmazás Inicializálása")
        print("=" * 50)
        
        # 1. Zászlók letöltése
        print("\n📥 1. Zászlók letöltése...")
        try:
            results = await self.downloader.download_all_flags(size="w320", max_concurrent=5)
            successful = sum(1 for success in results.values() if success)
            print(f"✅ {successful} zászló sikeresen letöltve!")
        except Exception as e:
            print(f"❌ Hiba a letöltés során: {e}")
            return False
        
        # 2. Zászlók elemzése
        print("\n🔍 2. Zászlók elemzése...")
        try:
            features = self.analyzer.analyze_all_flags()
            print(f"✅ {len(features)} zászló sikeresen elemezve!")
        except Exception as e:
            print(f"❌ Hiba az elemzés során: {e}")
            return False
        
        print("\n🎉 Inicializálás befejezve! Az alkalmazás használatra kész.")
        return True
    
    def interactive_search(self):
        """Interaktív keresési mód"""
        print("\n🔍 Interaktív Zászlókereső")
        print("=" * 30)
        print("Írj be keresési kifejezéseket, vagy 'quit' a kilépéshez.")
        print("Példák:")
        print("- 'piros és kék zászlók'")
        print("- 'csillagos zászlók'")
        print("- 'európai zászlók'")
        print("- 'help' - súgó megjelenítése")
        print()
        
        while True:
            try:
                query = input("🔍 Keresés: ").strip()
                
                if query.lower() in ['quit', 'exit', 'kilép']:
                    print("👋 Viszlát!")
                    break
                
                if query.lower() == 'help':
                    self.show_help()
                    continue
                
                if not query:
                    continue
                
                # Keresés végrehajtása
                results = self.search_engine.search_flags(query)
                self.display_results(results, query)
                
            except KeyboardInterrupt:
                print("\n👋 Viszlát!")
                break
            except Exception as e:
                print(f"❌ Hiba: {e}")
    
    def display_results(self, results: dict, query: str):
        """Keresési eredmények megjelenítése"""
        total_count = results.get('total_count', 0)
        search_info = results.get('search_info', {})
        flag_details = results.get('flag_details', [])
        
        print(f"\n📊 Keresési eredmények: '{query}'")
        print("-" * 40)
        
        # Keresési információk
        info_parts = []
        if search_info.get('colors'):
            info_parts.append(f"Színek: {', '.join(search_info['colors'])}")
        if search_info.get('patterns'):
            info_parts.append(f"Mintázatok: {', '.join(search_info['patterns'])}")
        if search_info.get('continents'):
            info_parts.append(f"Kontinensek: {', '.join(search_info['continents'])}")
        
        if info_parts:
            print(f"🎯 Szűrők: {' | '.join(info_parts)}")
        
        print(f"📈 Találatok: {total_count} zászló")
        
        if total_count == 0:
            print("❌ Nincs találat a keresési kritériumoknak megfelelően.")
            print("💡 Javaslatok:")
            print("   - Próbálj más színeket vagy mintázatokat")
            print("   - Használj egyszerűbb kifejezéseket")
            return
        
        # Első 10 eredmény megjelenítése
        print(f"\n🏳️ Első {min(10, len(flag_details))} eredmény:")
        for i, detail in enumerate(flag_details[:10], 1):
            colors_str = ", ".join(detail.get('colors', []))
            patterns = []
            if detail.get('has_stripes'):
                patterns.append("csíkos")
            if detail.get('has_bands'):
                patterns.append("sávos")
            if detail.get('has_stars'):
                patterns.append("csillagos")
            
            pattern_str = f" ({', '.join(patterns)})" if patterns else ""
            complexity = detail.get('complexity_score', 0)
            
            print(f"  {i:2d}. {detail['country_name']} ({detail['country_code'].upper()})")
            print(f"      Színek: {colors_str}{pattern_str}")
            if complexity > 0:
                print(f"      Komplexitás: {complexity}")
        
        if total_count > 10:
            print(f"\n... és még {total_count - 10} találat.")
    
    def show_help(self):
        """Súgó megjelenítése"""
        print("\n🤖 Zászlókereső Súgó")
        print("=" * 25)
        
        print("\n🎨 Keresési példák:")
        examples = [
            "Színek alapján: 'piros és kék zászlók', 'zöld zászlók'",
            "Mintázatok alapján: 'csillagos zászlók', 'csíkos zászlók'",
            "Kontinensek alapján: 'európai zászlók', 'ázsiai zászlók'",
            "Kombinált: 'piros csillagos zászlók', 'kék csíkos európai zászlók'"
        ]
        
        for example in examples:
            print(f"  • {example}")
        
        print("\n🌈 Támogatott színek:")
        colors = ["piros/vörös", "kék", "zöld", "sárga", "fehér", "fekete", "narancs", "lila", "rózsaszín", "barna"]
        print(f"  {', '.join(colors)}")
        
        print("\n🔷 Támogatott mintázatok:")
        patterns = ["csillag/csillagos", "csík/csíkos", "sáv/sávos", "kereszt", "kör"]
        print(f"  {', '.join(patterns)}")
        
        print("\n🌍 Támogatott kontinensek:")
        continents = ["Európa", "Ázsia", "Afrika", "Amerika", "Észak-Amerika", "Közép-Amerika", "Dél-Amerika", "Óceánia"]
        print(f"  {', '.join(continents)}")
    
    def show_stats(self):
        """Statisztikák megjelenítése"""
        features = self.analyzer.load_features()
        
        if not features:
            print("❌ Nincs elemzett adat!")
            return
        
        print("\n📊 Zászló Statisztikák")
        print("=" * 20)
        
        # Alapstatisztikák
        total_flags = len(features)
        print(f"📈 Összesen elemzett zászló: {total_flags}")
        
        # Színstatisztikák
        all_colors = []
        for flag_data in features.values():
            all_colors.extend(flag_data.get('unique_colors', []))
        
        from collections import Counter
        color_counts = Counter(all_colors)
        
        print("\n🌈 Leggyakoribb színek:")
        for color, count in color_counts.most_common(10):
            percentage = (count / total_flags) * 100
            print(f"  • {color}: {count} zászló ({percentage:.1f}%)")
        
        # Mintázat statisztikák
        stripe_count = sum(1 for f in features.values() 
                          if f.get('stripes', {}).get('has_horizontal_stripes') or
                             f.get('stripes', {}).get('has_vertical_stripes'))
        band_count = sum(1 for f in features.values() 
                         if f.get('stripes', {}).get('has_horizontal_bands') or
                            f.get('stripes', {}).get('has_vertical_bands'))
        star_count = sum(1 for f in features.values() 
                        if f.get('shapes', {}).get('stars', 0) > 0)
        
        print("\n🔷 Mintázatok:")
        print(f"  • Csíkos zászlók: {stripe_count} ({stripe_count/total_flags*100:.1f}%)")
        print(f"  • Sávos zászlók: {band_count} ({band_count/total_flags*100:.1f}%)")
        print(f"  • Csillagos zászlók: {star_count} ({star_count/total_flags*100:.1f}%)")


def main():
    """Főprogram"""
    parser = argparse.ArgumentParser(description='Világzászló Interaktív Alkalmazás')
    parser.add_argument('--setup', action='store_true', help='Adatok letöltése és elemzése')
    parser.add_argument('--search', type=str, help='Egyetlen keresés végrehajtása')
    parser.add_argument('--interactive', action='store_true', help='Interaktív keresési mód')
    parser.add_argument('--stats', action='store_true', help='Statisztikák megjelenítése')
    parser.add_argument('--streamlit', action='store_true', help='Streamlit webes felület indítása')
    parser.add_argument('--data-dir', type=str, default='data', help='Adatok könyvtára')
    
    args = parser.parse_args()
    
    app = WorldFlagsApp(args.data_dir)
    
    # Ha nincs argumentum, alapértelmezett művelet
    if not any([args.setup, args.search, args.interactive, args.stats, args.streamlit]):
        print("🏳️ Világzászló Interaktív Alkalmazás")
        print("Használat: python main.py [opciók]")
        print("\nOpciók:")
        print("  --setup          Adatok letöltése és elemzése")
        print("  --interactive    Interaktív keresési mód")
        print("  --search 'query' Egyetlen keresés")
        print("  --stats          Statisztikák")
        print("  --streamlit      Webes felület")
        print("  --help           Ez a súgó")
        print("\nPélda:")
        print("  python main.py --setup")
        print("  python main.py --interactive")
        print("  python main.py --search 'piros zászlók'")
        return
    
    try:
        # Adatok inicializálása
        if args.setup:
            asyncio.run(app.setup_data())
            return
        
        # Streamlit felület
        if args.streamlit:
            print("🌐 Streamlit webes felület indítása...")
            print("Nyisd meg a böngészőben: http://localhost:8501")
            
            try:
                # Egyszerű közvetlen futtatás
                from src.chat import FlagChatInterface
                
                # Streamlit alkalmazás közvetlenül
                chat_interface = FlagChatInterface()
                chat_interface.run_streamlit_app()
                
            except Exception as e:
                print(f"❌ Streamlit hiba: {e}")
                import traceback
                print(f"Részletek: {traceback.format_exc()}")
            
            return
        
        # Statisztikák
        if args.stats:
            app.show_stats()
            return
        
        # Egyetlen keresés
        if args.search:
            results = app.search_engine.search_flags(args.search)
            app.display_results(results, args.search)
            return
        
        # Interaktív mód
        if args.interactive:
            app.interactive_search()
            return
            
    except KeyboardInterrupt:
        print("\n👋 Alkalmazás leállítva.")
    except Exception as e:
        print(f"❌ Hiba: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 