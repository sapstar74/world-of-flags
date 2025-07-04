"""
Keresési és szűrési modul - Természetes nyelvi kérések feldolgozása
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from collections import defaultdict


class FlagSearchEngine:
    """Zászlókereső motor természetes nyelvi kérések feldolgozásához"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.features_file = self.data_dir / "flag_features.json"
        self.countries_file = self.data_dir / "countries.json"
        
        # Egyszerű stop szavak listája
        self.stop_words = {'a', 'an', 'and', 'or', 'the', 'is', 'are', 'with', 'of', 'in', 'on', 'at', 'to', 'for', 'by', 'mind', 'minden', 'all', 'every', 'az', 'el', 'le'}
        
        # Színek fordítása
        self.color_translations = {
            'piros': 'red', 'vörös': 'red', 'red': 'red',
            'kék': 'blue', 'blue': 'blue',
            'világos kék': 'lightblue', 'világoskék': 'lightblue', 'light blue': 'lightblue', 'lightblue': 'lightblue',
            'sötét kék': 'darkblue', 'sötétkék': 'darkblue', 'dark blue': 'darkblue', 'darkblue': 'darkblue',
            'égkék': 'lightblue', 'égszínkék': 'lightblue', 'sky blue': 'lightblue',
            'tengerkék': 'darkblue', 'navy': 'darkblue', 'navy blue': 'darkblue',
            'zöld': 'green', 'green': 'green',
            'világos zöld': 'lightgreen', 'világoszöld': 'lightgreen', 'light green': 'lightgreen', 'lightgreen': 'lightgreen',
            'sötét zöld': 'darkgreen', 'sötétzöld': 'darkgreen', 'dark green': 'darkgreen', 'darkgreen': 'darkgreen',
            'sárga': 'yellow', 'yellow': 'yellow',
            'fehér': 'white', 'white': 'white',
            'fekete': 'black', 'black': 'black',
            'narancs': 'orange', 'orange': 'orange',
            'lila': 'purple', 'purple': 'purple',
            'rózsaszín': 'pink', 'pink': 'pink',
            'barna': 'brown', 'brown': 'brown'
        }
        
        # Mintázatok fordítása
        self.pattern_translations = {
            'csíkos': 'stripes', 'csík': 'stripes', 'stripes': 'stripes',
        'sávos': 'bands', 'sáv': 'bands', 'bands': 'bands',
            'csillag': 'stars', 'csillagos': 'stars', 'stars': 'stars', 'star': 'stars',
            'kereszt': 'cross', 'cross': 'cross',
            'kör': 'circle', 'circles': 'circle', 'circle': 'circle'
        }
        
        # Szimbolikus elemek fordítása (pontos szóhatárokkal)
        self.symbolic_translations = {
            'állatos': 'animal', 'állat': 'animal', 'animal': 'animal', 'madár': 'animal', 'bird': 'animal',
            'sasos': 'animal', 'sas': 'animal', 'eagle': 'animal', 'oroszlán': 'animal', 'lion': 'animal',
            'ló': 'animal', 'horse': 'animal', 'kutya': 'animal', 'dog': 'animal',
            'macska': 'animal', 'cat': 'animal', 'medve': 'animal', 'bear': 'animal',
            'növényes': 'plant', 'növény': 'plant', 'plant': 'plant', 'fa': 'plant', 'tree': 'plant',
            'levél': 'plant', 'leaf': 'plant', 'virág': 'plant', 'flower': 'plant',
            'juharleveles': 'plant', 'juhar': 'plant', 'maple': 'plant', 'pálma': 'plant', 'palm': 'plant',
            'fegyveres': 'weapon', 'fegyver': 'weapon', 'weapon': 'weapon', 'kardos': 'weapon', 'kard': 'weapon', 'sword': 'weapon',
            'lándzsa': 'weapon', 'spear': 'weapon', 'puska': 'weapon', 'rifle': 'weapon',
            'ágyú': 'weapon', 'cannon': 'weapon', 'nyíl': 'weapon', 'arrow': 'weapon',
            'emberi': 'human', 'ember': 'human', 'human': 'human', 'alak': 'human',
            'épület': 'building', 'building': 'building', 'torony': 'building', 'tower': 'building',
            'templom': 'building', 'church': 'building', 'mecset': 'building', 'mosque': 'building',
            'napos': 'celestial', 'nap': 'celestial', 'sun': 'celestial', 'hold': 'celestial', 'moon': 'celestial',
            'égi': 'celestial', 'celestial': 'celestial',
            'union jack': 'union_jack', 'brit': 'union_jack', 'british': 'union_jack', 'angol': 'union_jack',
            'kereszt': 'cross', 'cross': 'cross', 'keresztes': 'cross', 'skandináv': 'cross',
            'félhold': 'crescent', 'crescent': 'crescent', 'félholdas': 'crescent', 'iszlám': 'crescent', 'islamic': 'crescent'
        }
        
        # Speciális csillag keresések
        self.star_modifiers = {
            'egy': 1, 'egyetlen': 1, 'single': 1, 'one': 1,
            'kettő': 2, 'két': 2, 'two': 2,
            'három': 3, 'three': 3,
            'négy': 4, 'four': 4,
            'öt': 5, 'five': 5,
            'sok': 'many', 'több': 'many', 'many': 'many', 'multiple': 'many',
            'nagy': 'large', 'kis': 'small', 'kicsi': 'small', 'large': 'large', 'small': 'small'
        }
        
        # Kontinensek fordítása
        self.continent_translations = {
            'európa': 'europe', 'europe': 'europe',
            'ázsia': 'asia', 'asia': 'asia',
            'afrika': 'africa', 'africa': 'africa',
            'amerika': 'america', 'america': 'america',
            'észak-amerika': 'north america', 'north america': 'north america',
            'közép-amerika': 'central america', 'central america': 'central america',
            'dél-amerika': 'south america', 'south america': 'south america',
            'óceánia': 'oceania', 'oceania': 'oceania',
            'szigetek': 'islands', 'szigetes': 'islands', 'islands': 'islands', 'island': 'islands'
        }
        
        # Kontinens-ország mapping (frissített Amerika felosztással)
        self.continent_countries = {
            'europe': ['de', 'fr', 'it', 'es', 'gb', 'pl', 'nl', 'be', 'ch', 'at', 'se', 'no', 'dk', 'fi', 'ie', 'pt', 'gr', 'cz', 'hu', 'ro', 'bg', 'hr', 'sk', 'si', 'al', 'rs', 'me', 'mk', 'ba', 'xk', 'li', 'ad', 'sm', 'va', 'mt', 'cy', 'is', 'lu', 'mc', 'ee', 'lv', 'lt', 'by', 'ua', 'md'],
            'asia': ['cn', 'jp', 'in', 'kr', 'th', 'id', 'my', 'sg', 'ph', 'vn', 'tw', 'hk', 'mn', 'kz', 'uz', 'af', 'pk', 'bd', 'lk', 'mm', 'la', 'kh', 'bt', 'np', 'mv', 'kg', 'tj', 'tm', 'ir', 'iq', 'sy', 'jo', 'il', 'ps', 'lb', 'tr', 'am', 'az', 'ge', 'ru', 'kp', 'ae', 'sa', 'ye', 'om', 'qa', 'bh', 'kw'],
            'north america': ['us', 'ca', 'mx'],  # Csak USA, Kanada, Mexikó
            'central america': ['gt', 'bz', 'sv', 'hn', 'ni', 'cr', 'pa', 'cu', 'jm', 'ht', 'do', 'bs', 'bb', 'ag', 'kn', 'lc', 'vc', 'gd', 'tt', 'dm', 'ai', 'aw', 'bq', 'cw', 'sx', 'bl', 'gp', 'mf', 'mq', 'pr', 'vi', 'vg', 'ky', 'tc', 'bm', 'ms', 'pm'],  # Közép-Amerika + Karib-térség
            'south america': ['br', 'ar', 'cl', 'pe', 'co', 've', 'ec', 'bo', 'py', 'uy', 'sr', 'gy', 'gf'],  # Dél-Amerika
            'africa': ['za', 'eg', 'ng', 'ke', 'ma', 'et', 'gh', 'ug', 'dz', 'tn', 'ly', 'sd', 'mw', 'zm', 'zw', 'bw', 'na', 'sz', 'ls', 'mz', 'mg', 'mu', 'sc', 'km', 'ao', 'cm', 'cf', 'td', 'ne', 'ml', 'bf', 'ci', 'lr', 'sl', 'gn', 'gw', 'sn', 'gm', 'cv', 'mr', 'so', 'dj', 'er', 'ss', 'bi', 'rw', 'tz', 'ga', 'gq', 'cg', 'cd', 'st', 'tg', 'bj'],
            'oceania': ['au', 'nz', 'fj', 'pg', 'sb', 'vu', 'nc', 'pf', 'ws', 'to', 'tv', 'nr', 'ki', 'mh', 'fm', 'pw', 'ck', 'nu', 'as', 'gu', 'mp', 'um'],
            'america': [],  # Egyesített Amerika (észak + közép + dél)
            'islands': [
                # Óceániai szigetek (kisebb szigetek)
                'fj', 'pg', 'sb', 'vu', 'ws', 'to', 'tv', 'nr', 'ki', 'mh', 'fm', 'pw', 'ck', 'nu', 'as', 'gu', 'mp', 'um',
                # Atlanti-óceáni szigetek
                'is', 'gb', 'ie', 'im', 'je', 'gg', 'fo', 'ax', 'gl', 'bv', 'sh', 'ac', 'ta', 'fk', 'gs', 'io',
                # Mediterrán szigetek
                'mt', 'cy',
                # Ázsiai szigetek
                'jp', 'ph', 'id', 'sg', 'tw', 'hk', 'mo', 'lk', 'mv', 'bn', 'tl', 'cc', 'cx',
                # Indiai-óceáni szigetek  
                'mu', 'sc', 'km', 'mg', 're', 'yt', 'tf', 'hm',
                # Karib-térségi szigetek
                'cu', 'jm', 'ht', 'do', 'bs', 'bb', 'ag', 'kn', 'lc', 'vc', 'gd', 'tt', 'dm', 
                'ai', 'aw', 'bq', 'cw', 'sx', 'bl', 'gp', 'mf', 'mq', 'pr', 'vi', 'vg', 'ky', 'tc', 'bm', 'ms',
                # Egyéb szigetek
                'cv',  # Zöld-foki Köztársaság
                'st',  # São Tomé és Príncipe
                'nf',  # Norfolk-sziget
                'pf',  # Francia Polinézia  
                'nc',  # Új-Kaledónia
                'wf',  # Wallis és Futuna
                'pm',  # Saint Pierre és Miquelon
                'tk',  # Tokelau
                'pn',  # Pitcairn-szigetek
            ]
        }
        
        # Amerika egyesítése (mind a három régió)
        self.continent_countries['america'] = (
            self.continent_countries['north america'] + 
            self.continent_countries['central america'] +
            self.continent_countries['south america']
        )
        
        # Magyar országnevek fordítása
        self.country_name_translations = {
            # Gyakori országok magyar nevei
            'magyarország': 'hu', 'hungary': 'hu',
            'németország': 'de', 'germany': 'de',
            'franciaország': 'fr', 'france': 'fr',
            'olaszország': 'it', 'italy': 'it',
            'spanyolország': 'es', 'spain': 'es',
            'egyesült királyság': 'gb', 'united kingdom': 'gb', 'anglia': 'gb', 'england': 'gb',
            'lengyelország': 'pl', 'poland': 'pl',
            'hollandia': 'nl', 'netherlands': 'nl',
            'belgium': 'be', 'belgium': 'be',
            'svájc': 'ch', 'switzerland': 'ch',
            'ausztria': 'at', 'austria': 'at',
            'svédország': 'se', 'sweden': 'se',
            'norvégia': 'no', 'norway': 'no',
            'dánia': 'dk', 'denmark': 'dk',
            'finnország': 'fi', 'finland': 'fi',
            'írország': 'ie', 'ireland': 'ie',
            'portugália': 'pt', 'portugal': 'pt',
            'görögország': 'gr', 'greece': 'gr',
            'csehország': 'cz', 'czechia': 'cz', 'czech republic': 'cz',
            'románia': 'ro', 'romania': 'ro',
            'bulgária': 'bg', 'bulgaria': 'bg',
            'horvátország': 'hr', 'croatia': 'hr',
            'szlovákia': 'sk', 'slovakia': 'sk',
            'szlovénia': 'si', 'slovenia': 'si',
            
            # Brit területek (Egyesült Királyság részei és koronafüggő területek)
            'skócia': 'gb-sct', 'scotland': 'gb-sct',
            'wales': 'gb-wls', 'wales': 'gb-wls',
            'észak-írország': 'gb-nir', 'northern ireland': 'gb-nir',
            'jersey': 'je', 'jersey': 'je',
            'guernsey': 'gg', 'guernsey': 'gg',
            'man-sziget': 'im', 'isle of man': 'im',
            
            # Ázsia
            'kína': 'cn', 'china': 'cn',
            'japán': 'jp', 'japan': 'jp',
            'india': 'in', 'india': 'in',
            'dél-korea': 'kr', 'south korea': 'kr',
            'észak-korea': 'kp', 'north korea': 'kp',
            'thaiföld': 'th', 'thailand': 'th',
            'indonézia': 'id', 'indonesia': 'id',
            'malajzia': 'my', 'malaysia': 'my',
            'szingapúr': 'sg', 'singapore': 'sg',
            'fülöp-szigetek': 'ph', 'philippines': 'ph',
            'vietnám': 'vn', 'vietnam': 'vn',
            'tajvan': 'tw', 'taiwan': 'tw',
            'hongkong': 'hk', 'hong kong': 'hk',
            'mongólia': 'mn', 'mongolia': 'mn',
            'kazahsztán': 'kz', 'kazakhstan': 'kz',
            'üzbegisztán': 'uz', 'uzbekistan': 'uz',
            'afganisztán': 'af', 'afghanistan': 'af',
            'pakisztán': 'pk', 'pakistan': 'pk',
            'banglades': 'bd', 'bangladesh': 'bd',
            'irán': 'ir', 'iran': 'ir',
            'irak': 'iq', 'iraq': 'iq',
            'izrael': 'il', 'israel': 'il',
            'törökország': 'tr', 'turkey': 'tr',
            'szaúd-arábia': 'sa', 'saudi arabia': 'sa',
            
            # Hiányzó ázsiai országok
            'bhután': 'bt', 'bhutan': 'bt',
            'nepál': 'np', 'nepal': 'np',
            'srí lanka': 'lk', 'sri lanka': 'lk',
            'mianmar': 'mm', 'myanmar': 'mm', 'burma': 'mm',
            'laosz': 'la', 'laos': 'la',
            'kambodzsa': 'kh', 'cambodia': 'kh',
            'maldív-szigetek': 'mv', 'maldives': 'mv',
            'brunei': 'bn', 'brunei': 'bn',
            'kelet-timor': 'tl', 'timor-leste': 'tl', 'east timor': 'tl',
            'kirgizisztán': 'kg', 'kyrgyzstan': 'kg',
            'tádzsikisztán': 'tj', 'tajikistan': 'tj',
            'türkmenisztán': 'tm', 'turkmenistan': 'tm',
            'azerbajdzsán': 'az', 'azerbaijan': 'az',
            'grúzia': 'ge', 'georgia': 'ge',
            'örményország': 'am', 'armenia': 'am',
            'libanon': 'lb', 'lebanon': 'lb',
            'szíria': 'sy', 'syria': 'sy',
            'jordánia': 'jo', 'jordan': 'jo',
            'palesztina': 'ps', 'palestine': 'ps',
            'jemen': 'ye', 'yemen': 'ye',
            'omán': 'om', 'oman': 'om',
            'katar': 'qa', 'qatar': 'qa',
            'bahrein': 'bh', 'bahrain': 'bh',
            'kuvait': 'kw', 'kuwait': 'kw',
            'egyesült arab emirátusok': 'ae', 'united arab emirates': 'ae', 'uae': 'ae',
            
            # Amerika
            'egyesült államok': 'us', 'united states': 'us', 'usa': 'us',
            'kanada': 'ca', 'canada': 'ca',
            'mexikó': 'mx', 'mexico': 'mx',
            'brazília': 'br', 'brazil': 'br',
            'argentína': 'ar', 'argentina': 'ar',
            'chile': 'cl', 'chile': 'cl',
            'peru': 'pe', 'peru': 'pe',
            'kolumbia': 'co', 'colombia': 'co',
            'venezuela': 've', 'venezuela': 've',
            'ecuador': 'ec', 'ecuador': 'ec',
            'bolívia': 'bo', 'bolivia': 'bo',
            'paraguay': 'py', 'paraguay': 'py',
            'uruguay': 'uy', 'uruguay': 'uy',
            'kuba': 'cu', 'cuba': 'cu',
            'jamaica': 'jm', 'jamaica': 'jm',
            
            # Hiányzó amerikai országok
            'guatemala': 'gt', 'guatemala': 'gt',
            'belize': 'bz', 'belize': 'bz',
            'salvador': 'sv', 'el salvador': 'sv',
            'honduras': 'hn', 'honduras': 'hn',
            'nicaragua': 'ni', 'nicaragua': 'ni',
            'costa rica': 'cr', 'costa rica': 'cr',
            'panama': 'pa', 'panama': 'pa',
            'haiti': 'ht', 'haiti': 'ht',
            'dominikai köztársaság': 'do', 'dominican republic': 'do',
            'bahama-szigetek': 'bs', 'bahamas': 'bs',
            'barbados': 'bb', 'barbados': 'bb',
            'trinidad és tobago': 'tt', 'trinidad and tobago': 'tt',
            'saint kitts és nevis': 'kn', 'saint kitts and nevis': 'kn',
            'suriname': 'sr', 'suriname': 'sr',
            'guyana': 'gy', 'guyana': 'gy',
            'francia guyana': 'gf', 'french guiana': 'gf',
            
            # Afrika
            'dél-afrika': 'za', 'south africa': 'za',
            'egyiptom': 'eg', 'egypt': 'eg',
            'nigéria': 'ng', 'nigeria': 'ng',
            'kenya': 'ke', 'kenya': 'ke',
            'marokkó': 'ma', 'morocco': 'ma',
            'etiópia': 'et', 'ethiopia': 'et',
            'ghána': 'gh', 'ghana': 'gh',
            'uganda': 'ug', 'uganda': 'ug',
            'algéria': 'dz', 'algeria': 'dz',
            'tunézia': 'tn', 'tunisia': 'tn',
            'líbia': 'ly', 'libya': 'ly',
            'szudán': 'sd', 'sudan': 'sd',
            
            # Hiányzó afrikai országok
            'tanzánia': 'tz', 'tanzania': 'tz',
            'zambia': 'zm', 'zambia': 'zm',
            'zimbabwe': 'zw', 'zimbabwe': 'zw',
            'botswana': 'bw', 'botswana': 'bw',
            'namíbia': 'na', 'namibia': 'na',
            'angola': 'ao', 'angola': 'ao',
            'mozambik': 'mz', 'mozambique': 'mz',
            'madagaszkár': 'mg', 'madagascar': 'mg',
            'mauritius': 'mu', 'mauritius': 'mu',
            'seychelle-szigetek': 'sc', 'seychelles': 'sc',
            'comore-szigetek': 'km', 'comoros': 'km',
            'kamerun': 'cm', 'cameroon': 'cm',
            'közép-afrikai köztársaság': 'cf', 'central african republic': 'cf',
            'csád': 'td', 'chad': 'td',
            'niger': 'ne', 'niger': 'ne',
            'mali': 'ml', 'mali': 'ml',
            'burkina faso': 'bf', 'burkina faso': 'bf',
            'elefántcsontpart': 'ci', 'ivory coast': 'ci', 'côte d\'ivoire': 'ci',
            'libéria': 'lr', 'liberia': 'lr',
            'sierra leone': 'sl', 'sierra leone': 'sl',
            'guinea': 'gn', 'guinea': 'gn',
            'guinea-bissau': 'gw', 'guinea-bissau': 'gw',
            'szenegál': 'sn', 'senegal': 'sn',
            'gambia': 'gm', 'gambia': 'gm',
            'zöld-foki köztársaság': 'cv', 'cape verde': 'cv',
            'mauritánia': 'mr', 'mauritania': 'mr',
            'szomália': 'so', 'somalia': 'so',
            'djibouti': 'dj', 'djibouti': 'dj',
            'eritrea': 'er', 'eritrea': 'er',
            'dél-szudán': 'ss', 'dél szudán': 'ss', 'délszudán': 'ss', 'south sudan': 'ss',
            'ruanda': 'rw', 'rwanda': 'rw',
            'burundi': 'bi', 'burundi': 'bi',
            'malawi': 'mw', 'malawi': 'mw',
            'lesotho': 'ls', 'lesotho': 'ls',
            'szváziföld': 'sz', 'eswatini': 'sz', 'swaziland': 'sz',
            'gabon': 'ga', 'gabon': 'ga',
            'egyenlítői-guinea': 'gq', 'equatorial guinea': 'gq',
            'kongói köztársaság': 'cg', 'republic of the congo': 'cg',
            'kongói demokratikus köztársaság': 'cd', 'democratic republic of the congo': 'cd',
            'são tomé és príncipe': 'st', 'sao tome and principe': 'st',
            'togo': 'tg', 'togo': 'tg',
            'benin': 'bj', 'benin': 'bj',
            
            # Óceánia
            'ausztrália': 'au', 'australia': 'au',
            'új-zéland': 'nz', 'new zealand': 'nz',
            'fiji': 'fj', 'fiji': 'fj',
            
            # Hiányzó óceániai országok
            'pápua új-guinea': 'pg', 'papua new guinea': 'pg',
            'salamon-szigetek': 'sb', 'solomon islands': 'sb',
            'vanuatu': 'vu', 'vanuatu': 'vu',
            'szamoa': 'ws', 'samoa': 'ws',
            'tonga': 'to', 'tonga': 'to',
            'tuvalu': 'tv', 'tuvalu': 'tv',
            'nauru': 'nr', 'nauru': 'nr',
            'kiribati': 'ki', 'kiribati': 'ki',
            'marshall-szigetek': 'mh', 'marshall islands': 'mh',
            'mikronézia': 'fm', 'micronesia': 'fm',
            'palau': 'pw', 'palau': 'pw',
            
            # Egyéb gyakori országok
            'oroszország': 'ru', 'russia': 'ru',
            'ukrajna': 'ua', 'ukraine': 'ua',
            'fehéroroszország': 'by', 'belarus': 'by',
            'szerbia': 'rs', 'serbia': 'rs',
            'montenegró': 'me', 'montenegro': 'me',
            'bosznia-hercegovina': 'ba', 'bosnia and herzegovina': 'ba',
            'albánia': 'al', 'albania': 'al',
            'macedónia': 'mk', 'north macedonia': 'mk',
            'moldova': 'md', 'moldova': 'md',
            'észtország': 'ee', 'estonia': 'ee',
            'lettország': 'lv', 'latvia': 'lv',
            'litvánia': 'lt', 'lithuania': 'lt',
            'izland': 'is', 'iceland': 'is',
            'málta': 'mt', 'malta': 'mt',
            'ciprus': 'cy', 'cyprus': 'cy',
            'luxemburg': 'lu', 'luxembourg': 'lu',
            'monaco': 'mc', 'monaco': 'mc',
            'liechtenstein': 'li', 'liechtenstein': 'li',
            'andorra': 'ad', 'andorra': 'ad',
            'san marino': 'sm', 'san marino': 'sm',
            'vatikán': 'va', 'vatican': 'va',
            'koszovó': 'xk', 'kosovo': 'xk',
        }
        
        # Betöltjük az adatokat
        self.flag_features = self.load_flag_features()
        self.countries = self.load_countries()
    
    def load_flag_features(self) -> Dict[str, Dict]:
        """Zászló jellemzők betöltése"""
        if self.features_file.exists():
            with open(self.features_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def load_countries(self) -> Dict[str, str]:
        """Országok adatainak betöltése"""
        if self.countries_file.exists():
            with open(self.countries_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def preprocess_query(self, query: str) -> List[str]:
        """Kérés előfeldolgozása egyszerű módszerekkel"""
        # Kisbetűsítés és egyszerű tokenizálás
        query = query.lower()
        
        # Egyszerű tokenizálás szóközök és írásjelek alapján
        tokens = re.findall(r'\b\w+\b', query)
        
        # Stop szavak eltávolítása
        tokens = [token for token in tokens if token not in self.stop_words and len(token) > 1]
        
        return tokens
    
    def extract_colors(self, query: str) -> List[str]:
        """Színek kinyerése a kérésből"""
        colors = []
        query_lower = query.lower()
        
        for color_hu, color_en in self.color_translations.items():
            if color_hu in query_lower:
                colors.append(color_en)
        
        return list(set(colors))
    
    def extract_patterns(self, query: str) -> List[str]:
        """Mintázatok kinyerése a kérésből"""
        patterns = []
        query_lower = query.lower()
        
        for pattern_hu, pattern_en in self.pattern_translations.items():
            if pattern_hu in query_lower:
                # Kizárjuk a 'cross' mintázatot, mert azt a szimbolikus keresés kezeli
                if pattern_en != 'cross':
                    patterns.append(pattern_en)
        
        return list(set(patterns))
    
    def extract_continents(self, query: str) -> List[str]:
        """Kontinensek kinyerése a kérésből"""
        continents = []
        query_lower = query.lower()
        
        # Prioritás sorrendben ellenőrizzük a kontinenseket
        # Specifikusabb kontinensek először (észak-amerika, közép-amerika, dél-amerika)
        priority_order = [
            ('észak-amerika', 'north america'),
            ('north america', 'north america'),
            ('közép-amerika', 'central america'),
            ('central america', 'central america'),
            ('dél-amerika', 'south america'),
            ('south america', 'south america'),
            ('európa', 'europe'),
            ('europe', 'europe'),
            ('ázsia', 'asia'),
            ('asia', 'asia'),
            ('afrika', 'africa'),
            ('africa', 'africa'),
            ('óceánia', 'oceania'),
            ('oceania', 'oceania'),
            ('szigetek', 'islands'),
            ('szigetes', 'islands'),
            ('sziget', 'islands'),  # HOZZÁADVA: egyes szám
            ('islands', 'islands'),
            ('island', 'islands'),
            ('amerika', 'america'),  # Csak akkor, ha nincs specifikusabb találat
            ('america', 'america'),
        ]
        
        found_specific_america = False
        
        for continent_hu, continent_en in priority_order:
            if continent_hu in query_lower:
                # Ha specifikus Amerika régiót találtunk, ne adjuk hozzá az általános "amerika"-t
                if continent_en in ['north america', 'central america', 'south america']:
                    found_specific_america = True
                    continents.append(continent_en)
                elif continent_en == 'america' and not found_specific_america:
                    # Csak akkor adjuk hozzá az általános "amerika"-t, ha nincs specifikus régió
                    continents.append(continent_en)
                elif continent_en != 'america':
                    # Minden más kontinens
                    continents.append(continent_en)
        
        return list(set(continents))
    
    def extract_countries(self, query: str) -> List[str]:
        """Országnevek kinyerése a kérésből"""
        countries = []
        query_lower = query.lower()
        original_query = query_lower
        
        # 1. Keresés a magyar/angol fordítási szótárban (prioritás hossz szerint rendezve)
        # Hosszabb nevek előbb, hogy elkerüljük a "szudán" vs "dél-szudán" problémát
        sorted_countries = sorted(self.country_name_translations.items(), 
                                 key=lambda x: len(x[0]), reverse=True)
        
        for country_name, country_code in sorted_countries:
            if country_name in query_lower:
                countries.append(country_code)
                # Ha megtaláltunk egy hosszabb nevet, ne keressük a rövidebbet
                # (pl. ha "dél-szudán" megvan, ne keressük a "szudán"-t)
                query_lower = query_lower.replace(country_name, "")
        
        # 2. Keresés az eredeti angol országnevek között (szintén hossz szerint)
        sorted_english_countries = sorted(self.countries.items(), 
                                         key=lambda x: len(x[1]), reverse=True)
        
        for code, name in sorted_english_countries:
            if name.lower() in query_lower and code not in countries:
                countries.append(code)
                query_lower = query_lower.replace(name.lower(), "")
        
        # 3. Speciális eset: ha csak "szudán" vagy "sudan" szerepel a kérésben 
        # (de nincs "dél-" vagy "south" előtte), akkor mindkét szudáni országot adjuk vissza
        if ('szudán' in original_query or 'sudan' in original_query) and \
           ('dél' not in original_query and 'south' not in original_query):
            # Ha csak "szudán" van (nem "dél-szudán"), akkor mindkét országot adjuk vissza
            if 'sd' in countries and 'ss' not in countries:
                countries.append('ss')  # Dél-Szudán hozzáadása
        
        # 4. Részleges egyezések keresése (pl. "német" -> "németország")
        # CSAK akkor, ha a kérésben NEM szerepelnek színek, mintázatok vagy kontinensek
        # Ezzel elkerüljük a téves országfelismerést színes/mintázatos kérések esetén
        if not countries:
            # Ellenőrizzük, hogy van-e szín/mintázat a kérésben
            has_colors = any(color in query_lower for color in self.color_translations.keys())
            has_patterns = any(pattern in query_lower for pattern in self.pattern_translations.keys())
            has_continents = any(continent in query_lower for continent in self.continent_translations.keys())
            
            # Csak akkor keresünk részleges országnév egyezéseket, ha nincs más keresési kritérium
            if not (has_colors or has_patterns or has_continents):
                for country_name, country_code in sorted_countries:
                    # Ellenőrizzük, hogy a kérésben szereplő szavak része-e az országnévnek
                    query_words = query_lower.split()
                    for word in query_words:
                        if len(word) >= 5 and word in country_name:  # Minimum 5 karakter (szigorúbb)
                            countries.append(country_code)
                            break
        
        return list(set(countries))  # Duplikátumok eltávolítása
    
    def search_by_colors(self, colors: List[str]) -> List[str]:
        """Keresés színek alapján"""
        matching_flags = []
        
        for country_code, features in self.flag_features.items():
            flag_colors = [c.lower() for c in features.get('unique_colors', [])]
            dominant_colors = features.get('dominant_colors', [])
            
            # Ellenőrizzük, hogy minden kért szín megvan-e (bővített logikával)
            match = True
            for color in colors:
                color_lower = color.lower()
                
                # Színárnyalatok figyelembevétele
                color_found = False
                if color_lower == 'green':
                    # 'zöld' keresés tartalmazza a világos, sötét és alap zöldet is
                    if any(green_variant in flag_colors for green_variant in ['green', 'lightgreen', 'darkgreen']):
                        color_found = True
                elif color_lower == 'blue':
                    # 'kék' keresés tartalmazza a világos, sötét és alap kéket is
                    if any(blue_variant in flag_colors for blue_variant in ['blue', 'lightblue', 'darkblue']):
                        color_found = True
                elif color_lower == 'black':
                    # Fekete színnél ellenőrizzük a dominancia mértékét
                    # Csak akkor fogadjuk el, ha a fekete legalább 5% a zászlóból
                    if 'black' in flag_colors:
                        black_percentage = 0
                        for color_info in dominant_colors:
                            if color_info.get('name') == 'black':
                                black_percentage = color_info.get('percentage', 0)
                                break
                        
                        # Csak akkor fogadjuk el, ha a fekete jelentős része a zászlónak (>= 5%)
                        if black_percentage >= 5.0:
                            color_found = True
                else:
                    # Egyéb színek esetén pontos egyezés
                    if color_lower in flag_colors:
                        color_found = True
                
                if not color_found:
                    match = False
                    break
            
            if match:
                matching_flags.append(country_code)
        
        return matching_flags
    
    def search_by_patterns(self, patterns: List[str]) -> List[str]:
        """Keresés mintázatok alapján"""
        matching_flags = []
        
        for country_code, features in self.flag_features.items():
            stripes = features.get('stripes', {})
            shapes = features.get('shapes', {})
            
            match = True
            for pattern in patterns:
                if pattern == 'stripes':
                    if not (stripes.get('has_horizontal_stripes') or stripes.get('has_vertical_stripes')):
                        match = False
                        break
                elif pattern == 'bands':
                    if not (stripes.get('has_horizontal_bands') or stripes.get('has_vertical_bands')):
                        match = False
                        break
                elif pattern == 'stars':
                    # Csak a valóban jól ismert csillagos zászlók (szigorú lista)
                    real_star_countries = {
                        'us',  # USA - 50 fehér csillag
                        'cn',  # Kína - 5 sárga csillag
                        'br',  # Brazília - 27 csillag
                        'au',  # Ausztrália - 6 fehér csillag
                        'nz',  # Új-Zéland - 4 fehér csillag
                        'eu',  # EU - 12 sárga csillag
                        'cl',  # Chile - 1 fehér csillag
                        'lr',  # Libéria - 1 fehér csillag
                        'tr',  # Törökország - 1 fehér csillag és hold
                        'pk',  # Pakisztán - 1 fehér csillag és hold
                        'so',  # Szomália - 1 fehér csillag
                        'gh',  # Ghana - 1 fekete csillag
                        'ma',  # Marokkó - 1 zöld csillag
                        'my',  # Malajzia - 1 sárga csillag és hold
                        'sg',  # Szingapúr - 5 fehér csillag
                        'hn',  # Honduras - 5 kék csillag
                        've',  # Venezuela - 8 fehér csillag
                        'sy',  # Szíria - 2 zöld csillag
                        'vn',  # Vietnám - 1 sárga csillag
                        'kn',  # Saint Kitts and Nevis - 2 fehér csillag
                        'gp',  # Guadeloupe - 10 fekete csillag
                        'ph',  # Fülöp-szigetek - 8 csillag és nap
                        'dz',  # Algéria - 1 piros csillag és hold
                        'tn',  # Tunézia - 1 piros csillag és hold
                        'mr',  # Mauritánia - 1 sárga csillag és hold
                        'sn',  # Szenegál - 1 zöld csillag
                        'et',  # Etiópia - 1 sárga csillag
                        'cm',  # Kamerun - 1 sárga csillag
                        'tg',  # Togo - 1 fehér csillag
                        'cv',  # Zöld-foki Köztársaság - 10 sárga csillag
                        'km',  # Comore-szigetek - 4 fehér csillag és hold
                        'mm',  # Myanmar - 1 fehér csillag
                        'np',  # Nepál - nap és hold
                        'pg',  # Pápua Új-Guinea - 5 fehér csillag
                        'sb',  # Salamon-szigetek - 5 fehér csillag
                        'tv',  # Tuvalu - 9 sárga csillag
                        'nr',  # Nauru - 1 fehér csillag
                        'mh',  # Marshall-szigetek - 1 fehér csillag
                        'fm',  # Mikronézia - 4 fehér csillag
                        'ws',  # Szamoa - 5 fehér csillag
                        'ck',  # Cook-szigetek - 15 fehér csillag
                        'as',  # Amerikai Szamoa - fehér csillagok
                        'pr',  # Puerto Rico - 1 fehér csillag
                        'um',  # USA külső szigetek - fehér csillagok
                        'tl',  # Kelet-Timor - 1 fehér csillag
                    }
                    if country_code not in real_star_countries:
                        match = False
                        break
                elif pattern == 'cross':
                    if shapes.get('crosses', 0) == 0:
                        match = False
                        break
                elif pattern == 'circle':
                    if shapes.get('circles', 0) == 0:
                        match = False
                        break
            
            if match:
                matching_flags.append(country_code)
        
        return matching_flags
    
    def search_by_continents(self, continents: List[str]) -> List[str]:
        """Keresés kontinensek alapján"""
        if not continents:
            return []
        
        # Ha csak egy kontinens van, egyszerű keresés
        if len(continents) == 1:
            continent = continents[0]
            if continent in self.continent_countries:
                return self.continent_countries[continent]
            else:
                return []
        
        # Ha több kontinens van, metszetet képezünk (pl. "európai szigetek")
        matching_flags = None
        
        for continent in continents:
            if continent in self.continent_countries:
                continent_flags = set(self.continent_countries[continent])
                
                if matching_flags is None:
                    # Első kontinens
                    matching_flags = continent_flags
                else:
                    # Metszet az eddigi eredményekkel
                    matching_flags = matching_flags.intersection(continent_flags)
        
        return list(matching_flags) if matching_flags else []
    
    def search_by_complexity(self, query: str) -> List[str]:
        """Keresés komplexitás alapján"""
        matching_flags = []
        
        if 'egyszerű' in query.lower() or 'simple' in query.lower():
            # Alacsony komplexitású zászlók
            for country_code, features in self.flag_features.items():
                if features.get('complexity_score', 0) < 3:
                    matching_flags.append(country_code)
        
        elif 'bonyolult' in query.lower() or 'komplex' in query.lower() or 'complex' in query.lower():
            # Magas komplexitású zászlók
            for country_code, features in self.flag_features.items():
                if features.get('complexity_score', 0) > 6:
                    matching_flags.append(country_code)
        
        return matching_flags
    
    def search_by_star_details(self, query: str) -> List[str]:
        """Speciális csillag keresések (szám, méret, pozíció, szín)"""
        matching_flags = []
        query_lower = query.lower()
        
        # Csillag színe keresése - speciális logika
        star_color = None
        for color_hu, color_en in self.color_translations.items():
            if f"{color_hu} csillag" in query_lower or f"{color_en} star" in query_lower:
                star_color = color_en
                break
        
        if star_color:
            # Ismert csillag színek országonként (tudásbázis alapú)
            star_color_mapping = {
                'us': 'white',      # USA - fehér csillagok kék mezőn
                'cn': 'yellow',     # Kína - sárga csillagok piros mezőn
                'tr': 'white',      # Törökország - fehér csillag és hold piros mezőn
                'br': 'yellow',     # Brazília - sárga csillagok kék mezőn
                'au': 'white',      # Ausztrália - fehér csillagok kék mezőn
                'nz': 'white',      # Új-Zéland - fehér csillagok kék mezőn
                'pk': 'white',      # Pakisztán - fehér csillag és hold zöld mezőn
                'my': 'yellow',     # Malajzia - sárga csillag és hold kék mezőn
                'sg': 'white',      # Szingapúr - fehér csillagok piros mezőn
                'cl': 'white',      # Chile - fehér csillag kék mezőn
                'lr': 'white',      # Libéria - fehér csillag kék mezőn
                'uy': 'yellow',     # Uruguay - sárga nap (csillag-szerű)
                'ar': 'yellow',     # Argentína - sárga nap
                'in': 'blue',       # India - kék kerék (csillag-szerű)
                'eu': 'yellow',     # EU - sárga csillagok kék mezőn
                'bo': 'yellow',     # Bolívia - sárga nap
                'ec': 'yellow',     # Ecuador - sárga nap
                've': 'yellow',     # Venezuela - sárga csillagok kék mezőn
                'hn': 'blue',       # Honduras - kék csillagok fehér mezőn
                'ni': 'blue',       # Nicaragua - kék színek
                'sv': 'blue',       # Salvador - kék elemek
                'sy': 'green',      # Szíria - 2 zöld csillag
                'so': 'white',      # Szomália - fehér csillag kék mezőn

                'et': 'yellow',     # Etiópia - sárga csillag
                'gh': 'black',      # Ghána - fekete csillag
                'gp': 'black',      # Guadeloupe - fekete csillagok
                'us': 'white',      # USA - 50 fehér csillag kék mezőn
                'lr': 'white',      # Libéria - fehér csillag (USA-hoz hasonlóan)
                'tg': 'white',      # Togo - fehér csillag
                'cv': 'yellow',     # Zöld-foki Köztársaság - sárga csillagok
                'gn': 'red',        # Guinea - piros csillag (ha van)
                'ml': 'red',        # Mali - piros elemek
                'sn': 'green',      # Szenegál - zöld csillag
                'ma': 'green',      # Marokkó - zöld csillag
                'mr': 'yellow',     # Mauritánia - sárga hold és csillag
                'dz': 'red',        # Algéria - piros hold és csillag
                'tn': 'red',        # Tunézia - piros hold és csillag
                'ma': 'green',      # Marokkó - zöld csillag
                'ly': 'white',      # Líbia - fehér hold és csillag
                'eg': 'yellow',     # Egyiptom - sárga sas (csillag-szerű)
                'sd': 'yellow',     # Szudán - sárga elemek
                'er': 'yellow',     # Eritrea - sárga elemek
                'ss': 'yellow',     # Dél-Szudán - sárga csillag
                'cf': 'yellow',     # Közép-afrikai Köztársaság - sárga csillag
                'td': 'yellow',     # Csád - sárga elemek
                'cm': 'yellow',     # Kamerun - sárga csillag
                'gq': 'yellow',     # Egyenlítői-Guinea - sárga csillagok
                'ga': 'yellow',     # Gabon - sárga elemek
                'cg': 'yellow',     # Kongói Köztársaság - sárga elemek
                'cd': 'yellow',     # Kongói Demokratikus Köztársaság - sárga csillag
                'ao': 'yellow',     # Angola - sárga elemek
                'na': 'yellow',     # Namíbia - sárga nap
                'bw': 'blue',       # Botswana - kék elemek
                'za': 'yellow',     # Dél-Afrika - sárga elemek
                'sz': 'yellow',     # Szváziföld - sárga elemek
                'ls': 'blue',       # Lesotho - kék elemek
                'mw': 'red',        # Malawi - piros nap
                'zm': 'red',        # Zambia - piros sas
                'zw': 'red',        # Zimbabwe - piros csillag
                'mz': 'yellow',     # Mozambik - sárga csillag
                'mg': 'white',      # Madagaszkár - fehér elemek
                'mu': 'yellow',     # Mauritius - sárga elemek
                'sc': 'yellow',     # Seychelle-szigetek - sárga elemek
                'km': 'white',      # Comore-szigetek - fehér hold és csillagok
                'lk': 'yellow',     # Srí Lanka - sárga elemek
                'bt': 'white',      # Bhután - fehér sárkány
                'np': 'white',      # Nepál - fehér hold és nap
                'bd': 'red',        # Banglades - piros kör
                'mm': 'white',      # Myanmar - fehér csillag
                'th': 'white',      # Thaiföld - fehér elemek
                'vn': 'yellow',     # Vietnám - sárga csillag
                'ph': 'yellow',     # Fülöp-szigetek - sárga nap és csillagok
                'id': 'red',        # Indonézia - piros-fehér
                'bn': 'yellow',     # Brunei - sárga elemek
                'tl': 'white',      # Kelet-Timor - fehér csillag
                'pg': 'white',      # Pápua Új-Guinea - fehér csillagok
                'sb': 'white',      # Salamon-szigetek - fehér csillagok
                'vu': 'yellow',     # Vanuatu - sárga elemek

                'to': 'red',        # Tonga - piros kereszt
                'ws': 'white',      # Szamoa - fehér csillagok
                'tv': 'yellow',     # Tuvalu - sárga csillagok
                'nr': 'white',      # Nauru - fehér csillag
                'ki': 'yellow',     # Kiribati - sárga nap
                'mh': 'white',      # Marshall-szigetek - fehér csillag
                'fm': 'white',      # Mikronézia - fehér csillagok
                'pw': 'yellow',     # Palau - sárga hold
                'ck': 'white',      # Cook-szigetek - fehér csillagok
                'nu': 'yellow',     # Niue - sárga csillagok

                'tk': 'yellow',     # Tokelau - sárga csillagok
                'as': 'white',      # Amerikai Szamoa - fehér csillagok
                'gu': 'red',        # Guam - piros elemek
                'mp': 'blue',       # Északi Mariana-szigetek - kék csillag
                'vi': 'yellow',     # Amerikai Virgin-szigetek - sárga sas
                'pr': 'white',      # Puerto Rico - fehér csillag
                'um': 'white',      # USA külső szigetek - fehér csillagok
                'kn': 'white',      # Saint Kitts and Nevis - fehér csillagok fekete mezőn
            }
            
            # Keresés a tudásbázis alapján - csak azok az országok, amelyek tényleg csillagos zászlók
            for country_code, expected_color in star_color_mapping.items():
                if expected_color == star_color and country_code in self.flag_features:
                    # Csak azokat az országokat vesszük figyelembe, amelyek a tudásbázisban szerepelnek
                    # Ez kizárja a téves képfelismerési eredményeket (pl. Laosz, Kambodzsa, Maldív-szigetek)
                    matching_flags.append(country_code)
        
        # Csillag szám keresése
        star_count = None
        for modifier, value in self.star_modifiers.items():
            if modifier in query_lower and 'csillag' in query_lower:
                if isinstance(value, int):
                    star_count = value
                elif value == 'many':
                    star_count = 'many'
                break
        
        if star_count:
            # Ismert csillag számok tudásbázis alapján (kiegészítés a képfelismeréshez)
            known_star_counts = {
                'sy': 2,    # Szíria - 2 zöld csillag
                'us': 50,   # USA - 50 fehér csillag
                'eu': 12,   # EU - 12 sárga csillag
                'br': 27,   # Brazília - 27 csillag
                'cn': 5,    # Kína - 5 sárga csillag
                'au': 6,    # Ausztrália - 6 fehér csillag
                'nz': 4,    # Új-Zéland - 4 fehér csillag
                'hn': 5,    # Honduras - 5 kék csillag
                've': 8,    # Venezuela - 8 fehér csillag
                'bo': 1,    # Bolívia - 1 nap (csillag-szerű)
                'cl': 1,    # Chile - 1 fehér csillag
                'lr': 1,    # Libéria - 1 fehér csillag
                'my': 1,    # Malajzia - 1 sárga csillag
                'pk': 1,    # Pakisztán - 1 fehér csillag
                'tr': 1,    # Törökország - 1 fehér csillag
                'so': 1,    # Szomália - 1 fehér csillag
                'gh': 1,    # Ghána - 1 fekete csillag
                'ma': 1,    # Marokkó - 1 zöld csillag
                'dz': 1,    # Algéria - 1 piros csillag
                'tn': 1,    # Tunézia - 1 piros csillag
                'mr': 1,    # Mauritánia - 1 sárga csillag
                'kn': 2,    # Saint Kitts and Nevis - 2 fehér csillag
                'gp': 10,   # Guadeloupe - 10 fekete csillag
            }
            
            for country_code, features in self.flag_features.items():
                shapes = features.get('shapes', {})
                stars = shapes.get('stars', 0)
                
                # Használjuk a tudásbázist, ha elérhető
                if country_code in known_star_counts:
                    stars = known_star_counts[country_code]
                
                if isinstance(star_count, int):
                    if stars == star_count:
                        matching_flags.append(country_code)
                elif star_count == 'many':
                    if stars >= 5:  # 5 vagy több csillag = sok
                        matching_flags.append(country_code)
        
        # Speciális kombinációk
        special_patterns = {
            'sarokban': 'corner_star',
            'középen': 'center_star', 
            'közepén': 'center_star',
            'felső': 'top_star',
            'bal': 'left_star'
        }
        
        for pattern, star_type in special_patterns.items():
            if pattern in query_lower and 'csillag' in query_lower:
                # Egyszerű heurisztika a pozíció alapján
                for country_code, features in self.flag_features.items():
                    shapes = features.get('shapes', {})
                    if shapes.get('stars', 0) > 0:
                        # USA, Libéria = sarokban, Kína = sarokban, stb.
                        if star_type == 'corner_star' and country_code in ['us', 'lr', 'my']:
                            matching_flags.append(country_code)
                        elif star_type == 'center_star' and country_code in ['so', 'pk', 'tr']:
                            matching_flags.append(country_code)
        
        return list(set(matching_flags))  # Duplikátumok eltávolítása
    
    def search_by_color_count(self, query: str) -> List[str]:
        """Keresés színek száma alapján"""
        matching_flags = []
        
        # Számok keresése a kérésben
        numbers = re.findall(r'\d+', query)
        
        if numbers:
            target_count = int(numbers[0])
            
            if 'szín' in query.lower() or 'color' in query.lower():
                for country_code, features in self.flag_features.items():
                    if features.get('color_count', 0) == target_count:
                        matching_flags.append(country_code)
        
        # Speciális esetek
        if 'tricolor' in query.lower() or 'háromszínű' in query.lower():
            for country_code, features in self.flag_features.items():
                if features.get('is_tricolor', False):
                    matching_flags.append(country_code)
        
        elif 'bicolor' in query.lower() or 'kétszínű' in query.lower():
            for country_code, features in self.flag_features.items():
                if features.get('is_bicolor', False):
                    matching_flags.append(country_code)
        
        return matching_flags
    
    def extract_symbolic_elements(self, query: str) -> List[str]:
        """Szimbolikus elemek kinyerése a kérésből"""
        symbolic_elements = []
        query_lower = query.lower()
        
        # Pontos szóhatár ellenőrzés a félreértések elkerülésére
        import re
        for symbolic_hu, symbolic_en in self.symbolic_translations.items():
            # Szóhatár ellenőrzés: a szó előtt és után szóhatár kell legyen
            pattern = r'\b' + re.escape(symbolic_hu) + r'\b'
            if re.search(pattern, query_lower):
                symbolic_elements.append(symbolic_en)
        
        return list(set(symbolic_elements))
    
    def search_by_symbolic_elements(self, symbolic_elements: List[str]) -> List[str]:
        """Keresés szimbolikus elemek alapján"""
        matching_flags = []
        
        for country_code, features in self.flag_features.items():
            symbolic = features.get('symbolic', {})
            shapes = features.get('shapes', {})
            
            match = True
            for element in symbolic_elements:
                if element == 'human' and not symbolic.get('has_human', False):
                    match = False
                    break
                elif element == 'animal':
                    if not symbolic.get('has_animal', False):
                        match = False
                        break
                    else:
                        # Kizárjuk azokat az országokat, ahol a "has_animal" téves
                        # (csak címerben, túl kicsi, stilizált, vagy nem domináns állat)
                        false_animal_flags = {
                            'gf',  # French Guiana - kakas túl kicsi/stilizált
                            'sb',  # Solomon Islands - sas túl kicsi  
                            'bb',  # Barbados - hal a szigonyban, nem domináns
                            'tv',  # Tuvalu - apró halak
                            'ki',  # Kiribati - madár túl stilizált
                            'nr',  # Nauru - madár túl kicsi
                            'pw',  # Palau - hal túl stilizált
                            'mh',  # Marshall Islands - madár túl kicsi
                            'fm',  # Micronesia - nincs valódi állat
                            'vu',  # Vanuatu - disznó fog túl stilizált
                            'to',  # Tonga - nincs állat, csak növény
                            'ls',  # Lesotho - ló csak a címerben
                            'gy',  # Guyana - jaguár csak a címerben
                            'za',  # South Africa - springbok csak a címerben
                            'ke',  # Kenya - oroszlán csak a címerben
                            'ag',  # Antigua and Barbuda - madár túl stilizált
                            'sz',  # Eswatini - állatok csak a címerben
                            'md',  # Moldova - sas emberi elemekkel, nem állat-központú
                            'mw',  # Malawi - oroszlán csak a címerben
                            'gd',  # Grenada - nutmeg nem igazi állat
                            'fj',  # Fiji - galamb csak a címerben
                            'pg',  # Papua New Guinea - madár csak a címerben
                            'kz',  # Kazakhstan - sas túl stilizált
                            've',  # Venezuela - ló csak a címerben
                            'al',  # Albania - sas stilizált, nem domináns
                            'lk',  # Sri Lanka - oroszlán csak a címerben
                            'pa',  # Panama - madár csak a címerben
                            'au',  # Australia - kenguru és emu csak a címerben
                            'nz',  # New Zealand - kiwi csak a címerben
                            'mn',  # Mongolia - ló túl stilizált (soyombo)
                            'kg',  # Kyrgyzstan - sas túl stilizált
                        }
                        if country_code in false_animal_flags:
                            match = False
                            break
                elif element == 'plant' and not symbolic.get('has_plant', False):
                    match = False
                    break
                elif element == 'weapon' and not symbolic.get('has_weapon', False):
                    match = False
                    break
                elif element == 'building' and not symbolic.get('has_building', False):
                    match = False
                    break
                elif element == 'celestial' and not symbolic.get('has_celestial', False):
                    match = False
                    break
                elif element == 'union_jack' and not symbolic.get('has_union_jack', False):
                    match = False
                    break
                elif element == 'cross' and not symbolic.get('has_cross', False):
                    match = False
                    break
                elif element == 'crescent' and not symbolic.get('has_crescent', False):
                    match = False
                    break
            
            if match:
                matching_flags.append(country_code)
        
        return matching_flags
    
    def combine_results(self, result_sets: List[List[str]]) -> List[str]:
        """Eredményhalmazok kombinálása (metszet)"""
        if not result_sets:
            return []
        
        # Az első halmaz az alap
        combined = set(result_sets[0])
        
        # Metszet képzése a többi halmazzal
        for result_set in result_sets[1:]:
            combined = combined.intersection(set(result_set))
        
        return list(combined)
    
    def search_flags(self, query: str) -> Dict[str, Any]:
        """Főkeresési függvény"""
        result_sets = []
        search_info = {
            'query': query,
            'colors': [],
            'patterns': [],
            'continents': [],
            'countries': [],
            'symbolic_elements': [],
            'complexity': [],
            'color_count': []
        }
        
        # Ellenőrizzük, hogy ez egy csillag színes keresés-e
        is_star_color_search = False
        for color_hu, color_en in self.color_translations.items():
            if f"{color_hu} csillag" in query.lower() or f"{color_en} star" in query.lower():
                is_star_color_search = True
                break
        
        # Színek keresése - DE csak akkor, ha ez NEM csillag színes keresés
        colors = self.extract_colors(query)
        if colors and not is_star_color_search:
            search_info['colors'] = colors
            color_results = self.search_by_colors(colors)
            if color_results:
                result_sets.append(color_results)
        
        # Mintázatok keresése
        patterns = self.extract_patterns(query)
        if patterns:
            search_info['patterns'] = patterns
            pattern_results = self.search_by_patterns(patterns)
            if pattern_results:
                result_sets.append(pattern_results)
        
        # Kontinensek keresése
        continents = self.extract_continents(query)
        if continents:
            search_info['continents'] = continents
            continent_results = self.search_by_continents(continents)
            if continent_results:
                result_sets.append(continent_results)
        
        # Országok keresése
        countries = self.extract_countries(query)
        if countries:
            search_info['countries'] = countries
            result_sets.append(countries)
        
        # Szimbolikus elemek keresése
        symbolic_elements = self.extract_symbolic_elements(query)
        if symbolic_elements:
            search_info['symbolic_elements'] = symbolic_elements
            symbolic_results = self.search_by_symbolic_elements(symbolic_elements)
            if symbolic_results:
                result_sets.append(symbolic_results)
        
        # Komplexitás keresése
        complexity_results = self.search_by_complexity(query)
        if complexity_results:
            search_info['complexity'] = ['found']
            result_sets.append(complexity_results)
        
        # Színszám keresése
        color_count_results = self.search_by_color_count(query)
        if color_count_results:
            search_info['color_count'] = ['found']
            result_sets.append(color_count_results)
        
        # Speciális csillag keresések
        star_detail_results = self.search_by_star_details(query)
        if star_detail_results:
            search_info['star_details'] = ['found']
            result_sets.append(star_detail_results)
        
        # Eredmények kombinálása
        if result_sets:
            final_results = self.combine_results(result_sets)
        else:
            # Ha nincs specifikus keresési feltétel, üres eredmény
            final_results = []
        
        # Eredmények rendezése komplexitás szerint
        final_results = self.rank_results(final_results, query)
        
        return {
            'results': final_results,  # Összes eredmény
            'total_count': len(final_results),
            'search_info': search_info,
            'flag_details': self.get_flag_details(final_results)
        }
    
    def rank_results(self, results: List[str], query: str) -> List[str]:
        """Eredmények rangsorolása relevancia szerint"""
        scored_results = []
        
        for country_code in results:
            score = 0
            features = self.flag_features.get(country_code, {})
            
            # Alappontszám
            score += 1
            
            # Bónusz pontok különböző kritériumok alapján
            if 'egyszerű' in query.lower():
                score += max(0, 5 - features.get('complexity_score', 0))
            elif 'bonyolult' in query.lower():
                score += features.get('complexity_score', 0)
            
            # Színek száma alapján
            if 'sok szín' in query.lower():
                score += features.get('color_count', 0)
            elif 'kevés szín' in query.lower():
                score += max(0, 5 - features.get('color_count', 0))
            
            scored_results.append((country_code, score))
        
        # Rendezés pontszám szerint
        scored_results.sort(key=lambda x: x[1], reverse=True)
        
        return [country_code for country_code, _ in scored_results]
    
    def get_flag_details(self, country_codes: List[str]) -> List[Dict]:
        """Zászló részletek lekérése"""
        details = []
        
        for code in country_codes:
            features = self.flag_features.get(code, {})
            country_name = self.countries.get(code, code.upper())
            
            symbolic = features.get('symbolic', {})
            
            detail = {
                'country_code': code,
                'country_name': country_name,
                'colors': features.get('unique_colors', []),
                'color_count': features.get('color_count', 0),
                'has_stripes': features.get('stripes', {}).get('has_horizontal_stripes', False) or 
                              features.get('stripes', {}).get('has_vertical_stripes', False),
                'has_bands': features.get('stripes', {}).get('has_horizontal_bands', False) or 
                            features.get('stripes', {}).get('has_vertical_bands', False),
                'has_stars': features.get('shapes', {}).get('stars', 0) > 0,
                'has_human': symbolic.get('has_human', False),
                'has_animal': symbolic.get('has_animal', False),
                'has_plant': symbolic.get('has_plant', False),
                'has_weapon': symbolic.get('has_weapon', False),
                'has_building': symbolic.get('has_building', False),
                'has_celestial': symbolic.get('has_celestial', False),
                'has_union_jack': symbolic.get('has_union_jack', False),
                'has_cross': symbolic.get('has_cross', False),
                'has_crescent': symbolic.get('has_crescent', False),
                'symbolic_details': symbolic.get('details', []),
                'complexity_score': features.get('complexity_score', 0),
                'file_path': features.get('file_path', '')
            }
            
            details.append(detail)
        
        return details
    
    def get_suggestions(self, query: str) -> List[str]:
        """Keresési javaslatok generálása"""
        suggestions = []
        
        # Színek alapján
        if not self.extract_colors(query):
            suggestions.extend([
                "Próbáld meg színekkel: 'piros és kék zászlók'",
                "Keress mintázatokra: 'csillagos zászlók'",
                "Kontinens szerint: 'európai zászlók'"
            ])
        
        # Ha nincs eredmény
        if not query.strip():
            suggestions.extend([
                "Példa kérések:",
                "- 'Piros, fehér és kék zászlók'",
                "- 'Csillagos zászlók Amerikából'",
                "- 'Egyszerű európai zászlók'",
                "- 'Csíkos zászlók'"
            ])
        
        return suggestions


def main():
    """Főprogram - tesztelés"""
    search_engine = FlagSearchEngine()
    
    # Teszt kérések
    test_queries = [
        "piros és kék zászlók",
        "csillagos zászlók",
        "európai zászlók",
        "egyszerű zászlók",
        "háromszínű zászlók"
    ]
    
    for query in test_queries:
        print(f"\nKérés: '{query}'")
        results = search_engine.search_flags(query)
        print(f"Találatok: {results['total_count']} db")
        
        for detail in results['flag_details'][:3]:
            print(f"- {detail['country_name']} ({detail['country_code']}): {detail['colors']}")


if __name__ == "__main__":
    main() 