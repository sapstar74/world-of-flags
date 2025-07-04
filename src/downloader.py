"""
Zászlóletöltő modul - Világzászlók letöltése a flagcdn.com API-ról
"""

import asyncio
import aiohttp
import aiofiles
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from tqdm.asyncio import tqdm
import requests


class FlagDownloader:
    """Zászlóletöltő osztály a flagcdn.com API használatával"""
    
    def __init__(self, base_dir: str = "data"):
        self.base_dir = Path(base_dir)
        self.flags_dir = self.base_dir / "flags"
        self.countries_file = self.base_dir / "countries.json"
        
        # API URL-ek
        self.codes_url = "https://flagcdn.com/en/codes.json"
        self.flag_base_url = "https://flagcdn.com"
        
        # Létrehozzuk a könyvtárakat
        self._create_directories()
    
    def _create_directories(self):
        """Szükséges könyvtárak létrehozása"""
        self.base_dir.mkdir(exist_ok=True)
        self.flags_dir.mkdir(exist_ok=True)
    
    def get_country_codes(self) -> Dict[str, str]:
        """Országkódok és nevek letöltése"""
        try:
            print("Országkódok letöltése...")
            response = requests.get(self.codes_url, timeout=10)
            response.raise_for_status()
            
            codes = response.json()
            print(f"Összesen {len(codes)} ország található")
            
            # Mentjük a countries.json fájlba
            with open(self.countries_file, 'w', encoding='utf-8') as f:
                json.dump(codes, f, ensure_ascii=False, indent=2)
            
            return codes
            
        except Exception as e:
            print(f"Hiba az országkódok letöltésekor: {e}")
            
            # Ha nem sikerül letölteni, próbáljuk betölteni a helyi fájlból
            if self.countries_file.exists():
                with open(self.countries_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            return {}
    
    async def download_flag(self, session: aiohttp.ClientSession, 
                          country_code: str, country_name: str,
                          size: str = "w320") -> Tuple[str, bool]:
        """Egyetlen zászló letöltése"""
        try:
            # Fájlnév generálása
            filename = f"{country_code}_{country_name.replace(' ', '_')}.png"
            filepath = self.flags_dir / filename
            
            # Ha már létezik, kihagyjuk
            if filepath.exists():
                return country_code, True
            
            # URL összeállítása
            flag_url = f"{self.flag_base_url}/{size}/{country_code}.png"
            
            async with session.get(flag_url) as response:
                if response.status == 200:
                    content = await response.read()
                    
                    async with aiofiles.open(filepath, 'wb') as f:
                        await f.write(content)
                    
                    return country_code, True
                else:
                    print(f"Hiba {country_code} letöltésekor: HTTP {response.status}")
                    return country_code, False
                    
        except Exception as e:
            print(f"Hiba {country_code} ({country_name}) letöltésekor: {e}")
            return country_code, False
    
    async def download_all_flags(self, size: str = "w320", 
                               max_concurrent: int = 10) -> Dict[str, bool]:
        """Összes zászló letöltése aszinkron módon"""
        
        # Országkódok beszerzése
        countries = self.get_country_codes()
        if not countries:
            print("Nem sikerült az országkódokat letölteni!")
            return {}
        
        print(f"\nZászlók letöltése kezdődik ({size} méret)...")
        print(f"Egyidejű letöltések száma: {max_concurrent}")
        
        # Aszinkron letöltés
        connector = aiohttp.TCPConnector(limit=max_concurrent)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(
            connector=connector, 
            timeout=timeout
        ) as session:
            
            # Létrehozzuk a feladatokat
            tasks = [
                self.download_flag(session, code, name, size)
                for code, name in countries.items()
            ]
            
            # Végrehajtjuk progress bar-ral
            results = {}
            
            # Egyszerű progress tracking
            print(f"Letöltés {len(tasks)} zászló...")
            completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in completed_tasks:
                if isinstance(result, tuple):
                    country_code, success = result
                    results[country_code] = success
                else:
                    print(f"Hiba egy letöltés során: {result}")
        
        # Eredmények összesítése
        successful = sum(1 for success in results.values() if success)
        failed = len(results) - successful
        
        print(f"\nLetöltés befejezve:")
        print(f"✅ Sikeres: {successful}")
        print(f"❌ Sikertelen: {failed}")
        
        return results
    
    def get_downloaded_flags(self) -> List[Dict[str, str]]:
        """Letöltött zászlók listájának visszaadása"""
        flags = []
        
        if not self.flags_dir.exists():
            return flags
        
        for flag_file in self.flags_dir.glob("*.png"):
            # Fájlnév elemzése: {country_code}_{country_name}.png
            name_parts = flag_file.stem.split('_', 1)
            if len(name_parts) >= 2:
                country_code = name_parts[0]
                country_name = name_parts[1].replace('_', ' ')
                
                flags.append({
                    'code': country_code,
                    'name': country_name,
                    'file': str(flag_file),
                    'filename': flag_file.name
                })
        
        return sorted(flags, key=lambda x: x['name'])
    
    def get_flag_info(self) -> Dict[str, Dict]:
        """Zászlók és országok információinak összesítése"""
        countries = {}
        
        # Országkódok betöltése
        if self.countries_file.exists():
            with open(self.countries_file, 'r', encoding='utf-8') as f:
                country_codes = json.load(f)
        else:
            country_codes = {}
        
        # Letöltött zászlók
        downloaded_flags = self.get_downloaded_flags()
        
        for flag in downloaded_flags:
            code = flag['code']
            countries[code] = {
                'name': flag['name'],
                'code': code,
                'flag_file': flag['file'],
                'downloaded': True,
                'official_name': country_codes.get(code, flag['name'])
            }
        
        return countries


# Kontinensek és régiók adatai
CONTINENTS = {
    'AF': 'Africa',
    'AS': 'Asia', 
    'EU': 'Europe',
    'NA': 'North America',
    'SA': 'South America',
    'OC': 'Oceania',
    'AN': 'Antarctica'
}

# Országok kontinens szerinti besorolása (részleges lista)
COUNTRY_CONTINENTS = {
    # Europa
    'de': 'EU', 'fr': 'EU', 'it': 'EU', 'es': 'EU', 'gb': 'EU', 'pl': 'EU',
    'nl': 'EU', 'be': 'EU', 'ch': 'EU', 'at': 'EU', 'se': 'EU', 'no': 'EU',
    'dk': 'EU', 'fi': 'EU', 'ie': 'EU', 'pt': 'EU', 'gr': 'EU', 'cz': 'EU',
    'hu': 'EU', 'ro': 'EU', 'bg': 'EU', 'hr': 'EU', 'sk': 'EU', 'si': 'EU',
    
    # Ázsia
    'cn': 'AS', 'jp': 'AS', 'in': 'AS', 'kr': 'AS', 'th': 'AS', 'id': 'AS',
    'my': 'AS', 'sg': 'AS', 'ph': 'AS', 'vn': 'AS', 'tw': 'AS', 'hk': 'AS',
    'mn': 'AS', 'kz': 'AS', 'uz': 'AS', 'af': 'AS', 'pk': 'AS', 'bd': 'AS',
    
    # Észak-Amerika
    'us': 'NA', 'ca': 'NA', 'mx': 'NA', 'gt': 'NA', 'bz': 'NA', 'sv': 'NA',
    'hn': 'NA', 'ni': 'NA', 'cr': 'NA', 'pa': 'NA', 'cu': 'NA', 'jm': 'NA',
    
    # Dél-Amerika
    'br': 'SA', 'ar': 'SA', 'cl': 'SA', 'pe': 'SA', 'co': 'SA', 've': 'SA',
    'ec': 'SA', 'bo': 'SA', 'py': 'SA', 'uy': 'SA', 'sr': 'SA', 'gy': 'SA',
    
    # Afrika
    'za': 'AF', 'eg': 'AF', 'ng': 'AF', 'ke': 'AF', 'ma': 'AF', 'et': 'AF',
    'gh': 'AF', 'ug': 'AF', 'dz': 'AF', 'tn': 'AF', 'ly': 'AF', 'sd': 'AF',
    
    # Óceánia
    'au': 'OC', 'nz': 'OC', 'fj': 'OC', 'pg': 'OC', 'sb': 'OC', 'vu': 'OC'
}


async def main():
    """Főprogram - tesztelés"""
    downloader = FlagDownloader()
    
    # Zászlók letöltése
    results = await downloader.download_all_flags(size="w320", max_concurrent=5)
    
    # Eredmények megjelenítése
    print(f"\nLetöltött zászlók száma: {len(downloader.get_downloaded_flags())}")
    
    # Zászló információk
    flag_info = downloader.get_flag_info()
    print(f"Elérhető országok: {len(flag_info)}")


if __name__ == "__main__":
    asyncio.run(main()) 