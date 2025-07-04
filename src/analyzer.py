"""
Zászlóelemző modul - Színek, formák és ábrák felismerése zászlóképeken
"""

import cv2
import numpy as np
from PIL import Image
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any
import webcolors
from collections import Counter
from sklearn.cluster import KMeans
import math


class FlagAnalyzer:
    """Zászlóelemző osztály színek, formák és szimbólumok felismerésére"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.flags_dir = self.data_dir / "flags"
        self.features_file = self.data_dir / "flag_features.json"
        
        # Színkategóriák definiálása
        self.color_categories = {
            'red': [(255, 0, 0), (220, 20, 60), (178, 34, 34), (255, 69, 0)],
            'blue': [(0, 0, 255), (0, 0, 139), (25, 25, 112), (72, 61, 139)],  # Sötét kékek
            'lightblue': [(135, 206, 235), (173, 216, 230), (0, 191, 255), (30, 144, 255), (100, 149, 237)],  # Világos kékek
            'darkblue': [(0, 0, 139), (25, 25, 112), (0, 0, 128), (72, 61, 139)],  # Sötét kékek
            'green': [(0, 255, 0), (34, 139, 34), (0, 128, 0), (124, 252, 0)],
            'lightgreen': [(144, 238, 144), (152, 251, 152), (173, 255, 47), (127, 255, 0)],  # Világos zöldek
            'darkgreen': [(0, 100, 0), (34, 139, 34), (0, 128, 0), (85, 107, 47)],  # Sötét zöldek
            'yellow': [(255, 255, 0), (255, 215, 0), (255, 165, 0), (255, 140, 0)],
            'white': [(255, 255, 255), (248, 248, 255), (245, 245, 245)],
            'black': [(0, 0, 0), (47, 79, 79), (25, 25, 112)],
            'orange': [(255, 165, 0), (255, 140, 0), (255, 69, 0)],
            'purple': [(128, 0, 128), (75, 0, 130), (138, 43, 226)],
            'pink': [(255, 192, 203), (255, 20, 147), (219, 112, 147)],
            'brown': [(139, 69, 19), (160, 82, 45), (210, 180, 140)]
        }
    
    def load_image(self, image_path: str) -> Tuple[np.ndarray, np.ndarray]:
        """Kép betöltése OpenCV és PIL formátumban"""
        # OpenCV formátum (BGR)
        cv_image = cv2.imread(image_path)
        if cv_image is None:
            raise ValueError(f"Nem sikerült betölteni a képet: {image_path}")
        
        # RGB formátum
        rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        
        return cv_image, rgb_image
    
    def extract_dominant_colors(self, image: np.ndarray, n_colors: int = 5, min_percentage: float = 1.0) -> List[Dict]:
        """Domináns színek kinyerése K-means klaszterezéssel"""
        # Kép átméretezése a gyorsabb feldolgozásért
        height, width = image.shape[:2]
        if height * width > 50000:  # Ha túl nagy
            scale = math.sqrt(50000 / (height * width))
            new_height = int(height * scale)
            new_width = int(width * scale)
            image = cv2.resize(image, (new_width, new_height))
        
        # Pixelek átformázása
        pixels = image.reshape(-1, 3)
        
        # K-means klaszterezés
        kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=10)
        kmeans.fit(pixels)
        
        # Színek és arányaik
        colors = kmeans.cluster_centers_.astype(int)
        labels = kmeans.labels_
        
        # Színek gyakorisága
        color_counts = Counter(labels)
        total_pixels = len(labels)
        
        dominant_colors = []
        for i, color in enumerate(colors):
            count = color_counts[i]
            percentage = (count / total_pixels) * 100
            
            # Kiszűrjük a túl kis százalékú színeket (zaj)
            if percentage < min_percentage:
                continue
            
            # Színnév meghatározása
            color_name = self.get_color_name(tuple(color))
            
            dominant_colors.append({
                'rgb': tuple(color),
                'hex': f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}",
                'name': color_name,
                'percentage': round(percentage, 2)
            })
        
        # Rendezés arány szerint
        return sorted(dominant_colors, key=lambda x: x['percentage'], reverse=True)
    
    def get_color_name(self, rgb_color: Tuple[int, int, int]) -> str:
        """RGB szín neve meghatározása finomabb kategorizálással"""
        try:
            # Pontos színnév keresése
            closest_name = webcolors.rgb_to_name(rgb_color)
            return closest_name
        except ValueError:
            # Legközelebbi színkategória keresése
            min_distance = float('inf')
            closest_category = 'unknown'
            
            for category, category_colors in self.color_categories.items():
                for cat_color in category_colors:
                    distance = sum((a - b) ** 2 for a, b in zip(rgb_color, cat_color))
                    if distance < min_distance:
                        min_distance = distance
                        closest_category = category
            
            # Speciális fekete szín felismerés - szigorúbb küszöb
            r, g, b = rgb_color
            if max(r, g, b) < 40:  # Csak nagyon sötét színek legyenek feketék
                return 'black'
            
            # Speciális kék árnyalatok felismerése
            if b > r and b > g:  # Kék dominál
                if b > 180 and (r + g) < 200:  # Világos kék
                    if r > 100 or g > 100:  # Van benne világosság
                        return 'lightblue'
                    else:  # Sötét kék
                        return 'darkblue'
                elif b > 120:  # Közepes kék
                    return 'blue'
            
            # Speciális zöld árnyalatok felismerése
            if g > r and g > b:  # Zöld dominál
                if g > 180 and (r + b) < 200:  # Világos zöld
                    if r > 100 or b > 100:
                        return 'lightgreen'
                    else:
                        return 'darkgreen'
            
            # Ha fekete lett volna, de nem elég sötét, akkor a legközelebbi kategóriát adjuk vissza
            if closest_category == 'black' and max(r, g, b) >= 40:
                # Keressük a második legközelebbi színt
                second_min_distance = float('inf')
                second_category = 'unknown'
                for category, category_colors in self.color_categories.items():
                    if category == 'black':
                        continue
                    for cat_color in category_colors:
                        distance = sum((a - b) ** 2 for a, b in zip(rgb_color, cat_color))
                        if distance < second_min_distance:
                            second_min_distance = distance
                            second_category = category
                return second_category
            
            return closest_category
    
    def detect_stripes(self, image: np.ndarray) -> Dict[str, Any]:
        """Csíkok és sávok felismerése a zászlón"""
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        height, width = gray.shape
        
        # Vízszintes csíkok/sávok detektálása
        horizontal_profile = np.mean(gray, axis=1)
        horizontal_diff = np.abs(np.diff(horizontal_profile))
        horizontal_peaks = len([x for x in horizontal_diff if x > np.std(horizontal_diff)])
        
        # Függőleges csíkok/sávok detektálása  
        vertical_profile = np.mean(gray, axis=0)
        vertical_diff = np.abs(np.diff(vertical_profile))
        vertical_peaks = len([x for x in vertical_diff if x > np.std(vertical_diff)])
        
        # Sáv vs csík megkülönböztetés (sáv = kevesebb, de szélesebb rész)
        # Csík: sok keskeny rész (>4), Sáv: kevés széles rész (2-4)
        has_horizontal_bands = 2 <= horizontal_peaks <= 4
        has_vertical_bands = 2 <= vertical_peaks <= 4
        has_horizontal_stripes = horizontal_peaks > 4
        has_vertical_stripes = vertical_peaks > 4
        
        return {
            'has_horizontal_stripes': has_horizontal_stripes,
            'has_vertical_stripes': has_vertical_stripes,
            'has_horizontal_bands': has_horizontal_bands,
            'has_vertical_bands': has_vertical_bands,
            'horizontal_stripe_count': horizontal_peaks,
            'vertical_stripe_count': vertical_peaks
        }
    
    def detect_geometric_shapes(self, image: np.ndarray) -> Dict[str, Any]:
        """Geometriai formák felismerése"""
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        
        # Többféle módszerrel keressük a csillagokat
        shapes = {
            'circles': 0,
            'triangles': 0,
            'rectangles': 0,
            'stars': 0,
            'crosses': 0,
            'total_shapes': 0
        }
        
        # 1. Kontúr alapú keresés
        edges = cv2.Canny(gray, 30, 100, apertureSize=3)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 50:  # Kisebb küszöb a csillagokhoz
                continue
            
            # Közelítő poligon
            epsilon = 0.015 * cv2.arcLength(contour, True)  # Pontosabb közelítés
            approx = cv2.approxPolyDP(contour, epsilon, True)
            vertices = len(approx)
            
            # Konvex hull és konkávitás ellenőrzése (csillag jellemző)
            try:
                hull = cv2.convexHull(contour, returnPoints=False)
                if len(hull) > 3:  # Legalább 4 pont szükséges
                    defects = cv2.convexityDefects(contour, hull)
                    if defects is not None and len(defects) >= 3:  # Legalább 3 konkáv pont
                        shapes['stars'] += 1
                        continue
            except:
                pass  # Ha hiba van, folytassuk a többi ellenőrzéssel
            
            if vertices == 3:
                shapes['triangles'] += 1
            elif vertices == 4:
                shapes['rectangles'] += 1
            elif vertices > 8:
                # Kör ellenőrzése
                (x, y), radius = cv2.minEnclosingCircle(contour)
                circle_area = np.pi * radius * radius
                if abs(area - circle_area) / circle_area < 0.3:
                    shapes['circles'] += 1
                else:
                    shapes['stars'] += 1
            elif 5 <= vertices <= 8:
                shapes['stars'] += 1
        
        # 2. Template matching csillagokhoz (egyszerű heurisztika)
        # Keressük a tipikus csillag formákat
        star_patterns = self.detect_star_patterns(gray)
        shapes['stars'] += star_patterns
        
        # 3. Kereszt felismerés
        cross_patterns = self.detect_cross_patterns(gray)
        shapes['crosses'] += cross_patterns
        
        shapes['total_shapes'] = shapes['circles'] + shapes['triangles'] + shapes['rectangles'] + shapes['stars'] + shapes['crosses']
        
        return shapes
    
    def detect_star_patterns(self, gray: np.ndarray) -> int:
        """Csillag mintázatok felismerése heurisztikával"""
        height, width = gray.shape
        stars = 0
        
        # Keressük a sötét pontokat világos háttéren (vagy fordítva)
        # Tipikus csillag pozíciók a zászlókon
        regions = [
            (0, 0, width//3, height//3),  # Bal felső
            (width//3, height//3, 2*width//3, 2*height//3),  # Közép
            (0, height//3, width//2, 2*height//3),  # Bal közép
        ]
        
        for x1, y1, x2, y2 in regions:
            region = gray[y1:y2, x1:x2]
            if region.size == 0:
                continue
                
            # Threshold alkalmazása
            _, thresh = cv2.threshold(region, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Kis objektumok keresése (potenciális csillagok)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if 20 < area < 1000:  # Megfelelő méretű objektumok
                    # Kompaktság ellenőrzése (csillag jellemző)
                    perimeter = cv2.arcLength(contour, True)
                    if perimeter > 0:
                        compactness = 4 * np.pi * area / (perimeter * perimeter)
                        if 0.1 < compactness < 0.7:  # Csillag-szerű kompaktság
                            stars += 1
        
        return min(stars, 10)  # Maximum 10 csillag per zászló
    
    def detect_cross_patterns(self, gray: np.ndarray) -> int:
        """Kereszt mintázatok felismerése"""
        height, width = gray.shape
        crosses = 0
        
        # Vízszintes és függőleges vonalak keresése
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (width//4, 3))
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, height//4))
        
        # Morfológiai műveletek
        horizontal_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, horizontal_kernel)
        vertical_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, vertical_kernel)
        
        # Kereszteződések keresése
        combined = cv2.bitwise_and(horizontal_lines, vertical_lines)
        
        # Ha van jelentős átfedés, akkor kereszt
        if np.sum(combined > 100) > width * height * 0.01:  # Legalább 1% átfedés
            crosses = 1
        
        return crosses
    
    def detect_symbolic_elements(self, image: np.ndarray, country_code: str) -> Dict[str, Any]:
        """Szimbolikus elemek felismerése (ember, állat, növény, fegyver)"""
        # Tudásbázis alapú felismerés - országkód alapján
        symbolic_elements = {
            'has_human': False,
            'has_animal': False, 
            'has_plant': False,
            'has_weapon': False,
            'has_building': False,
            'has_celestial': False,  # Hold, nap, csillagok
            'has_union_jack': False,  # Union Jack (brit zászló)
            'has_cross': False,  # Keresztek (latin, görög, skandináv, stb.)
            'has_crescent': False,  # Félhold
            'details': []
        }
        
        # Ember/emberi alak (címerekben, szimbólumokban)
        human_countries = {
            'md': 'eagle with human elements',  # Moldova - sas emberi elemekkel
            'al': 'double-headed eagle',        # Albánia - kétfejű sas
            'rs': 'coat of arms with crown',    # Szerbia - címer koronával
            'me': 'coat of arms with crown',    # Montenegró - címer koronával
            'ba': 'coat of arms',               # Bosznia - címer
            'mk': 'sun with human face',        # Macedónia - nap emberi arccal
            'im': 'three legs (triskelion)',    # Man-sziget - három láb
            'si': 'coat of arms with Triglav',  # Szlovénia - címer Triglavval
            'sk': 'double cross',               # Szlovákia - kettős kereszt
            'hr': 'coat of arms with crown',    # Horvátország - címer koronával
            'es': 'coat of arms',               # Spanyolország - címer
            'pt': 'coat of arms',               # Portugália - címer
            'ad': 'coat of arms',               # Andorra - címer
            'sm': 'coat of arms with towers',   # San Marino - címer tornyokkal
        }
        
        # Állatok (főként címerekben)
        animal_countries = {
            'al': 'double-headed eagle',        # Albánia - kétfejű sas
            'md': 'eagle',                      # Moldova - sas
            'me': 'eagle',                      # Montenegró - sas
            'rs': 'eagle',                      # Szerbia - sas
            'za': 'springbok and other animals', # Dél-Afrika - springbok és más állatok
            'zm': 'eagle',                      # Zambia - sas
            'zw': 'bird (Zimbabwe bird)',       # Zimbabwe - Zimbabwe madár
            'ug': 'crane',                      # Uganda - daru
            'ke': 'lion and cock',              # Kenya - oroszlán és kakas
            'mw': 'lion',                       # Malawi - oroszlán
            'ls': 'horse',                      # Lesotho - ló
            'sz': 'lion and elephant',          # Szváziföld - oroszlán és elefánt
            'fj': 'dove',                       # Fiji - galamb
            'pg': 'bird of paradise',           # Pápua Új-Guinea - paradicsommadár
            'sb': 'eagle',                      # Salamon-szigetek - sas
            'vu': 'boar tusk',                  # Vanuatu - vaddisznó agyar
            'bt': 'dragon',                     # Bhután - sárkány
            'lk': 'lion',                       # Srí Lanka - oroszlán
            'kg': 'eagle',                      # Kirgizisztán - sas
            'kz': 'eagle',                      # Kazahsztán - sas
            'mn': 'horse (soyombo symbol)',     # Mongólia - ló (soyombo szimbólum)
            'pe': 'vicuña',                     # Peru - vikunya
            'bo': 'condor',                     # Bolívia - kondor
            'ec': 'condor',                     # Ecuador - kondor
            'gt': 'quetzal bird',               # Guatemala - quetzal madár
            'mx': 'eagle',                      # Mexikó - sas
            'do': 'parrot',                     # Dominikai Köztársaság - papagáj
            'gd': 'nutmeg (armadillo)',         # Grenada - szerecsendió (tatú)
            'ag': 'sun with bird',              # Antigua és Barbuda - nap madárral
            'bb': 'trident with fish',          # Barbados - háromágú szigony hallal
            'bz': 'jaguar and tree',            # Belize - jaguár és fa
            'pa': 'harpy eagle',                # Panama - hárpia sas
            'py': 'lion',                       # Paraguay - oroszlán
            've': 'horse',                      # Venezuela - ló
            'gf': 'rooster',                    # Francia Guyana - kakas
            'gy': 'jaguar',                     # Guyana - jaguár
            # Union Jack-es zászlók állatokkal
            'au': 'kangaroo and emu',           # Ausztrália - kenguru és emu (címerben)
            'nz': 'kiwi bird',                  # Új-Zéland - kiwi madár (címerben)
            'tc': 'lobster and conch',          # Turks és Caicos - languszta és kagyló (címerben)
            'fk': 'sheep',                      # Falkland-szigetek - bárány (címerben)
            'bm': 'lion',                       # Bermuda - oroszlán (címerben)
            'ky': 'sea turtle',                 # Kajmán-szigetek - tengeri teknős (címerben)
        }
        
        # Növények - CSAK valóban látható növényeket tartalmazó zászlók
        plant_countries = {
            # Nyilvánvaló növények a zászlón
            'ca': 'red maple leaf',             # Kanada - piros juharlevél (központi elem)
            'lb': 'green cedar tree',           # Libanon - zöld cédrusfa (központi elem)
            'cy': 'olive branches',             # Ciprus - olajfa ágak (térkép alatt)
            'bz': 'mahogany tree',              # Belize - mahagóni fa (címerben)
            'nf': 'norfolk pine tree',          # Norfolk-sziget - Norfolk fenyő (címerben)
            
            # Kisebb növény elemek címerekben (csak biztos esetek)
            'fj': 'coconut palm',               # Fiji - kókuszpálma (címerben)
            'sc': 'coco de mer palm',           # Seychelle-szigetek - coco de mer pálma (címerben)
            'vu': 'fern leaf',                  # Vanuatu - páfránylevél (címerben)
            'pg': 'bird of paradise plant',     # Pápua Új-Guinea - paradicsommadár növény (címerben)
            'sl': 'oil palm tree',              # Sierra Leone - olajpálma (címerben)
            
            # Egyéb biztos növény esetek
            'cc': 'coconut palm and crescent',  # Kókusz-szigetek - kókuszpálma és félhold
            'tc': 'cactus plant',               # Turks és Caicos - kaktusz (címerben)
            
            # Hiányzó országok növényekkel
            'mo': 'lotus flower',               # Macau - lótuszvirág (címerben)
            'hk': 'bauhinia flower',            # Hong Kong - bauhinia virág (címerben)
            'er': 'olive branch',               # Eritrea - olajág (címerben)
            'gt': 'quetzal bird and ceiba tree', # Guatemala - quetzal madár és ceiba fa (címerben)
            'ht': 'palm tree',                  # Haiti - pálmafa (címerben)
            'sm': 'oak and laurel branches',    # San Marino - tölgy és babér ágak (címerben)
            've': 'orchid flower',              # Venezuela - orchidea virág (címerben)
            'pe': 'vicuña and cinchona tree',   # Peru - vicuña és cinchona fa (címerben)
            'mx': 'cactus and eagle',           # Mexikó - kaktusz és sas (címerben)
            'ec': 'condor and mountain plants', # Ecuador - kondor és hegyi növények (címerben)
            'cr': 'coffee plant',               # Costa Rica - kávéplanta (címerben)
        }
        
        # Fegyverek (kardok, nyilak, lándzsák)
        weapon_countries = {
            'sa': 'sword',                      # Szaúd-Arábia - kard
            'ao': 'machete and gear',           # Angola - machete és fogaskerék
            'mz': 'rifle and hoe',              # Mozambik - puska és kapa
            'ke': 'spears and shield',          # Kenya - lándzsák és pajzs
            'sz': 'spear and shield',           # Szváziföld - lándzsa és pajzs
            'ls': 'club and shield',            # Lesotho - buzogány és pajzs
            'bw': 'gear wheels',                # Botswana - fogaskerekek
            'zm': 'eagle over tools',           # Zambia - sas szerszámok felett
            'zw': 'rifle and hoe',              # Zimbabwe - puska és kapa
            'ug': 'spear',                      # Uganda - lándzsa
            'mw': 'sun over spear',             # Malawi - nap lándzsa felett
            'za': 'spear and knobkerrie',       # Dél-Afrika - lándzsa és buzogány
            'na': 'sun and eagle',              # Namíbia - nap és sas
            'bz': 'tools and weapons',          # Belize - szerszámok és fegyverek
            'gt': 'rifles crossed',             # Guatemala - keresztezett puskák
            'ni': 'volcano and tools',          # Nicaragua - vulkán és szerszámok
            'ht': 'cannon and flags',           # Haiti - ágyú és zászlók
            'do': 'bible and cross',            # Dominikai Köztársaság - biblia és kereszt
            'bb': 'trident',                    # Barbados - háromágú szigony
            'ag': 'anchor',                     # Antigua és Barbuda - horgony
            'kn': 'sugar mill',                 # Saint Kitts és Nevis - cukormalom
            'lc': 'roses and bamboo',           # Saint Lucia - rózsák és bambusz
            'vc': 'gems',                       # Saint Vincent és Grenadines - drágakövek
            'gd': 'nutmeg',                     # Grenada - szerecsendió
            'tt': 'birds and ships',            # Trinidad és Tobago - madarak és hajók
            'sr': 'star over tools',            # Suriname - csillag szerszámok felett
            'gy': 'arrowhead',                  # Guyana - nyílhegy
            'gf': 'canoe',                      # Francia Guyana - kenu
            'br': 'order and progress',         # Brazília - rend és haladás
            'ar': 'sun with face',              # Argentína - nap arccal
            'cl': 'condor and deer',            # Chile - kondor és szarvas
            'pe': 'tree and cornucopia',        # Peru - fa és bőségszaru
            'bo': 'llama and tree',             # Bolívia - láma és fa
            'ec': 'condor and mountain',        # Ecuador - kondor és hegy
            'co': 'condor and cornucopia',      # Kolumbia - kondor és bőségszaru
            've': 'horse and cornucopia',       # Venezuela - ló és bőségszaru
            'py': 'star and wreath',            # Paraguay - csillag és koszorú
            'uy': 'sun and stripes',            # Uruguay - nap és csíkok
        }
        
        # Épületek/építmények
        building_countries = {
            'kh': 'angkor wat',                 # Kambodzsa - Angkor Wat
            'af': 'mosque',                     # Afganisztán - mecset
            'iq': 'takbir (god is great)',      # Irak - takbir
            'ir': 'sword and tulip',            # Irán - kard és tulipán
            'sa': 'sword and palm tree',        # Szaúd-Arábia - kard és pálmafa
            'ae': 'falcon',                     # Egyesült Arab Emírségek - sólyom
            'bh': 'dhow boat',                  # Bahrein - dhow csónak
            'qa': 'serrated edge',              # Katar - fogazott él
            'kw': 'dhow boat',                  # Kuvait - dhow csónak
            'om': 'khanjar dagger',             # Omán - khanjar tőr
            'ye': 'eagle',                      # Jemen - sas
            'jo': 'seven pointed star',         # Jordánia - hétágú csillag
            'sy': 'hawk of quraish',            # Szíria - Quraish sólyom
            'lb': 'cedar tree',                 # Libanon - cédrusfa
            'il': 'star of david',              # Izrael - Dávid csillaga
            'ps': 'eagle',                      # Palesztina - sas
            'cy': 'dove and olive branch',      # Ciprus - galamb és olajág
            'tr': 'crescent and star',          # Törökország - félhold és csillag
            'gr': 'cross',                      # Görögország - kereszt
            'bg': 'coat of arms',               # Bulgária - címer
            'ro': 'coat of arms',               # Románia - címer
            'hu': 'coat of arms',               # Magyarország - címer
            'sk': 'double cross',               # Szlovákia - kettős kereszt
            'cz': 'coat of arms',               # Csehország - címer
            'pl': 'eagle',                      # Lengyelország - sas
            'de': 'federal eagle',              # Németország - szövetségi sas
            'at': 'federal eagle',              # Ausztria - szövetségi sas
            'ch': 'swiss cross',                # Svájc - svájci kereszt
            'li': 'crown',                      # Liechtenstein - korona
            'lu': 'coat of arms',               # Luxemburg - címer
            'be': 'coat of arms',               # Belgium - címer
            'nl': 'coat of arms',               # Hollandia - címer
            'fr': 'tricolor',                   # Franciaország - tricolor
            'mc': 'coat of arms',               # Monaco - címer
            'ad': 'coat of arms',               # Andorra - címer
            'es': 'coat of arms',               # Spanyolország - címer
            'pt': 'coat of arms',               # Portugália - címer
            'it': 'coat of arms',               # Olaszország - címer
            'sm': 'towers',                     # San Marino - tornyok
            'va': 'papal keys',                 # Vatikán - pápai kulcsok
            'mt': 'george cross',               # Málta - György kereszt
            'si': 'triglav mountain',           # Szlovénia - Triglav hegy
            'hr': 'coat of arms',               # Horvátország - címer
            'ba': 'coat of arms',               # Bosznia - címer
            'rs': 'coat of arms',               # Szerbia - címer
            'me': 'coat of arms',               # Montenegró - címer
            'mk': 'sun of vergina',             # Macedónia - Vergina nap
            'xk': 'map and stars',              # Koszovó - térkép és csillagok
            'cr': 'volcanoes and sea',          # Costa Rica - vulkánok és tenger (landscape)
            'sv': 'volcanoes',                  # Salvador - vulkánok (landscape)
            'ni': 'volcanoes',                  # Nicaragua - vulkánok (landscape)
            'bw': 'pattern design',             # Botswana - mintázat design
        }
        
        # Égi testek (nap, hold, csillagok - már meglévő csillag adatokkal kiegészítve)
        celestial_countries = {
            'ar': 'sun with face',              # Argentína - nap arccal
            'uy': 'sun with face',              # Uruguay - nap arccal
            'mk': 'sun with rays',              # Macedónia - nap sugarakkal
            'rw': 'sun',                        # Ruanda - nap
            'mw': 'sun',                        # Malawi - nap
            'na': 'sun',                        # Namíbia - nap
            'ki': 'sun over waves',             # Kiribati - nap hullámok felett
            'ne': 'sun',                        # Niger - nap
            'jp': 'sun',                        # Japán - nap
            'bd': 'sun',                        # Banglades - nap
            'tw': 'sun',                        # Tajvan - nap
            'ph': 'sun and stars',              # Fülöp-szigetek - nap és csillagok
            'my': 'crescent moon and star',     # Malajzia - félhold és csillag
            'sg': 'crescent moon and stars',    # Szingapúr - félhold és csillagok
            'pk': 'crescent moon and star',     # Pakisztán - félhold és csillag
            'tr': 'crescent moon and star',     # Törökország - félhold és csillag
            'az': 'crescent moon and star',     # Azerbajdzsán - félhold és csillag
            'tm': 'crescent moon and stars',    # Türkmenisztán - félhold és csillagok
            'uz': 'crescent moon and stars',    # Üzbegisztán - félhold és csillagok
            'dz': 'crescent moon and star',     # Algéria - félhold és csillag
            'tn': 'crescent moon and star',     # Tunézia - félhold és csillag
            'mr': 'crescent moon and star',     # Mauritánia - félhold és csillag
            'mv': 'crescent moon',              # Maldív-szigetek - félhold
            'cc': 'crescent moon',              # Kókusz-szigetek - félhold
            'la': 'moon phases',                # Laosz - hold fázisai
            'sr': 'star',                       # Suriname - csillag
        }
        
        # Félhold - iszlám országok és mások félhold szimbólummal
        crescent_countries = {
            # Főbb iszlám országok félhold és csillaggal
            'tr': 'red crescent and star',      # Törökország - piros félhold és csillag
            'pk': 'white crescent and star',    # Pakisztán - fehér félhold és csillag zöld mezőn
            'my': 'yellow crescent and star',   # Malajzia - sárga félhold és csillag kék mezőn
            'sg': 'white crescent and stars',   # Szingapúr - fehér félhold és csillagok piros mezőn
            'dz': 'red crescent and star',      # Algéria - piros félhold és csillag fehér mezőn
            'tn': 'red crescent and star',      # Tunézia - piros félhold és csillag fehér mezőn
            'mr': 'yellow crescent and star',   # Mauritánia - sárga félhold és csillag zöld mezőn
            'mv': 'white crescent',             # Maldív-szigetek - fehér félhold piros mezőn
            'cc': 'white crescent',             # Kókusz-szigetek - fehér félhold zöld mezőn
            
            # Közép-ázsiai iszlám országok
            'az': 'white crescent and star',    # Azerbajdzsán - fehér félhold és csillag
            'tm': 'white crescent and stars',   # Türkmenisztán - fehér félhold és csillagok
            'uz': 'white crescent and stars',   # Üzbegisztán - fehér félhold és csillagok
            
            # Arab országok
            'ae': 'crescent references',        # Egyesült Arab Emírségek - félhold utalások
            'qa': 'crescent references',        # Katar - félhold utalások
            'bh': 'crescent references',        # Bahrein - félhold utalások
            'kw': 'crescent references',        # Kuvait - félhold utalások
            'om': 'crescent references',        # Omán - félhold utalások
            'ye': 'crescent references',        # Jemen - félhold utalások
            'sa': 'islamic crescent',           # Szaúd-Arábia - iszlám félhold
            'jo': 'crescent references',        # Jordánia - félhold utalások
            'sy': 'green stars (islam)',       # Szíria - zöld csillagok (iszlám)
            'iq': 'takbir (islamic)',          # Irak - takbir (iszlám)
            'ir': 'islamic symbols',           # Irán - iszlám szimbólumok
            'af': 'islamic symbols',           # Afganisztán - iszlám szimbólumok
            'lb': 'crescent references',        # Libanon - félhold utalások
            'ps': 'crescent references',        # Palesztina - félhold utalások
            
            # Afrikai iszlám országok
            'eg': 'crescent references',        # Egyiptom - félhold utalások
            'ly': 'crescent and star',          # Líbia - félhold és csillag
            'sd': 'crescent references',        # Szudán - félhold utalások
            'so': 'star (islamic)',            # Szomália - csillag (iszlám)
            'dj': 'crescent references',        # Djibouti - félhold utalások
            'er': 'crescent references',        # Eritrea - félhold utalások
            'et': 'crescent references',        # Etiópia - félhold utalások (keresztény többség, de iszlám kisebbség)
            'td': 'crescent references',        # Csád - félhold utalások
            'ne': 'crescent references',        # Niger - félhold utalások
            'ml': 'crescent references',        # Mali - félhold utalások
            'bf': 'crescent references',        # Burkina Faso - félhold utalások
            'sn': 'crescent references',        # Szenegál - félhold utalások
            'gm': 'crescent references',        # Gambia - félhold utalások
            'gn': 'crescent references',        # Guinea - félhold utalások
            'gw': 'crescent references',        # Guinea-Bissau - félhold utalások
            'sl': 'crescent references',        # Sierra Leone - félhold utalások
            'lr': 'crescent references',        # Libéria - félhold utalások
            'ci': 'crescent references',        # Elefántcsontpart - félhold utalások
            'gh': 'crescent references',        # Ghána - félhold utalások
            'tg': 'crescent references',        # Togo - félhold utalások
            'bj': 'crescent references',        # Benin - félhold utalások
            'ng': 'crescent references',        # Nigéria - félhold utalások
            'cm': 'crescent references',        # Kamerun - félhold utalások
            'cf': 'crescent references',        # Közép-afrikai Köztársaság - félhold utalások
            'cg': 'crescent references',        # Kongói Köztársaság - félhold utalások
            'ga': 'crescent references',        # Gabon - félhold utalások
            'gq': 'crescent references',        # Egyenlítői-Guinea - félhold utalások
            'km': 'green and crescent',         # Comore-szigetek - zöld és félhold
            
            # Ázsiai iszlám országok
            'id': 'crescent references',        # Indonézia - félhold utalások
            'bn': 'crescent references',        # Brunei - félhold utalások
            'bd': 'crescent references',        # Banglades - félhold utalások
            'kz': 'crescent references',        # Kazahsztán - félhold utalások
            'kg': 'crescent references',        # Kirgizisztán - félhold utalások
            'tj': 'crescent references',        # Tádzsikisztán - félhold utalások
            'kp': 'crescent references',        # Észak-Korea - félhold utalások (kis iszlám közösség)
            
            # Balkáni iszlám közösségek
            'al': 'crescent references',        # Albánia - félhold utalások (iszlám többség)
            'xk': 'crescent references',        # Koszovó - félhold utalások (iszlám többség)
            'ba': 'crescent references',        # Bosznia - félhold utalások (jelentős iszlám közösség)
            'mk': 'crescent references',        # Macedónia - félhold utalások (iszlám kisebbség)
            'bg': 'crescent references',        # Bulgária - félhold utalások (iszlám kisebbség)
            'rs': 'crescent references',        # Szerbia - félhold utalások (iszlám kisebbség)
            'me': 'crescent references',        # Montenegró - félhold utalások (iszlám kisebbség)
            
            # Egyéb országok iszlám közösségekkel
            'in': 'crescent references',        # India - félhold utalások (nagy iszlám kisebbség)
            'ru': 'crescent references',        # Oroszország - félhold utalások (iszlám köztársaságok)
            'cn': 'crescent references',        # Kína - félhold utalások (ujgurok)
            'th': 'crescent references',        # Thaiföld - félhold utalások (déli iszlám közösség)
            'ph': 'crescent references',        # Fülöp-szigetek - félhold utalások (déli iszlám közösség)
            'mm': 'crescent references',        # Mianmar - félhold utalások (iszlám kisebbség)
            'lk': 'crescent references',        # Srí Lanka - félhold utalások (iszlám kisebbség)
            'np': 'crescent references',        # Nepál - félhold utalások (iszlám kisebbség)
            'bt': 'crescent references',        # Bhután - félhold utalások (iszlám kisebbség)
            
            # Kaukázusi régió
            'ge': 'crescent references',        # Grúzia - félhold utalások (iszlám közösségek)
            'am': 'crescent references',        # Örményország - félhold utalások (kis iszlám közösség)
        }
        
        # Ellenőrizzük az aktuális országot
        if country_code in human_countries:
            symbolic_elements['has_human'] = True
            symbolic_elements['details'].append(f"Human: {human_countries[country_code]}")
        
        if country_code in animal_countries:
            symbolic_elements['has_animal'] = True
            symbolic_elements['details'].append(f"Animal: {animal_countries[country_code]}")
        
        if country_code in plant_countries:
            symbolic_elements['has_plant'] = True
            symbolic_elements['details'].append(f"Plant: {plant_countries[country_code]}")
        
        if country_code in weapon_countries:
            symbolic_elements['has_weapon'] = True
            symbolic_elements['details'].append(f"Weapon: {weapon_countries[country_code]}")
        
        if country_code in building_countries:
            symbolic_elements['has_building'] = True
            symbolic_elements['details'].append(f"Building: {building_countries[country_code]}")
        
        if country_code in celestial_countries:
            symbolic_elements['has_celestial'] = True
            symbolic_elements['details'].append(f"Celestial: {celestial_countries[country_code]}")
        
        if country_code in crescent_countries:
            symbolic_elements['has_crescent'] = True
            symbolic_elements['details'].append(f"Crescent: {crescent_countries[country_code]}")
        
        # Union Jack (brit zászló) - CSAK azok az országok amelyeknek zászlójában VALÓBAN megjelenik
        union_jack_countries = {
            'gb': 'United Kingdom flag',            # Nagy-Britannia - maga az Union Jack
            'au': 'Union Jack in canton',           # Ausztrália - bal felső sarokban
            'nz': 'Union Jack in canton',           # Új-Zéland - bal felső sarokban  
            'fj': 'Union Jack in canton',           # Fiji - bal felső sarokban
            'tv': 'Union Jack in canton',           # Tuvalu - bal felső sarokban
            'ck': 'Union Jack in canton',           # Cook-szigetek - bal felső sarokban
            'nu': 'Union Jack in canton',           # Niue - bal felső sarokban
            'pn': 'Union Jack in canton',           # Pitcairn-szigetek - bal felső sarokban
            'sh': 'Union Jack in canton',           # Szent Ilona - bal felső sarokban
            'tc': 'Union Jack in canton',           # Turks és Caicos - bal felső sarokban
            'vg': 'Union Jack in canton',           # Brit Virgin-szigetek - bal felső sarokban
            'ai': 'Union Jack in canton',           # Anguilla - bal felső sarokban
            'ms': 'Union Jack in canton',           # Montserrat - bal felső sarokban
            'fk': 'Union Jack in canton',           # Falkland-szigetek - bal felső sarokban
            'gs': 'Union Jack in canton',           # Dél-Georgia - bal felső sarokban
            'io': 'Union Jack in canton',           # Brit Indiai-óceáni Terület - bal felső sarokban
            'ky': 'Union Jack in canton',           # Kajmán-szigetek - bal felső sarokban
            'bm': 'Union Jack in canton',           # Bermuda - bal felső sarokban
            'gb-eng': 'St Georges cross',           # Anglia - Szent György kereszt (Union Jack része)
            # ELTÁVOLÍTOTT országok - ezek SAJÁT zászlókkal rendelkeznek, NEM Union Jack-kel:
            # 'gb-sct': Skócia - kék zászló fehér X kereszttel (Saint Andrew's Cross)
            # 'gb-wls': Wales - fehér-zöld zászló piros sárkánnyal  
            # 'je': Jersey - fehér zászló piros kereszttel és címerrel
            # 'gg': Guernsey - fehér zászló piros kereszttel és címerrel
            # 'im': Man-sziget - piros zászló három lábbal (triskelion)
        }
        
        if country_code in union_jack_countries:
            symbolic_elements['has_union_jack'] = True
            symbolic_elements['details'].append(f"Union Jack: {union_jack_countries[country_code]}")
        
        # Keresztek - országok amelyeknek zászlójában kereszt van
        cross_countries = {
            # Skandináv keresztek
            'dk': 'Nordic cross (Dannebrog)',      # Dánia - skandináv kereszt
            'se': 'Nordic cross',                  # Svédország - skandináv kereszt
            'no': 'Nordic cross',                  # Norvégia - skandináv kereszt
            'fi': 'Nordic cross',                  # Finnország - skandináv kereszt
            'is': 'Nordic cross',                  # Izland - skandináv kereszt
            'fo': 'Nordic cross',                  # Feröer-szigetek - skandináv kereszt
            'ax': 'Nordic cross',                  # Åland-szigetek - skandináv kereszt
            'sj': 'Nordic cross',                  # Svalbard - skandináv kereszt
            
            # Nyilvánvaló keresztek (teljes zászló)
            'ch': 'Swiss cross',                   # Svájc - svájci kereszt
            'gr': 'Greek cross',                   # Görögország - görög kereszt
            'to': 'Red cross on white',            # Tonga - piros kereszt fehér mezőn
            'ge': 'Five crosses',                  # Grúzia - öt kereszt
            'mt': 'Maltese cross',                 # Málta - máltai kereszt
            
            # Kettős keresztek
            'sk': 'Double cross',                  # Szlovákia - kettős kereszt
            'hu': 'Double cross',                  # Magyarország - kettős kereszt
            'lt': 'Double cross',                  # Litvánia - kettős kereszt
            
            # Ortodox/keresztény keresztek
            'md': 'Orthodox cross',                # Moldova - ortodox kereszt
            'am': 'Armenian cross',                # Örményország - örmény kereszt
            'do': 'Cross in coat of arms',         # Dominikai Köztársaság - kereszt a címerben
            'et': 'Cross in coat of arms',         # Etiópia - kereszt a címerben
            'er': 'Cross elements',                # Eritrea - kereszt elemek
            
            # Union Jack keresztek (Szent György és Szent András)
            'gb': 'Union Jack crosses',            # Egyesült Királyság - Union Jack keresztek
            'gb-eng': 'St Georges cross',          # Anglia - Szent György kereszt
            'gb-sct': 'St Andrews cross',          # Skócia - Szent András kereszt (X kereszt)
            
            # Koronafüggő területek saját kereszteikkel
            'je': 'Red cross on white',            # Jersey - piros kereszt fehér mezőn
            'gg': 'Red cross on white',            # Guernsey - piros kereszt fehér mezőn
            'au': 'Union Jack and Southern Cross', # Ausztrália - Union Jack + déli kereszt
            'nz': 'Union Jack and Southern Cross', # Új-Zéland - Union Jack + déli kereszt
            'fj': 'Union Jack cross in canton',    # Fiji - Union Jack kereszt
            'tv': 'Union Jack cross in canton',    # Tuvalu - Union Jack kereszt
            
            # Címerbeli keresztek (európai országok)
            'va': 'Papal cross',                   # Vatikán - pápai kereszt
            'sm': 'Cross in coat of arms',         # San Marino - kereszt a címerben
            'ad': 'Cross elements',                # Andorra - kereszt elemek
            'pt': 'Cross of Christ',               # Portugália - Krisztus keresztje
            'es': 'Cross in coat of arms',         # Spanyolország - kereszt a címerben
            'it': 'Cross elements',                # Olaszország - kereszt elemek
            'fr': 'Cross references',              # Franciaország - kereszt utalások
            'be': 'Cross in coat of arms',         # Belgium - kereszt a címerben
            'nl': 'Cross in coat of arms',         # Hollandia - kereszt a címerben
            'de': 'Cross in coat of arms',         # Németország - kereszt a címerben
            'at': 'Cross in coat of arms',         # Ausztria - kereszt a címerben
            'pl': 'Cross elements',                # Lengyelország - kereszt elemek
            'cz': 'Cross in coat of arms',         # Csehország - kereszt a címerben
            'si': 'Cross in coat of arms',         # Szlovénia - kereszt a címerben
            'hr': 'Cross in coat of arms',         # Horvátország - kereszt a címerben
            'ba': 'Cross elements',                # Bosznia - kereszt elemek
            'rs': 'Cross in coat of arms',         # Szerbia - kereszt a címerben
            'me': 'Cross in coat of arms',         # Montenegró - kereszt a címerben
            'al': 'Cross references',              # Albánia - kereszt utalások
            'mk': 'Cross elements',                # Macedónia - kereszt elemek
            'ro': 'Cross in coat of arms',         # Románia - kereszt a címerben
            'by': 'Cross elements',                # Fehéroroszország - kereszt elemek
            'ru': 'Cross elements',                # Oroszország - kereszt elemek
            'ee': 'Cross elements',                # Észtország - kereszt elemek
            'lv': 'Cross elements',                # Lettország - kereszt elemek
            
            # Keresztény országok keresztekkel
            'cy': 'Cross elements',                # Ciprus - kereszt elemek
            'lb': 'Cross references',              # Libanon - kereszt utalások
            'ph': 'Cross references',              # Fülöp-szigetek - kereszt utalások
            'tl': 'Cross elements',                # Kelet-Timor - kereszt elemek
            
            # Déli kereszt (csillagkép)
            'br': 'Southern Cross constellation',  # Brazília - déli kereszt csillagkép
            'ws': 'Southern Cross constellation',  # Szamoa - déli kereszt csillagkép
            'pg': 'Southern Cross constellation',  # Pápua Új-Guinea - déli kereszt csillagkép
            'sb': 'Southern Cross constellation',  # Salamon-szigetek - déli kereszt csillagkép
            'fm': 'Southern Cross constellation',  # Mikronézia - déli kereszt csillagkép
        }
        
        if country_code in cross_countries:
            symbolic_elements['has_cross'] = True
            symbolic_elements['details'].append(f"Cross: {cross_countries[country_code]}")
        
        return symbolic_elements
    
    def analyze_layout(self, image: np.ndarray) -> Dict[str, Any]:
        """Zászló elrendezésének elemzése"""
        height, width = image.shape[:2]
        
        # Aspect ratio
        aspect_ratio = width / height
        
        # Szín eloszlás régiók szerint
        regions = {
            'top_left': image[:height//2, :width//2],
            'top_right': image[:height//2, width//2:],
            'bottom_left': image[height//2:, :width//2],
            'bottom_right': image[height//2:, width//2:],
            'center': image[height//4:3*height//4, width//4:3*width//4]
        }
        
        region_colors = {}
        for region_name, region in regions.items():
            dominant = self.extract_dominant_colors(region, n_colors=3)
            region_colors[region_name] = dominant[0]['name'] if dominant else 'unknown'
        
        return {
            'aspect_ratio': round(aspect_ratio, 2),
            'width': width,
            'height': height,
            'region_colors': region_colors,
            'is_square': abs(aspect_ratio - 1.0) < 0.1,
            'is_horizontal': aspect_ratio > 1.5,
            'is_vertical': aspect_ratio < 0.7
        }
    
    def analyze_flag(self, image_path: str) -> Dict[str, Any]:
        """Teljes zászlóelemzés"""
        try:
            cv_image, rgb_image = self.load_image(image_path)
            
            # Országkód kinyerése a fájlnévből
            country_code = Path(image_path).stem.split('_')[0]
            
            # Alapvető elemzések
            dominant_colors = self.extract_dominant_colors(rgb_image)
            stripes = self.detect_stripes(rgb_image)
            shapes = self.detect_geometric_shapes(rgb_image)
            layout = self.analyze_layout(rgb_image)
            symbolic = self.detect_symbolic_elements(rgb_image, country_code)
            
            # Színkategóriák
            color_names = [color['name'] for color in dominant_colors]
            unique_colors = list(set(color_names))
            
            # Összesített jellemzők
            features = {
                'file_path': image_path,
                'dominant_colors': dominant_colors,
                'unique_colors': unique_colors,
                'color_count': len(unique_colors),
                'stripes': stripes,
                'shapes': shapes,
                'layout': layout,
                'symbolic': symbolic,
                'has_red': 'red' in unique_colors,
                'has_blue': 'blue' in unique_colors,
                'has_green': 'green' in unique_colors,
                'has_yellow': 'yellow' in unique_colors,
                'has_white': 'white' in unique_colors,
                'has_black': 'black' in unique_colors,
                'is_tricolor': len(unique_colors) == 3,
                'is_bicolor': len(unique_colors) == 2,
                'complexity_score': self.calculate_complexity(shapes, stripes, len(unique_colors), symbolic)
            }
            
            # Félhold felismerés javítása
            features = self.fix_crescent_detection(features)
            
            return features
            
        except Exception as e:
            print(f"Hiba a zászló elemzésekor ({image_path}): {e}")
            return {}
    
    def calculate_complexity(self, shapes: Dict, stripes: Dict, color_count: int, symbolic: Dict = None) -> float:
        """Zászló komplexitási pontszámának kiszámítása"""
        score = 0
        
        # Színek száma
        score += color_count * 0.5
        
        # Formák száma
        score += shapes.get('total_shapes', 0) * 2
        
        # Csíkok
        if stripes.get('has_horizontal_stripes', False):
            score += 1
        if stripes.get('has_vertical_stripes', False):
            score += 1
        
        # Speciális formák
        score += shapes.get('stars', 0) * 3
        score += shapes.get('crosses', 0) * 2
        score += shapes.get('circles', 0) * 1.5
        
        # Szimbolikus elemek bónusz pontjai
        if symbolic:
            if symbolic.get('has_animal', False):
                score += 4  # Állatok komplexek
            if symbolic.get('has_human', False):
                score += 5  # Emberi alakok nagyon komplexek
            if symbolic.get('has_plant', False):
                score += 2  # Növények közepesen komplexek
            if symbolic.get('has_weapon', False):
                score += 3  # Fegyverek komplexek
            if symbolic.get('has_building', False):
                score += 4  # Épületek komplexek
            if symbolic.get('has_celestial', False):
                score += 1  # Égi testek egyszerűbbek
            if symbolic.get('has_union_jack', False):
                score += 3  # Union Jack komplex (keresztek és átlók)
            if symbolic.get('has_cross', False):
                score += 2  # Keresztek közepesen komplexek
        
        return round(score, 2)
    
    def analyze_all_flags(self) -> Dict[str, Dict]:
        """Összes letöltött zászló elemzése"""
        if not self.flags_dir.exists():
            print("Nincsenek letöltött zászlók!")
            return {}
        
        flag_features = {}
        flag_files = list(self.flags_dir.glob("*.png"))
        
        print(f"Zászlók elemzése kezdődik... ({len(flag_files)} fájl)")
        
        for i, flag_file in enumerate(flag_files, 1):
            print(f"Elemzés: {flag_file.name} ({i}/{len(flag_files)})")
            
            # Országkód kinyerése a fájlnévből
            country_code = flag_file.stem.split('_')[0]
            
            # Elemzés
            features = self.analyze_flag(str(flag_file))
            if features:
                flag_features[country_code] = features
        
        # Eredmények mentése (numpy típusok konvertálása)
        def convert_numpy(obj):
            if isinstance(obj, (np.integer, np.int64, np.int32)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float64, np.float32)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, tuple):
                return tuple(convert_numpy(item) for item in obj)
            return obj
        
        # Rekurzív konvertálás
        def clean_for_json(data):
            if isinstance(data, dict):
                return {key: clean_for_json(value) for key, value in data.items()}
            elif isinstance(data, (list, tuple)):
                return [clean_for_json(item) for item in data]
            else:
                return convert_numpy(data)
        
        cleaned_features = clean_for_json(flag_features)
        
        with open(self.features_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_features, f, ensure_ascii=False, indent=2)
        
        print(f"\nElemzés befejezve! {len(flag_features)} zászló elemezve.")
        print(f"Eredmények mentve: {self.features_file}")
        
        return flag_features
    
    def load_features(self) -> Dict[str, Dict]:
        """Mentett jellemzők betöltése"""
        if self.features_file.exists():
            with open(self.features_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def get_flags_by_color(self, color_name: str) -> List[str]:
        """Adott színt tartalmazó zászlók keresése"""
        features = self.load_features()
        matching_flags = []
        
        for country_code, flag_data in features.items():
            if color_name.lower() in [c.lower() for c in flag_data.get('unique_colors', [])]:
                matching_flags.append(country_code)
        
        return matching_flags
    
    def get_flags_by_pattern(self, pattern: str) -> List[str]:
        """Adott mintázatú zászlók keresése"""
        features = self.load_features()
        matching_flags = []
        
        for country_code, flag_data in features.items():
            stripes = flag_data.get('stripes', {})
            shapes = flag_data.get('shapes', {})
            
            if pattern.lower() == 'stripes':
                if stripes.get('has_horizontal_stripes') or stripes.get('has_vertical_stripes'):
                    matching_flags.append(country_code)
            elif pattern.lower() == 'bands':
                if stripes.get('has_horizontal_bands') or stripes.get('has_vertical_bands'):
                    matching_flags.append(country_code)
            elif pattern.lower() == 'stars':
                if shapes.get('stars', 0) > 0:
                    matching_flags.append(country_code)
            elif pattern.lower() == 'cross':
                if shapes.get('crosses', 0) > 0:
                    matching_flags.append(country_code)
            elif pattern.lower() == 'circle':
                if shapes.get('circles', 0) > 0:
                    matching_flags.append(country_code)
        
        return matching_flags
    
    def extract_country_code_from_path(self, file_path: str) -> str:
        """Országkód kinyerése a fájl útvonalából"""
        return Path(file_path).stem.split('_')[0]
    
    def fix_crescent_detection(self, features: Dict) -> Dict:
        """Félhold felismerés javítása tudásbázis alapján"""
        
        # Precíz félhold országok adatbázisa (CSAK valóban félholdas zászlók!)
        crescent_countries = {
            # Valódi félhold és csillag kombinációk (látható a zászlón)
            'tr': 'White crescent and star on red',        # Törökország - fehér félhold és csillag piros mezőn
            'pk': 'White crescent and star on green',      # Pakisztán - fehér félhold és csillag zöld mezőn
            'my': 'Yellow crescent and star on blue',      # Malajzia - sárga félhold és csillag kék mezőn
            'sg': 'White crescent and stars on red',       # Szingapúr - fehér félhold és csillagok piros mezőn
            'dz': 'Red crescent and star on white',        # Algéria - piros félhold és csillag fehér mezőn
            'tn': 'Red crescent and star on white',        # Tunézia - piros félhold és csillag fehér mezőn
            'mr': 'Yellow crescent and star',              # Mauritánia - sárga félhold és csillag
            'mv': 'White crescent on green',               # Maldív-szigetek - fehér félhold zöld mezőn
            'ly': 'White crescent and star',               # Líbia - fehér félhold és csillag
            'km': 'White crescent and stars',              # Comore-szigetek - fehér félhold és csillagok
            
            # Közép-ázsiai országok valódi félholddal
            'az': 'White crescent and star on blue',       # Azerbajdzsán - fehér félhold és csillag kék mezőn
            'tm': 'White crescent and stars',              # Türkmenisztán - fehér félhold és csillagok
            'uz': 'White crescent and stars',              # Üzbegisztán - fehér félhold és csillagok
            
            # Délkelet-ázsiai iszlám országok
            'bn': 'Yellow crescent on black and white'     # Brunei - sárga félhold fekete-fehér mezőn
        }
        
        country_code = self.extract_country_code_from_path(features.get('file_path', ''))
        
        if country_code in crescent_countries:
            # Csak a tudásbázisban szereplő országok kapnak félhold jelölést
            features['symbolic']['has_crescent'] = True
            features['symbolic']['details'].append(f"Crescent: {crescent_countries[country_code]}")
        else:
            # Minden más ország esetén töröljük a félhold jelölést
            features['symbolic']['has_crescent'] = False
            # Távolítsuk el a crescent references bejegyzéseket
            features['symbolic']['details'] = [
                detail for detail in features['symbolic']['details'] 
                if not detail.startswith('Crescent:')
            ]
        
        return features


def main():
    """Főprogram - tesztelés"""
    analyzer = FlagAnalyzer()
    
    # Összes zászló elemzése
    features = analyzer.analyze_all_flags()
    
    # Példa keresések
    red_flags = analyzer.get_flags_by_color('red')
    print(f"Piros zászlók: {len(red_flags)} db")
    
    star_flags = analyzer.get_flags_by_pattern('stars')
    print(f"Csillagos zászlók: {len(star_flags)} db")


if __name__ == "__main__":
    main() 