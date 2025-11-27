# -*- coding: utf-8 -*-
"""
Module de gestion de la base de données SQLite pour l'application Crew Taxation Web
"""

import sqlite3
import pandas as pd
from datetime import datetime
import os

# Chemin de la base de données à la racine du projet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'crew_taxation.db')

def get_db_connection():
    """Crée et retourne une connexion à la base de données"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Pour accéder aux colonnes par nom
    return conn

def init_database():
    """Initialise la base de données avec toutes les tables nécessaires"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Table des aéroports
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS airports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            iata_code TEXT,
            icao_code TEXT NOT NULL UNIQUE,
            name TEXT,
            latitude REAL,
            longitude REAL,
            elevation INTEGER,
            timezone TEXT,
            city_code TEXT,
            country TEXT,
            city TEXT,
            state TEXT,
            county TEXT,
            type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Table des pays/zones avec préfixes OACI
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS countries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            icao_prefix TEXT NOT NULL UNIQUE,
            country_name TEXT NOT NULL,
            zone TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Table de l'historique des prix par pays et par année
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prices_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            icao_prefix TEXT NOT NULL,
            year INTEGER NOT NULL,
            price REAL NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (icao_prefix) REFERENCES countries(icao_prefix),
            UNIQUE(icao_prefix, year)
        )
    ''')

    # Nouvelle table des prix avec périodes de validité
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prices_periods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            icao_prefix TEXT NOT NULL,
            year INTEGER NOT NULL,
            valid_from DATE,
            price REAL NOT NULL,
            country_name TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(icao_prefix, year, valid_from)
        )
    ''')

    # Index pour la nouvelle table
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_prices_periods_prefix_year ON prices_periods(icao_prefix, year)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_prices_periods_valid_from ON prices_periods(valid_from)')

    # Table de configuration (bases, etc.)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL UNIQUE,
            value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Index pour améliorer les performances
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_airports_icao ON airports(icao_code)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_airports_iata ON airports(iata_code)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_countries_prefix ON countries(icao_prefix)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_prices_year ON prices_history(year)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_prices_active ON prices_history(is_active)')

    conn.commit()
    conn.close()
    print(f"[OK] Base de donnees initialisee: {DB_PATH}")

def import_airports_from_csv(csv_path):
    """Importe les aéroports depuis le fichier CSV"""
    if not os.path.exists(csv_path):
        print(f"⚠ Fichier non trouvé: {csv_path}")
        return 0

    df = pd.read_csv(csv_path)
    conn = get_db_connection()
    cursor = conn.cursor()

    count = 0
    for _, row in df.iterrows():
        # Ignorer les lignes sans code ICAO
        icao_code = row.get('icao', '')
        if pd.isna(icao_code) or icao_code == '':
            continue

        try:
            cursor.execute('''
                INSERT OR REPLACE INTO airports
                (iata_code, icao_code, name, latitude, longitude, elevation,
                 timezone, city_code, country, city, state, county, type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                row.get('code', ''),
                icao_code,
                row.get('name', ''),
                row.get('latitude', 0.0),
                row.get('longitude', 0.0),
                row.get('elevation', 0),
                row.get('time_zone', ''),
                row.get('city_code', ''),
                row.get('country', ''),
                row.get('city', ''),
                row.get('state', ''),
                row.get('county', ''),
                row.get('type', '')
            ))
            count += 1
        except Exception as e:
            print(f"Erreur lors de l'import de {icao_code}: {e}")

    conn.commit()
    conn.close()
    print(f"[OK] {count} aeroports importes depuis {csv_path}")
    return count

def import_countries_from_excel(excel_path, year=None):
    """
    Importe les pays et leurs prix depuis le fichier Excel

    Args:
        excel_path: Chemin vers le fichier Country-OACI-Code.xlsx
        year: Année pour les prix (par défaut: année courante)
    """
    if not os.path.exists(excel_path):
        print(f"⚠ Fichier non trouvé: {excel_path}")
        return 0

    if year is None:
        year = datetime.now().year

    df = pd.read_excel(excel_path)
    conn = get_db_connection()
    cursor = conn.cursor()

    countries_count = 0
    prices_count = 0

    for _, row in df.iterrows():
        icao_prefix = row['ICAO']
        country_name = row['Country']
        zone = row['Zone']
        price = row['Indem']

        try:
            # Insérer ou mettre à jour le pays
            cursor.execute('''
                INSERT OR REPLACE INTO countries (icao_prefix, country_name, zone)
                VALUES (?, ?, ?)
            ''', (icao_prefix, country_name, zone))
            countries_count += 1

            # Insérer ou mettre à jour le prix pour l'année
            cursor.execute('''
                INSERT OR REPLACE INTO prices_history (icao_prefix, year, price, is_active)
                VALUES (?, ?, ?, 1)
            ''', (icao_prefix, year, price))
            prices_count += 1

        except Exception as e:
            print(f"Erreur lors de l'import de {icao_prefix}: {e}")

    conn.commit()
    conn.close()
    print(f"[OK] {countries_count} pays importes avec {prices_count} prix pour l'annee {year}")
    return countries_count

def set_config(key, value):
    """Définit une valeur de configuration"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR REPLACE INTO config (key, value, updated_at)
        VALUES (?, ?, ?)
    ''', (key, value, datetime.now().isoformat()))

    conn.commit()
    conn.close()

def get_config(key, default=None):
    """Récupère une valeur de configuration"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT value FROM config WHERE key = ?', (key,))
    row = cursor.fetchone()
    conn.close()

    return row['value'] if row else default

def get_airports():
    """Récupère tous les aéroports"""
    conn = get_db_connection()
    df = pd.read_sql_query('SELECT * FROM airports', conn)
    conn.close()
    return df

def get_countries():
    """Récupère tous les pays"""
    conn = get_db_connection()
    df = pd.read_sql_query('SELECT * FROM countries', conn)
    conn.close()
    return df

def get_prices_by_year(year=None):
    """
    Récupère les prix pour une année donnée

    Args:
        year: Année (par défaut: année courante)

    Returns:
        DataFrame avec icao_prefix, country_name, zone, price
    """
    if year is None:
        year = datetime.now().year

    conn = get_db_connection()
    query = '''
        SELECT c.icao_prefix, c.country_name, c.zone, p.price, p.year
        FROM countries c
        LEFT JOIN prices_history p ON c.icao_prefix = p.icao_prefix AND p.year = ?
        ORDER BY c.country_name
    '''
    df = pd.read_sql_query(query, conn, params=(year,))
    conn.close()
    return df

def get_available_years():
    """Récupère toutes les années disponibles dans l'historique des prix"""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Utiliser prices_periods comme source principale
    cursor.execute('SELECT DISTINCT year FROM prices_periods ORDER BY year DESC')
    years = [row['year'] for row in cursor.fetchall()]
    conn.close()
    return years

def update_price(icao_prefix, year, price):
    """Met à jour le prix pour un pays et une année"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR REPLACE INTO prices_history (icao_prefix, year, price, updated_at)
        VALUES (?, ?, ?, ?)
    ''', (icao_prefix, year, price, datetime.now().isoformat()))

    conn.commit()
    conn.close()

def duplicate_prices_for_year(source_year, target_year):
    """
    Duplique les prix d'une année source vers une année cible

    Args:
        source_year: Année source
        target_year: Année cible
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Verifier si l'annee cible existe deja
    cursor.execute('SELECT COUNT(*) as count FROM prices_history WHERE year = ?', (target_year,))
    if cursor.fetchone()['count'] > 0:
        print(f"[WARNING] L'annee {target_year} existe deja")
        conn.close()
        return False

    # Dupliquer les prix
    cursor.execute('''
        INSERT INTO prices_history (icao_prefix, year, price, is_active, created_at)
        SELECT icao_prefix, ?, price, 1, ?
        FROM prices_history
        WHERE year = ?
    ''', (target_year, datetime.now().isoformat(), source_year))

    count = cursor.rowcount
    conn.commit()
    conn.close()
    print(f"[OK] {count} prix dupliques de {source_year} vers {target_year}")
    return True

def iata_to_icao(iata_code):
    """Convertit un code IATA en code ICAO"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT icao_code FROM airports WHERE iata_code = ?', (iata_code,))
    row = cursor.fetchone()
    conn.close()
    return row['icao_code'] if row else iata_code

def get_country_info(icao_prefix):
    """Récupère les informations d'un pays par son préfixe ICAO"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM countries WHERE icao_prefix = ?', (icao_prefix,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_price_for_prefix(icao_prefix, year=None):
    """Récupère le prix pour un préfixe ICAO et une année"""
    if year is None:
        year = datetime.now().year

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT price FROM prices_history
        WHERE icao_prefix = ? AND year = ?
    ''', (icao_prefix, year))
    row = cursor.fetchone()
    conn.close()
    return row['price'] if row else 0.0


def get_price_for_prefix_with_date(icao_prefix, flight_date, year=None):
    """
    Récupère le prix pour un préfixe ICAO à une date donnée.
    Cherche le prix avec valid_from <= flight_date le plus récent.

    Args:
        icao_prefix: Préfixe ICAO du pays
        flight_date: Date du vol (datetime.date ou string 'YYYY-MM-DD')
        year: Année (par défaut: année de flight_date)

    Returns:
        Prix (float) ou 0.0 si non trouvé
    """
    # Convertir la date si nécessaire
    if isinstance(flight_date, str):
        flight_date = datetime.strptime(flight_date, '%Y-%m-%d').date()
    elif isinstance(flight_date, datetime):
        flight_date = flight_date.date()

    if year is None:
        year = flight_date.year

    conn = get_db_connection()
    cursor = conn.cursor()

    # Chercher le prix avec valid_from <= flight_date le plus récent
    # OU le prix sans valid_from (prix par défaut)
    cursor.execute('''
        SELECT price FROM prices_periods
        WHERE icao_prefix = ? AND year = ?
        AND (valid_from IS NULL OR valid_from <= ?)
        ORDER BY valid_from DESC NULLS LAST
        LIMIT 1
    ''', (icao_prefix, year, flight_date.isoformat()))

    row = cursor.fetchone()
    conn.close()

    if row:
        return row['price']

    # Fallback sur l'ancienne table prices_history
    return get_price_for_prefix(icao_prefix, year)


def migrate_prices_to_periods():
    """
    Migre les données de prices_history vers prices_periods.
    Les prix existants sont importés avec valid_from = NULL (prix par défaut).
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Vérifier s'il y a déjà des données dans prices_periods
    cursor.execute('SELECT COUNT(*) as count FROM prices_periods')
    if cursor.fetchone()['count'] > 0:
        print("[INFO] La table prices_periods contient déjà des données")
        conn.close()
        return False

    # Migrer les données
    cursor.execute('''
        INSERT INTO prices_periods (icao_prefix, year, valid_from, price, is_active, created_at)
        SELECT icao_prefix, year, NULL, price, is_active, created_at
        FROM prices_history
    ''')

    count = cursor.rowcount
    conn.commit()
    conn.close()

    print(f"[OK] {count} prix migrés vers prices_periods")
    return True


def add_price_period(icao_prefix, year, price, valid_from=None, country_name=None):
    """
    Ajoute ou met à jour un prix pour une période donnée.
    Vérifie les doublons car SQLite ne gère pas UNIQUE avec NULL.

    Args:
        icao_prefix: Préfixe ICAO du pays
        year: Année
        price: Montant de l'indemnité
        valid_from: Date de début de validité (None = prix par défaut)
        country_name: Nom du pays (optionnel)
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Convertir la date si nécessaire
    valid_from_str = None
    if valid_from:
        if isinstance(valid_from, str):
            valid_from_str = valid_from
        else:
            valid_from_str = valid_from.isoformat()

    # Vérifier si une entrée existe déjà (gère le cas NULL)
    if valid_from_str is None:
        cursor.execute('''
            SELECT id FROM prices_periods
            WHERE icao_prefix = ? AND year = ? AND valid_from IS NULL
        ''', (icao_prefix, year))
    else:
        cursor.execute('''
            SELECT id FROM prices_periods
            WHERE icao_prefix = ? AND year = ? AND valid_from = ?
        ''', (icao_prefix, year, valid_from_str))

    existing = cursor.fetchone()

    if existing:
        # Mettre à jour l'entrée existante
        cursor.execute('''
            UPDATE prices_periods
            SET price = ?, country_name = COALESCE(?, country_name), updated_at = ?
            WHERE id = ?
        ''', (price, country_name, datetime.now().isoformat(), existing['id']))
    else:
        # Insérer une nouvelle entrée
        cursor.execute('''
            INSERT INTO prices_periods (icao_prefix, year, valid_from, price, country_name, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, 1, ?)
        ''', (icao_prefix, year, valid_from_str, price, country_name, datetime.now().isoformat()))

    conn.commit()
    conn.close()


def get_prices_periods_by_year(year=None):
    """
    Récupère tous les pays avec leurs prix pour une année.
    Affiche tous les pays même s'ils n'ont pas de prix.

    Returns:
        DataFrame avec icao_prefix, country_name, zone, price, valid_from
    """
    if year is None:
        year = datetime.now().year

    conn = get_db_connection()
    # LEFT JOIN depuis countries pour voir tous les pays
    # même ceux sans prix pour l'année sélectionnée
    query = '''
        SELECT c.icao_prefix,
               c.country_name,
               COALESCE(c.zone, '') as zone,
               p.price,
               p.valid_from
        FROM countries c
        LEFT JOIN prices_periods p ON c.icao_prefix = p.icao_prefix AND p.year = ?
        ORDER BY c.country_name, p.valid_from
    '''
    df = pd.read_sql_query(query, conn, params=(year,))
    conn.close()
    return df

def import_airports_from_new_txt(txt_path, clear_existing=False):
    """
    Importe les aéroports depuis le fichier Airport new.txt (format tab-delimited)
    Ajoute/met à jour les aéroports (stratégie UPSERT)
    Ne garde que les aéroports de type AD/AH avec un code IATA

    Args:
        txt_path: Chemin vers le fichier Airport new.txt
        clear_existing: Si True, vide la table avant l'import

    Returns:
        Nombre d'aéroports importés
    """
    if not os.path.exists(txt_path):
        print(f"⚠ Fichier non trouve: {txt_path}")
        return 0

    conn = get_db_connection()
    cursor = conn.cursor()

    # Vider la table si demandé
    if clear_existing:
        cursor.execute('DELETE FROM airports')
        print("[OK] Table airports videe")

    count = 0
    errors = 0
    skipped_types = 0
    skipped_no_iata = 0

    with open(txt_path, 'r', encoding='utf-8') as f:
        # Sauter les 3 premières lignes d'en-tête
        for _ in range(3):
            next(f)

        # Lire la ligne d'en-têtes de colonnes
        headers = next(f).strip().split('\t')
        print(f"[INFO] Colonnes detectees: {len(headers)}")

        # Parser chaque ligne
        for line_num, line in enumerate(f, start=5):
            line = line.strip()
            if not line:
                continue

            try:
                # Séparer les champs par tabulation
                fields = line.split('\t')

                if len(fields) < 16:
                    errors += 1
                    if errors <= 5:
                        print(f"[WARNING] Ligne {line_num}: pas assez de champs ({len(fields)})")
                    continue

                # Extraire les champs pertinents
                # 0: Master gUID, 1: Identifier, 2: Responsible State, 3: Name,
                # 4: ICAO Code, 5: IATA Code, 6: Type, 7: Operation code,
                # 8: ARP latitude, 9: ARP Longitude, 10: Datum, ...

                airport_type = fields[6].strip()

                # Ne garder que les aéroports de type AD ou AH
                if airport_type not in ['AD', 'AH']:
                    skipped_types += 1
                    continue

                icao_code = fields[4].strip()
                iata_code = fields[5].strip() if fields[5].strip() else None
                name = fields[3].strip()
                country = fields[2].strip()

                # Parser les coordonnées (format: 68.7218472N ou 052.7847472W)
                lat_str = fields[8].strip()
                lon_str = fields[9].strip()

                # Convertir latitude
                if lat_str:
                    direction = lat_str[-1]  # N ou S
                    value = float(lat_str[:-1])
                    latitude = value if direction == 'N' else -value
                else:
                    latitude = None

                # Convertir longitude
                if lon_str:
                    direction = lon_str[-1]  # E ou W
                    value = float(lon_str[:-1])
                    longitude = value if direction == 'E' else -value
                else:
                    longitude = None

                # Insérer ou mettre à jour dans la base de données (UPSERT)
                # Ne garder que les aéroports avec code ICAO ET code IATA
                if icao_code and iata_code:
                    cursor.execute('''
                        INSERT OR REPLACE INTO airports (icao_code, iata_code, name, country, type, latitude, longitude)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        icao_code,
                        iata_code,
                        name,
                        country,
                        airport_type,
                        latitude,
                        longitude
                    ))
                    count += 1

                    # Afficher la progression tous les 100 aéroports
                    if count % 100 == 0:
                        print(f"[INFO] {count} aeroports importes...")
                elif icao_code and not iata_code:
                    skipped_no_iata += 1

            except Exception as e:
                errors += 1
                if errors <= 5:  # Afficher seulement les 5 premières erreurs
                    print(f"[ERROR] Ligne {line_num}: {str(e)}")

    conn.commit()
    conn.close()

    print(f"[OK] {count} aeroports de type AD/AH avec code IATA importes depuis {txt_path}")
    print(f"[INFO] {skipped_types} aeroports ignores (type != AD/AH)")
    print(f"[INFO] {skipped_no_iata} aeroports AD/AH ignores (sans code IATA)")
    if errors > 0:
        print(f"[WARNING] {errors} entrees n'ont pas pu etre parsees")

    return count

def search_airports(search_term=None, country=None, airport_type=None, limit=100, offset=0):
    """
    Recherche des aéroports avec filtres

    Args:
        search_term: Terme de recherche (code ICAO, IATA ou nom)
        country: Filtrer par pays
        airport_type: Filtrer par type (AD, HP, LS, etc.)
        limit: Nombre de résultats max
        offset: Offset pour pagination

    Returns:
        Tuple (liste d'aéroports, total count)
    """
    conn = get_db_connection()

    # Construction de la requête avec JOIN sur la table countries
    query = '''
        SELECT a.icao_code, a.iata_code, a.name, a.country, a.type, a.latitude, a.longitude,
               COALESCE(c.country_name, a.country) as country_name
        FROM airports a
        LEFT JOIN countries c ON SUBSTR(a.icao_code, 1, 2) = c.icao_prefix
        WHERE 1=1
    '''
    params = []

    if search_term:
        query += ' AND (a.icao_code LIKE ? OR a.iata_code LIKE ? OR a.name LIKE ?)'
        search_pattern = f'%{search_term}%'
        params.extend([search_pattern, search_pattern, search_pattern])

    if country:
        query += ' AND (a.country LIKE ? OR c.country_name LIKE ?)'
        params.extend([f'%{country}%', f'%{country}%'])

    if airport_type:
        query += ' AND a.type = ?'
        params.append(airport_type)

    # Compter le total
    count_query = query.replace('SELECT a.icao_code, a.iata_code, a.name, a.country, a.type, a.latitude, a.longitude,\n               COALESCE(c.country_name, a.country) as country_name', 'SELECT COUNT(*)')
    df_count = pd.read_sql_query(count_query, conn, params=params)
    total = int(df_count.iloc[0, 0])

    # Récupérer les résultats avec pagination
    query += ' ORDER BY a.icao_code LIMIT ? OFFSET ?'
    params.extend([limit, offset])

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()

    return df, total


def get_all_countries():
    """
    Récupère la liste de tous les pays depuis la table countries

    Returns:
        Liste de dictionnaires avec icao_prefix et country_name
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT icao_prefix, country_name FROM countries ORDER BY country_name')
    countries = [{'icao_prefix': row['icao_prefix'], 'country_name': row['country_name']} for row in cursor.fetchall()]

    conn.close()
    return countries


def populate_countries_from_mapping():
    """
    Remplit la table countries avec tous les pays du mapping ICAO.
    Utilisé pour avoir un référentiel complet des pays.
    """
    # Mapping complet des pays avec leurs préfixes ICAO et zones
    # Format: 'prefix': ('nom', 'zone')
    countries_data = {
        # Europe
        'LA': ('Albanie', 'Europe'),
        'LE': ('Espagne', 'Europe'),
        'ED': ('Allemagne', 'Europe'),
        'LO': ('Autriche', 'Europe'),
        'EB': ('Belgique', 'Europe'),
        'LB': ('Bulgarie', 'Europe'),
        'LC': ('Chypre', 'Europe'),
        'LD': ('Croatie', 'Europe'),
        'EK': ('Danemark', 'Europe'),
        'EE': ('Estonie', 'Europe'),
        'EF': ('Finlande', 'Europe'),
        'LF': ('France', 'Europe'),
        'LX': ('Gibraltar', 'Europe'),
        'EG': ('Grande-Bretagne', 'Europe'),
        'LG': ('Grèce', 'Europe'),
        'LH': ('Hongrie', 'Europe'),
        'EI': ('Irlande', 'Europe'),
        'BI': ('Islande', 'Europe'),
        'LI': ('Italie', 'Europe'),
        'EV': ('Lettonie', 'Europe'),
        'EY': ('Lituanie', 'Europe'),
        'EL': ('Luxembourg', 'Europe'),
        'LW': ('Macédoine', 'Europe'),
        'LM': ('Malte', 'Europe'),
        'LU': ('Moldavie', 'Europe'),
        'LN': ('Monaco', 'Europe'),
        'LY': ('Serbie', 'Europe'),
        'EN': ('Norvège', 'Europe'),
        'EH': ('Pays-Bas', 'Europe'),
        'EP': ('Pologne', 'Europe'),
        'LP': ('Portugal', 'Europe'),
        'LR': ('Roumanie', 'Europe'),
        'LZ': ('Slovaquie', 'Europe'),
        'LJ': ('Slovénie', 'Europe'),
        'ES': ('Suède', 'Europe'),
        'LS': ('Suisse', 'Europe'),
        'LQ': ('Bosnie-Herzégovine', 'Europe'),
        'UK': ('Ukraine', 'Europe'),
        'UM': ('Biélorussie', 'Europe'),
        'LT': ('Turquie', 'Europe'),
        # Afrique
        'DA': ('Algérie', 'Afrique'),
        'FN': ('Angola', 'Afrique'),
        'DB': ('Bénin', 'Afrique'),
        'FB': ('Botswana', 'Afrique'),
        'DF': ('Burkina Faso', 'Afrique'),
        'HB': ('Burundi', 'Afrique'),
        'FK': ('Cameroun', 'Afrique'),
        'GV': ('Cap-Vert', 'Afrique'),
        'FE': ('Centrafricaine', 'Afrique'),
        'FM': ('Comores', 'Afrique'),
        'FC': ('Congo', 'Afrique'),
        'DI': ("Côte d'Ivoire", 'Afrique'),
        'HD': ('Djibouti', 'Afrique'),
        'HE': ('Égypte', 'Afrique'),
        'HH': ('Érythrée', 'Afrique'),
        'HA': ('Éthiopie', 'Afrique'),
        'FO': ('Gabon', 'Afrique'),
        'GB': ('Gambie', 'Afrique'),
        'DG': ('Ghana', 'Afrique'),
        'FG': ('Guinée Équatoriale', 'Afrique'),
        'GG': ('Guinée-Bissau', 'Afrique'),
        'HK': ('Kenya', 'Afrique'),
        'FX': ('Lesotho', 'Afrique'),
        'GL': ('Libéria', 'Afrique'),
        'HL': ('Libye', 'Afrique'),
        'FW': ('Malawi', 'Afrique'),
        'GA': ('Mali', 'Afrique'),
        'GM': ('Maroc', 'Afrique'),
        'FI': ('Maurice', 'Afrique'),
        'GQ': ('Mauritanie', 'Afrique'),
        'FQ': ('Mozambique', 'Afrique'),
        'FY': ('Namibie', 'Afrique'),
        'DR': ('Niger', 'Afrique'),
        'DN': ('Nigéria', 'Afrique'),
        'HU': ('Ouganda', 'Afrique'),
        'HR': ('Rwanda', 'Afrique'),
        'FP': ('Sao Tomé-et-Principe', 'Afrique'),
        'GS': ('Sénégal', 'Afrique'),
        'FS': ('Seychelles', 'Afrique'),
        'GF': ('Sierra Leone', 'Afrique'),
        'HC': ('Somalie', 'Afrique'),
        'HS': ('Soudan', 'Afrique'),
        'HJ': ('Soudan du Sud', 'Afrique'),
        'FA': ('Afrique du Sud', 'Afrique'),
        'FD': ('Swaziland', 'Afrique'),
        'HT': ('Tanzanie', 'Afrique'),
        'FT': ('Tchad', 'Afrique'),
        'DX': ('Togo', 'Afrique'),
        'DT': ('Tunisie', 'Afrique'),
        'FL': ('Zambie', 'Afrique'),
        'FV': ('Zimbabwe', 'Afrique'),
        # Moyen-Orient
        'OA': ('Afghanistan', 'Moyen-Orient'),
        'OE': ('Arabie Saoudite', 'Moyen-Orient'),
        'OB': ('Bahreïn', 'Moyen-Orient'),
        'OM': ('Émirats Arabes Unis', 'Moyen-Orient'),
        'OI': ('Iran', 'Moyen-Orient'),
        'OR': ('Irak', 'Moyen-Orient'),
        'LL': ('Israël', 'Moyen-Orient'),
        'OJ': ('Jordanie', 'Moyen-Orient'),
        'OK': ('Koweït', 'Moyen-Orient'),
        'OL': ('Liban', 'Moyen-Orient'),
        'OO': ('Oman', 'Moyen-Orient'),
        'OT': ('Qatar', 'Moyen-Orient'),
        'OS': ('Syrie', 'Moyen-Orient'),
        'OY': ('Yémen', 'Moyen-Orient'),
        # Asie
        'UD': ('Arménie', 'Asie'),
        'UB': ('Azerbaïdjan', 'Asie'),
        'VG': ('Bangladesh', 'Asie'),
        'VY': ('Birmanie', 'Asie'),
        'WB': ('Brunei', 'Asie'),
        'VD': ('Cambodge', 'Asie'),
        'Z': ('Chine', 'Asie'),
        'RK': ('Corée du Sud', 'Asie'),
        'ZK': ('Corée du Nord', 'Asie'),
        'UG': ('Géorgie', 'Asie'),
        'VH': ('Hong Kong', 'Asie'),
        'VI': ('Inde', 'Asie'),
        'WI': ('Indonésie', 'Asie'),
        'RJ': ('Japon', 'Asie'),
        'UA': ('Kazakhstan', 'Asie'),
        'UC': ('Kirghizie', 'Asie'),
        'VL': ('Laos', 'Asie'),
        'VM': ('Macao', 'Asie'),
        'WM': ('Malaisie', 'Asie'),
        'VR': ('Maldives', 'Asie'),
        'ZM': ('Mongolie', 'Asie'),
        'VN': ('Népal', 'Asie'),
        'UT': ('Ouzbékistan', 'Asie'),
        'OP': ('Pakistan', 'Asie'),
        'RP': ('Philippines', 'Asie'),
        'U': ('Russie', 'Asie'),
        'WS': ('Singapour', 'Asie'),
        'VC': ('Sri Lanka', 'Asie'),
        'RC': ('Taïwan', 'Asie'),
        'VT': ('Thaïlande', 'Asie'),
        'WP': ('Timor Oriental', 'Asie'),
        'VV': ('Vietnam', 'Asie'),
        # Océanie
        'Y': ('Australie', 'Océanie'),
        'NF': ('Fidji', 'Océanie'),
        'NG': ('Kiribati', 'Océanie'),
        'PK': ('Marshall', 'Océanie'),
        'PT': ('Micronésie', 'Océanie'),
        'AN': ('Nauru', 'Océanie'),
        'NI': ('Niue', 'Océanie'),
        'NW': ('Nouvelle-Calédonie', 'Océanie'),
        'NZ': ('Nouvelle-Zélande', 'Océanie'),
        'AY': ('Papouasie', 'Océanie'),
        'NT': ('Polynésie Française', 'Océanie'),
        'AG': ('Salomon', 'Océanie'),
        'NS': ('Samoa', 'Océanie'),
        'NV': ('Vanuatu', 'Océanie'),
        'NC': ('Îles Cook', 'Océanie'),
        # Amérique du Nord
        'C': ('Canada', 'Amérique du Nord'),
        'K': ('États-Unis', 'Amérique du Nord'),
        'MM': ('Mexique', 'Amérique du Nord'),
        # Amérique Centrale et Caraïbes
        'TU': ('Anguilla', 'Caraïbes'),
        'TA': ('Antigua', 'Caraïbes'),
        'TN': ('Aruba', 'Caraïbes'),
        'MY': ('Bahamas', 'Caraïbes'),
        'TB': ('Barbade', 'Caraïbes'),
        'MZ': ('Belize', 'Amérique Centrale'),
        'TX': ('Bermudes', 'Caraïbes'),
        'MR': ('Costa Rica', 'Amérique Centrale'),
        'MU': ('Cuba', 'Caraïbes'),
        'TD': ('Dominique', 'Caraïbes'),
        'TG': ('Grenade', 'Caraïbes'),
        'TF': ('Guadeloupe', 'Caraïbes'),
        'MG': ('Guatemala', 'Amérique Centrale'),
        'MT': ('Haïti', 'Caraïbes'),
        'MH': ('Honduras', 'Amérique Centrale'),
        'MK': ('Jamaïque', 'Caraïbes'),
        'MN': ('Nicaragua', 'Amérique Centrale'),
        'MP': ('Panama', 'Amérique Centrale'),
        'MD': ('République Dominicaine', 'Caraïbes'),
        'TK': ('Saint Kitts et Nevis', 'Caraïbes'),
        'TV': ('Saint Vincent', 'Caraïbes'),
        'TL': ('Sainte-Lucie', 'Caraïbes'),
        'MS': ('Salvador', 'Amérique Centrale'),
        'TT': ('Trinité et Tobago', 'Caraïbes'),
        'MW': ('Îles Caïmans', 'Caraïbes'),
        # Amérique du Sud
        'SA': ('Argentine', 'Amérique du Sud'),
        'SL': ('Bolivie', 'Amérique du Sud'),
        'SB': ('Brésil', 'Amérique du Sud'),
        'SC': ('Chili', 'Amérique du Sud'),
        'SK': ('Colombie', 'Amérique du Sud'),
        'SE': ('Équateur', 'Amérique du Sud'),
        'SY': ('Guyana', 'Amérique du Sud'),
        'SG': ('Paraguay', 'Amérique du Sud'),
        'SP': ('Pérou', 'Amérique du Sud'),
        'SM': ('Surinam', 'Amérique du Sud'),
        'SU': ('Uruguay', 'Amérique du Sud'),
        'SV': ('Venezuela', 'Amérique du Sud'),
    }

    conn = get_db_connection()
    cursor = conn.cursor()

    count = 0
    for icao_prefix, (country_name, zone) in countries_data.items():
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO countries (icao_prefix, country_name, zone)
                VALUES (?, ?, ?)
            ''', (icao_prefix, country_name, zone))
            count += 1
        except Exception as e:
            print(f"Erreur pour {icao_prefix}: {e}")

    conn.commit()
    conn.close()

    print(f"[OK] {count} pays ajoutés/mis à jour dans la table countries")
    return count


def add_airport_manual(icao_code, iata_code, name, country, airport_type='AD', latitude=None, longitude=None):
    """
    Ajoute un aéroport manuellement à la base de données

    Args:
        icao_code: Code ICAO (4 lettres, obligatoire)
        iata_code: Code IATA (3 lettres, obligatoire)
        name: Nom de l'aéroport (obligatoire)
        country: Code pays (2 lettres ICAO prefix, obligatoire)
        airport_type: Type d'aéroport (AD par défaut)
        latitude: Latitude (optionnel)
        longitude: Longitude (optionnel)

    Returns:
        True si succès, False si échec
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Vérifier si l'aéroport existe déjà
        cursor.execute('SELECT icao_code FROM airports WHERE icao_code = ?', (icao_code,))
        if cursor.fetchone():
            conn.close()
            return False, "Un aéroport avec ce code ICAO existe déjà"

        # Valider les champs obligatoires
        if not icao_code or len(icao_code) != 4:
            conn.close()
            return False, "Le code ICAO doit contenir exactement 4 caractères"

        if not iata_code or len(iata_code) != 3:
            conn.close()
            return False, "Le code IATA doit contenir exactement 3 caractères"

        if not name:
            conn.close()
            return False, "Le nom de l'aéroport est obligatoire"

        if not country:
            conn.close()
            return False, "Le pays est obligatoire"

        # Insérer l'aéroport
        cursor.execute('''
            INSERT INTO airports (icao_code, iata_code, name, country, type, latitude, longitude)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            icao_code.upper(),
            iata_code.upper(),
            name.upper(),
            country.upper(),
            airport_type,
            latitude if latitude is not None else 0.0,
            longitude if longitude is not None else 0.0
        ))

        conn.commit()
        conn.close()

        return True, "Aéroport ajouté avec succès"

    except Exception as e:
        conn.close()
        return False, f"Erreur lors de l'ajout: {str(e)}"


if __name__ == '__main__':
    """Script d'initialisation de la base de données"""
    print("=== Initialisation de la base de données ===\n")

    # Initialiser la structure
    init_database()

    # Chemins des fichiers source (relatifs au script)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    airports_csv = os.path.join(script_dir, 'doc', 'airports.csv')
    countries_excel = os.path.join(script_dir, 'doc', 'Country-OACI-Code.xlsx')

    # Importer les données
    print("\n--- Import des données ---")
    import_airports_from_csv(airports_csv)
    import_countries_from_excel(countries_excel, year=2024)

    # Definir la configuration par defaut
    print("\n--- Configuration par defaut ---")
    import json
    bases_default = ['LFLB', 'LFLS', 'LFLY', 'LSGG', 'LFLP']
    set_config('bases', json.dumps(bases_default))
    print(f"[OK] Bases configurees: {bases_default}")

    print("\n=== Initialisation terminee ===")
