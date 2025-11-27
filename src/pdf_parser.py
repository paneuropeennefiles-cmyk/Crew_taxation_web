# -*- coding: utf-8 -*-
"""
Script d'extraction des barèmes d'indemnités depuis un PDF
"""

import pdfplumber
import re
from datetime import datetime
from .database import (
    get_db_connection, add_price_period, get_countries
)


def parse_baremes_pdf(pdf_path):
    """
    Extrait les barèmes d'indemnités du PDF.

    Le PDF contient un tableau avec 3 colonnes répétées 3 fois:
    Pays | Au (date) | Montant | Pays | Au | Montant | Pays | Au | Montant

    Args:
        pdf_path: Chemin vers le fichier PDF

    Returns:
        Liste de dicts: [{'pays': str, 'date_debut': date|None, 'montant': float}, ...]
    """
    data = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            # Extraire le tableau
            table = page.extract_table()
            if not table:
                continue

            # Parcourir chaque ligne du tableau
            for row in table:
                if not row:
                    continue

                # Le tableau a 11 colonnes avec séparateurs vides:
                # Pays, Au, Montant, '', Pays, Au, Montant, '', Pays, Au, Montant
                # Indices des groupes: (0,1,2), (4,5,6), (8,9,10)
                group_indices = [(0, 1, 2), (4, 5, 6), (8, 9, 10)]

                for pays_idx, date_idx, montant_idx in group_indices:
                    if montant_idx >= len(row):
                        break

                    pays = row[pays_idx]
                    date_str = row[date_idx] if date_idx < len(row) else None
                    montant_str = row[montant_idx] if montant_idx < len(row) else None

                    # Ignorer les lignes d'en-tête ou vides
                    if not pays or pays.strip() in ['Pays', '']:
                        continue
                    if not montant_str:
                        continue

                    pays = pays.strip()

                    # Extraire le montant (ex: "176 €" -> 176.0)
                    montant_match = re.search(r'(\d+)', str(montant_str))
                    if not montant_match:
                        continue
                    montant = float(montant_match.group(1))

                    # Parser la date si présente (ex: "01/01/2024")
                    date_debut = None
                    if date_str and str(date_str).strip():
                        date_match = re.match(r'(\d{2})/(\d{2})/(\d{4})', str(date_str).strip())
                        if date_match:
                            day, month, year = date_match.groups()
                            date_debut = datetime(int(year), int(month), int(day)).date()

                    data.append({
                        'pays': pays,
                        'date_debut': date_debut,
                        'montant': montant
                    })

    return data


def get_country_mapping():
    """
    Crée un mapping des noms de pays français vers les préfixes ICAO.
    Utilise les données existantes dans la table countries.

    Returns:
        Dict {nom_pays_normalisé: icao_prefix}
    """
    # Récupérer les pays existants
    df_countries = get_countries()

    # Créer le mapping de base depuis la BDD
    mapping = {}
    for _, row in df_countries.iterrows():
        # Normaliser le nom (minuscule, sans accents pour comparaison)
        name_normalized = normalize_country_name(row['country_name'])
        mapping[name_normalized] = row['icao_prefix']

    # Ajouter des alias manuels pour les noms du PDF qui diffèrent
    aliases = {
        # Noms du PDF -> préfixe ICAO
        'allemagne': 'ED',
        'grande-bretagne': 'EG',
        'grande bretagne': 'EG',
        'royaume-uni': 'EG',
        'pays-bas': 'EH',
        'pays bas': 'EH',
        'etats-unis': 'K',
        'etats unis': 'K',
        'états-unis': 'K',
        'états unis': 'K',
        'coree du sud': 'RK',
        'corée du sud': 'RK',
        'coree du nord': 'ZK',
        'corée du nord': 'ZK',
        'emirats arabes unis': 'OM',
        'émirats arabes unis': 'OM',
        'russie': 'U',
        'chine': 'Z',
        'japon': 'RJ',
        'inde': 'VI',
        'bresil': 'SB',
        'brésil': 'SB',
        'australie': 'Y',
        'canada': 'C',
        'mexique': 'MM',
        'afrique du sud': 'FA',
        'nouvelle zelande': 'NZ',
        'nouvelle zélande': 'NZ',
        'egypte': 'HE',
        'égypte': 'HE',
        'arabie saoudite': 'OE',
        'iran': 'OI',
        'irak': 'OR',
        'israel': 'LL',
        'israël': 'LL',
        'turquie': 'LT',
        'grece': 'LG',
        'grèce': 'LG',
        'pologne': 'EP',
        'suede': 'ES',
        'suède': 'ES',
        'norvege': 'EN',
        'norvège': 'EN',
        'finlande': 'EF',
        'danemark': 'EK',
        'belgique': 'EB',
        'suisse': 'LS',
        'autriche': 'LO',
        'portugal': 'LP',
        'espagne': 'LE',
        'italie': 'LI',
        'france': 'LF',
        'irlande': 'EI',
        'islande': 'BI',
        'hongrie': 'LH',
        'roumanie': 'LR',
        'bulgarie': 'LB',
        'ukraine': 'UK',
        'thailande': 'VT',
        'thaïlande': 'VT',
        'vietnam': 'VV',
        'indonesie': 'WI',
        'indonésie': 'WI',
        'malaisie': 'WM',
        'philippines': 'RP',
        'singapour': 'WS',
        'hong-kong': 'VH',
        'hong kong': 'VH',
        'taiwan': 'RC',
        'taïwan': 'RC',
        'argentine': 'SA',
        'chili': 'SC',
        'colombie': 'SK',
        'perou': 'SP',
        'pérou': 'SP',
        'venezuela': 'SV',
        'equateur': 'SE',
        'équateur': 'SE',
        'bolivie': 'SL',
        'paraguay': 'SG',
        'uruguay': 'SU',
        'cuba': 'MU',
        'jamaique': 'MK',
        'jamaïque': 'MK',
        'bahamas': 'MY',
        'maroc': 'GM',
        'algerie': 'DA',
        'algérie': 'DA',
        'tunisie': 'DT',
        'libye': 'HL',
        'nigeria': 'DN',
        'kenya': 'HK',
        'ethiopie': 'HA',
        'éthiopie': 'HA',
        'ghana': 'DG',
        'senegal': 'GS',
        'sénégal': 'GS',
        'cote divoire': 'DI',
        "côte d'ivoire": 'DI',
        "cote d'ivoire": 'DI',
        'cote d ivoire': 'DI',
        "cote d'ivoire": 'DI',  # Apostrophe typographique U+2019
        'cameroun': 'FK',
        'congo': 'FC',
        'angola': 'FN',
        'mozambique': 'FQ',
        'zimbabwe': 'FV',
        'zambie': 'FL',
        'tanzanie': 'HT',
        'ouganda': 'HU',
        'madagascar': 'FM',
        'maurice': 'FI',
        'reunion': 'FM',
        'réunion': 'FM',
        'seychelles': 'FS',
        'qatar': 'OT',
        'koweit': 'OK',
        'koweït': 'OK',
        'bahrein': 'OB',
        'bahreïn': 'OB',
        'oman': 'OO',
        'jordanie': 'OJ',
        'liban': 'OL',
        'syrie': 'OS',
        'pakistan': 'OP',
        'bangladesh': 'VG',
        'sri lanka': 'VC',
        'nepal': 'VN',
        'népal': 'VN',
        'afghanistan': 'OA',
        'mongolie': 'ZM',
        'mongolie exterieure': 'ZM',
        'mongolie extérieure': 'ZM',
        'kazakhstan': 'UA',
        'ouzbekistan': 'UT',
        'ouzbékistan': 'UT',
        'turkmenistan': 'UT',
        'turkménistan': 'UT',
        'azerbaidjan': 'UB',
        'azerbaïdjan': 'UB',
        'georgie': 'UG',
        'géorgie': 'UG',
        'armenie': 'UD',
        'arménie': 'UD',
        'bielorussie': 'UM',
        'biélorussie': 'UM',
        'lettonie': 'EV',
        'lituanie': 'EY',
        'estonie': 'EE',
        'slovaquie': 'LZ',
        'slovenie': 'LJ',
        'slovénie': 'LJ',
        'croatie': 'LD',
        'serbie': 'LY',
        'montenegro': 'LY',
        'monténégro': 'LY',
        'macedoine': 'LW',
        'macédoine': 'LW',
        'albanie': 'LA',
        'bosnie-herzegovine': 'LQ',
        'bosnie-herzégovine': 'LQ',
        'kosovo': 'LY',
        'moldavie': 'LU',
        'chypre': 'LC',
        'malte': 'LM',
        'luxembourg': 'EL',
        'andorre': 'LE',
        'monaco': 'LN',
        'liechtenstein': 'LS',
        'nouvelle-caledonie': 'NW',
        'nouvelle-calédonie': 'NW',
        'polynesie francaise': 'NT',
        'polynésie française': 'NT',
        'fidji': 'NF',
        'papouasie': 'AY',
        'nouvelle-guinee-papouasie': 'AY',
        'nouvelle-guinée-papouasie': 'AY',
        # Territoires français
        'guadeloupe': 'TF',
        'martinique': 'TF',
        'guyane': 'SO',
        'mayotte': 'FM',
        'saint-barthelemy': 'TF',
        'saint-barthélemy': 'TF',
        'saint-martin': 'TF',
        'saint pierre et miquelon': 'LF',
        'wallis et futuna': 'NL',
        # Pays et territoires supplémentaires
        'anguilla': 'TU',
        'antigua': 'TA',
        'aruba': 'TN',
        'barbade': 'TB',
        'belize': 'MZ',
        'bermudes': 'TX',
        'botswana': 'FB',
        'brunei darussalam': 'WB',
        'brunei': 'WB',
        'burkina faso': 'DF',
        'burundi': 'HB',
        'benin': 'DB',
        'bénin': 'DB',
        'cambodge': 'VD',
        'cap-vert': 'GV',
        'caimans': 'MW',
        'caïmans': 'MW',
        'centrafricaine': 'FE',
        'comores': 'FM',
        'cook': 'NC',
        'costa-rica': 'MR',
        'costa rica': 'MR',
        'curacao': 'TN',
        'curaçao': 'TN',
        'djibouti': 'HD',
        'dominicaine': 'MD',
        'dominique': 'TD',
        'gabon': 'FO',
        'gambie': 'GB',
        'gibraltar': 'LX',
        'grenade': 'TG',
        'grenadines': 'TV',
        'guatemala': 'MG',
        'guinee equatoriale': 'FG',
        'guinée équatoriale': 'FG',
        'guinee-bissau': 'GG',
        'guinée-bissau': 'GG',
        'guyana': 'SY',
        'haiti': 'MT',
        'haïti': 'MT',
        'honduras': 'MH',
        'kirghizie': 'UC',
        'kiribati': 'NG',
        'laos': 'VL',
        'lesotho': 'FX',
        'liberia': 'GL',
        'macao': 'VM',
        'malawi': 'FW',
        'maldives': 'VR',
        'mali': 'GA',
        'marshall': 'PK',
        'mauritanie': 'GQ',
        'micronesie': 'PT',
        'micronésie': 'PT',
        'myanmar': 'VY',
        'birmanie': 'VY',
        'namibie': 'FY',
        'nauru': 'AN',
        'nicaragua': 'MN',
        'niue': 'NI',
        'palaos': 'PT',
        'panama': 'MP',
        'rwanda': 'HR',
        'saint kitts et nevis': 'TK',
        'saint kitts': 'TK',
        'saint vincent': 'TV',
        'sainte-lucie': 'TL',
        'sainte lucie': 'TL',
        'salomon': 'AG',
        'salvador': 'MS',
        'samoa occidentales': 'NS',
        'samoa': 'NS',
        'sao tome-et-principe': 'FP',
        'sao tomé-et-principe': 'FP',
        'sierra leone': 'GF',
        'somalie': 'HC',
        'soudan': 'HS',
        'soudan du sud': 'HJ',
        'surinam': 'SM',
        'swaziland': 'FD',
        'tadjikistan': 'UT',
        'tchad': 'FT',
        'timor oriental': 'WP',
        'timor': 'WP',
        'togo': 'DX',
        'tonga': 'NF',
        'trinite et tobago': 'TT',
        'trinité et tobago': 'TT',
        'tuvalu': 'NG',
        'vanuatu': 'NV',
        'yemen': 'OY',
        'yémen': 'OY',
        'erythree': 'HH',
        'érythrée': 'HH',
    }

    # Fusionner les alias dans le mapping
    for alias, prefix in aliases.items():
        mapping[alias] = prefix

    return mapping


def normalize_country_name(name):
    """
    Normalise un nom de pays pour la comparaison.
    - Minuscule
    - Supprime les accents courants
    - Supprime les parenthèses et leur contenu
    """
    if not name:
        return ''

    name = name.lower().strip()

    # Supprimer le contenu entre parenthèses
    name = re.sub(r'\([^)]*\)', '', name).strip()

    # Remplacements d'accents et caractères spéciaux
    replacements = {
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'à': 'a', 'â': 'a', 'ä': 'a',
        'î': 'i', 'ï': 'i',
        'ô': 'o', 'ö': 'o',
        'ù': 'u', 'û': 'u', 'ü': 'u',
        'ç': 'c', 'ñ': 'n',
        ''': "'", ''': "'", '´': "'", '`': "'"  # Apostrophes typographiques
    }

    for old, new in replacements.items():
        name = name.replace(old, new)

    # Normaliser les apostrophes (U+2019 -> U+0027)
    name = name.replace('\u2019', "'").replace('\u2018', "'")

    return name


def import_baremes_to_database(pdf_path, year=2024, clear_existing=False):
    """
    Importe les barèmes du PDF dans la table prices_periods.

    Args:
        pdf_path: Chemin vers le fichier PDF
        year: Année des barèmes
        clear_existing: Si True, supprime les prix existants pour cette année

    Returns:
        Tuple (nb_importes, nb_non_trouves, pays_non_trouves)
    """
    # Extraire les données du PDF
    print(f"[INFO] Extraction des données du PDF: {pdf_path}")
    data = parse_baremes_pdf(pdf_path)
    print(f"[INFO] {len(data)} entrées extraites du PDF")

    # Récupérer le mapping des pays
    country_mapping = get_country_mapping()

    # Supprimer les prix existants si demandé
    if clear_existing:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM prices_periods WHERE year = ?', (year,))
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        print(f"[INFO] {deleted} prix supprimés pour l'année {year}")

    # Importer les données
    imported = 0
    not_found = 0
    pays_non_trouves = set()

    for entry in data:
        pays = entry['pays']
        montant = entry['montant']
        date_debut = entry['date_debut']

        # Normaliser le nom du pays
        pays_normalized = normalize_country_name(pays)

        # Chercher le préfixe ICAO
        icao_prefix = country_mapping.get(pays_normalized)

        if not icao_prefix:
            # Essayer une recherche partielle
            for key, prefix in country_mapping.items():
                if pays_normalized in key or key in pays_normalized:
                    icao_prefix = prefix
                    break

        if icao_prefix:
            add_price_period(icao_prefix, year, montant, date_debut, pays)
            imported += 1
        else:
            not_found += 1
            pays_non_trouves.add(pays)

    print(f"[OK] {imported} prix importés dans prices_periods")
    if not_found > 0:
        print(f"[WARNING] {not_found} pays non trouvés:")
        for pays in sorted(pays_non_trouves):
            print(f"  - {pays}")

    return imported, not_found, pays_non_trouves


if __name__ == '__main__':
    """Script principal pour tester l'extraction"""
    import os

    # Chemin du PDF
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_path = os.path.join(script_dir, 'doc', 'Barèmes 2024.pdf')

    if not os.path.exists(pdf_path):
        print(f"[ERROR] Fichier non trouvé: {pdf_path}")
        exit(1)

    # Tester l'extraction
    print("=== Test d'extraction du PDF ===\n")
    data = parse_baremes_pdf(pdf_path)

    print(f"Nombre d'entrées extraites: {len(data)}\n")
    print("Exemples d'entrées:")
    for i, entry in enumerate(data[:10]):
        date_str = entry['date_debut'].strftime('%d/%m/%Y') if entry['date_debut'] else 'N/A'
        print(f"  {entry['pays']}: {entry['montant']}€ (début: {date_str})")

    print("\n=== Import dans la base de données ===\n")
    response = input("Voulez-vous importer ces données dans la BDD? (o/n): ")

    if response.lower() == 'o':
        imported, not_found, pays_non_trouves = import_baremes_to_database(
            pdf_path,
            year=2024,
            clear_existing=True
        )
        print(f"\n=== Import terminé ===")
