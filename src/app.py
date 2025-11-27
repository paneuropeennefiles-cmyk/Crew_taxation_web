# -*- coding: utf-8 -*-
"""
Application Flask pour le calcul des indemnités d'équipage
Version web de Crew_Taxation
"""

from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import os
import json
from werkzeug.utils import secure_filename
from datetime import datetime
import tempfile

# Imports des modules locaux
from .database import (
    get_config, set_config, get_prices_by_year, get_available_years,
    update_price, duplicate_prices_for_year, get_countries,
    import_airports_from_new_txt, search_airports, get_all_countries,
    add_airport_manual, get_prices_periods_by_year, add_price_period,
    get_db_connection, init_database
)
from .crew_taxation_logic import (
    parse_flight_log, identifier_rotations, calcul_indemnites_par_rotation,
    get_icao_mappings
)
from .pdf_generator import generate_pdf_report

# Chemins relatifs à la racine du projet (un niveau au-dessus de src)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__,
            template_folder=os.path.join(BASE_DIR, 'templates'),
            static_folder=os.path.join(BASE_DIR, 'static'))
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max

# Créer le dossier uploads s'il n'existe pas
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialiser la base de données au démarrage
init_database()

# Variable globale pour stocker les résultats du traitement
df_resultats = None

# Make the WSGI interface available at the top level so wfastcgi can get it.
wsgi_app = app.wsgi_app


@app.route('/')
def index():
    """Renders la page principale"""
    return render_template('index.html')


@app.route('/upload_excel', methods=['POST'])
def upload_excel():
    """Upload et validation du fichier Excel"""
    global df_resultats

    if 'excel_file' not in request.files:
        return jsonify(success=False, message='Aucun fichier recu.')

    file = request.files['excel_file']
    if file.filename == '':
        return jsonify(success=False, message='Nom de fichier vide.')

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    try:
        # Parse et validation du fichier
        df_excel = parse_flight_log(filepath)

        # Vérifier qu'on a les colonnes nécessaires
        required_cols = ['Date', 'ADEP', 'ADES', 'OFF', 'ON']
        missing_cols = [col for col in required_cols if col not in df_excel.columns]

        if missing_cols:
            return jsonify(success=False,
                         message=f'Colonnes manquantes: {", ".join(missing_cols)}')

        # Sauvegarder temporairement pour le traitement ultérieur
        df_resultats = None  # Réinitialiser les résultats

        return jsonify(
            success=True,
            message=f'Fichier {filename} charge avec succes',
            filename=filename,
            nb_vols=len(df_excel)
        )
    except Exception as e:
        return jsonify(success=False, message=f'Erreur lors du traitement: {str(e)}')


@app.route('/process_file', methods=['POST'])
def process_file():
    """Traite le fichier Excel et calcule les indemnités"""
    global df_resultats

    data = request.get_json()
    filename = data.get('filename')
    year = data.get('year', datetime.now().year)

    if not filename:
        return jsonify(success=False, message='Aucun fichier specifie.')

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    if not os.path.exists(filepath):
        return jsonify(success=False, message='Fichier non trouve.')

    try:
        # Récupérer les bases depuis la config
        bases_json = get_config('bases', '["LFLB", "LFLS", "LFLY", "LSGG", "LFLP"]')
        bases = json.loads(bases_json)

        # Parser le fichier
        df = parse_flight_log(filepath)

        # Identifier les rotations
        df = identifier_rotations(df, bases)

        # Récupérer les mappings ICAO depuis la BDD
        icao_to_country, icao_to_indem, icao_to_zone = get_icao_mappings(year)

        # Calculer les indemnités
        df_resultats = calcul_indemnites_par_rotation(
            df, bases, icao_to_country, icao_to_zone, icao_to_indem
        )

        # Préparer le résumé
        total_indemnites = df_resultats['Indemnite_Jour'].sum()
        nb_rotations = df_resultats['Rotation_ID'].nunique()
        nb_vols = len(df_resultats[~df_resultats['JourSansVol']])

        # Compter les problèmes diagnostiqués
        nb_problemes = len(df_resultats[df_resultats['Diagnostic'].notna() & (df_resultats['Diagnostic'] != '')])

        # Statistiques par pays
        pays_stats = df_resultats[df_resultats['Pays_Indemnisation'].notna()].groupby('Pays_Indemnisation')['Indemnite_Jour'].agg(['sum', 'count'])
        pays_stats = pays_stats.sort_values('sum', ascending=False)
        pays_details = [
            {
                'pays': pays,
                'count': int(stats['count']),
                'total': float(stats['sum'])
            }
            for pays, stats in pays_stats.iterrows()
        ]

        # Préparer les rotations pour l'affichage
        rotations = []
        for rot_id in df_resultats['Rotation_ID'].unique():
            if pd.isna(rot_id):
                continue

            rotation_data = df_resultats[df_resultats['Rotation_ID'] == rot_id]
            total_rotation = rotation_data['Indemnite_Jour'].sum()

            vols = []
            for _, vol in rotation_data.iterrows():
                # Fonction helper pour gérer les valeurs NaN
                def safe_get(value, default=''):
                    return value if pd.notna(value) else default

                vols.append({
                    'date': safe_get(vol.get('Date'), ''),
                    'adep': safe_get(vol.get('ADEP'), ''),
                    'ades': safe_get(vol.get('ADES'), ''),
                    'off': safe_get(vol.get('OFF'), ''),
                    'on': safe_get(vol.get('ON'), ''),
                    'zone': safe_get(vol.get('Zone'), ''),
                    'indemnite': float(vol.get('Indemnite_Jour', 0)) if pd.notna(vol.get('Indemnite_Jour')) else 0.0,
                    'pays': safe_get(vol.get('Pays_Indemnisation'), ''),
                    'flight_no': safe_get(vol.get('Flight No.'), ''),
                    'jour_sans_vol': bool(vol.get('JourSansVol', False)),
                    'diagnostic': safe_get(vol.get('Diagnostic'), '')
                })

            rotations.append({
                'id': rot_id,
                'total': float(total_rotation),
                'vols': vols
            })

        return jsonify(
            success=True,
            summary={
                'total_indemnites': float(total_indemnites),
                'nb_rotations': int(nb_rotations),
                'nb_vols': int(nb_vols),
                'nb_problemes': int(nb_problemes),
                'pays_details': pays_details
            },
            rotations=rotations
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify(success=False, message=f'Erreur lors du traitement: {str(e)}')


@app.route('/export_results', methods=['POST'])
def export_results():
    """Exporte les résultats en Excel"""
    global df_resultats

    if df_resultats is None or df_resultats.empty:
        return jsonify(success=False, message='Aucun resultat a exporter.')

    try:
        # Créer un fichier temporaire
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'export_indemnites_{timestamp}.xlsx'
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Créer un writer Excel
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Feuille détails
            df_resultats.to_excel(writer, sheet_name='Details', index=False)

            # Feuille résumé par rotation
            resume_rotation = df_resultats.groupby('Rotation_ID')['Indemnite_Jour'].sum().reset_index()
            resume_rotation.columns = ['Rotation_ID', 'Total_Indemnites']
            resume_rotation.to_excel(writer, sheet_name='Resume_Rotation', index=False)

            # Feuille résumé par pays
            resume_pays = df_resultats[df_resultats['Pays_Indemnisation'].notna()].groupby('Pays_Indemnisation').agg({
                'Indemnite_Jour': 'sum',
                'ADES': 'count'
            }).reset_index()
            resume_pays.columns = ['Pays', 'Total_Indemnites', 'Nombre_Indemnites']
            resume_pays = resume_pays.sort_values('Total_Indemnites', ascending=False)
            resume_pays.to_excel(writer, sheet_name='Resume_Pays', index=False)

            # Feuille statistiques générales
            stats = pd.DataFrame({
                'Metrique': ['Nombre de rotations', 'Nombre de vols', 'Total des indemnites (EUR)'],
                'Valeur': [
                    df_resultats['Rotation_ID'].nunique(),
                    len(df_resultats[~df_resultats['JourSansVol']]),
                    df_resultats['Indemnite_Jour'].sum()
                ]
            })
            stats.to_excel(writer, sheet_name='Statistiques', index=False)

        return send_file(
            filepath,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        return jsonify(success=False, message=f'Erreur lors de l\'exportation: {str(e)}')


@app.route('/export_pdf', methods=['POST'])
def export_pdf():
    """Génère et exporte un rapport PDF avec l'identité visuelle Pan Européenne"""
    global df_resultats

    if df_resultats is None or df_resultats.empty:
        return jsonify(success=False, message='Aucun resultat a exporter.')

    try:
        data = request.get_json()
        year = data.get('year', datetime.now().year)

        # Préparer le résumé
        total_indemnites = df_resultats['Indemnite_Jour'].sum()
        nb_rotations = df_resultats['Rotation_ID'].nunique()
        nb_vols = len(df_resultats[~df_resultats['JourSansVol']])
        nb_problemes = len(df_resultats[df_resultats['Diagnostic'].notna() & (df_resultats['Diagnostic'] != '')])

        # Statistiques par pays
        pays_stats = df_resultats[df_resultats['Pays_Indemnisation'].notna()].groupby('Pays_Indemnisation')['Indemnite_Jour'].agg(['sum', 'count'])
        pays_stats = pays_stats.sort_values('sum', ascending=False)
        pays_details = [
            {
                'pays': pays,
                'count': int(stats['count']),
                'total': float(stats['sum'])
            }
            for pays, stats in pays_stats.iterrows()
        ]

        summary_data = {
            'total_indemnites': float(total_indemnites),
            'nb_rotations': int(nb_rotations),
            'nb_vols': int(nb_vols),
            'nb_problemes': int(nb_problemes),
            'pays_details': pays_details
        }

        # Préparer les rotations
        rotations = []
        for rot_id in df_resultats['Rotation_ID'].unique():
            if pd.isna(rot_id):
                continue

            rotation_data = df_resultats[df_resultats['Rotation_ID'] == rot_id]
            total_rotation = rotation_data['Indemnite_Jour'].sum()

            vols = []
            for _, vol in rotation_data.iterrows():
                def safe_get(value, default=''):
                    return value if pd.notna(value) else default

                vols.append({
                    'date': safe_get(vol.get('Date'), ''),
                    'adep': safe_get(vol.get('ADEP'), ''),
                    'ades': safe_get(vol.get('ADES'), ''),
                    'off': safe_get(vol.get('OFF'), ''),
                    'on': safe_get(vol.get('ON'), ''),
                    'zone': safe_get(vol.get('Zone'), ''),
                    'indemnite': float(vol.get('Indemnite_Jour', 0)) if pd.notna(vol.get('Indemnite_Jour')) else 0.0,
                    'pays': safe_get(vol.get('Pays_Indemnisation'), ''),
                    'flight_no': safe_get(vol.get('Flight No.'), ''),
                    'jour_sans_vol': bool(vol.get('JourSansVol', False)),
                    'diagnostic': safe_get(vol.get('Diagnostic'), '')
                })

            rotations.append({
                'id': rot_id,
                'total': float(total_rotation),
                'vols': vols
            })

        # Préparer les prix par pays utilisés
        # Récupérer les pays uniques du traitement
        pays_utilises = df_resultats['Pays_Indemnisation'].dropna().unique()

        # Récupérer les prix depuis la BDD pour ces pays
        from .database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()

        countries_prices = {}
        for pays in pays_utilises:
            cursor.execute('''
                SELECT c.country_name, ph.price, ph.year
                FROM countries c
                LEFT JOIN prices_history ph ON c.icao_prefix = ph.icao_prefix AND ph.year = ?
                WHERE c.country_name = ?
                ORDER BY ph.year DESC
            ''', (year, pays))

            rows = cursor.fetchall()
            if rows:
                countries_prices[pays] = [
                    {
                        'price': row['price'] if row['price'] is not None else 0.0,
                        'valid_from': f"Année {row['year']}" if row['year'] is not None else 'Par défaut'
                    }
                    for row in rows
                ]

        # Générer le PDF
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'rapport_indemnites_{timestamp}.pdf'
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        generate_pdf_report(filepath, summary_data, rotations, countries_prices)

        return send_file(
            filepath,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify(success=False, message=f'Erreur lors de la generation du PDF: {str(e)}')


@app.route('/get_config', methods=['GET'])
def get_configuration():
    """Récupère la configuration actuelle"""
    try:
        bases_json = get_config('bases', '["LFLB", "LFLS", "LFLY", "LSGG", "LFLP"]')
        bases = json.loads(bases_json)

        return jsonify(
            success=True,
            bases=bases
        )
    except Exception as e:
        return jsonify(success=False, message=str(e))


@app.route('/save_config', methods=['POST'])
def save_configuration():
    """Sauvegarde la configuration"""
    try:
        data = request.get_json()
        bases = data.get('bases', [])

        # Valider les bases (doivent être des codes OACI de 4 lettres)
        for base in bases:
            if not isinstance(base, str) or len(base) != 4 or not base.isalpha():
                return jsonify(success=False, message=f'Code OACI invalide: {base}')

        set_config('bases', json.dumps(bases))

        return jsonify(success=True, message='Configuration sauvegardee')
    except Exception as e:
        return jsonify(success=False, message=str(e))


@app.route('/get_prices/<int:year>', methods=['GET'])
def get_prices(year):
    """Récupère les prix pour une année donnée"""
    try:
        df_prices = get_prices_by_year(year)

        prices = []
        for _, row in df_prices.iterrows():
            prices.append({
                'icao_prefix': row['icao_prefix'],
                'country': row['country_name'],
                'zone': row['zone'],
                'price': float(row['price']) if pd.notna(row['price']) else 0.0
            })

        return jsonify(success=True, prices=prices)
    except Exception as e:
        return jsonify(success=False, message=str(e))


@app.route('/get_available_years', methods=['GET'])
def get_years():
    """Récupère les années disponibles"""
    try:
        years = get_available_years()
        return jsonify(success=True, years=years)
    except Exception as e:
        return jsonify(success=False, message=str(e))


@app.route('/update_price', methods=['POST'])
def update_country_price():
    """Met à jour le prix d'un pays"""
    try:
        data = request.get_json()
        icao_prefix = data.get('icao_prefix')
        year = data.get('year')
        price = data.get('price')

        if not icao_prefix or year is None or price is None:
            return jsonify(success=False, message='Parametres manquants')

        update_price(icao_prefix, year, price)

        return jsonify(success=True, message='Prix mis a jour')
    except Exception as e:
        return jsonify(success=False, message=str(e))


@app.route('/duplicate_year', methods=['POST'])
def duplicate_year():
    """Duplique les prix d'une année vers une autre"""
    try:
        data = request.get_json()
        source_year = data.get('source_year')
        target_year = data.get('target_year')

        if not source_year or not target_year:
            return jsonify(success=False, message='Annees manquantes')

        success = duplicate_prices_for_year(source_year, target_year)

        if success:
            return jsonify(success=True, message=f'Prix dupliques de {source_year} vers {target_year}')
        else:
            return jsonify(success=False, message=f'L\'annee {target_year} existe deja')

    except Exception as e:
        return jsonify(success=False, message=str(e))


@app.route('/import_prices', methods=['POST'])
def import_prices():
    """Importe les prix depuis un fichier Excel"""
    try:
        if 'prices_file' not in request.files:
            return jsonify(success=False, message='Aucun fichier recu')

        file = request.files['prices_file']
        if file.filename == '':
            return jsonify(success=False, message='Nom de fichier vide')

        year = int(request.form.get('year', datetime.now().year))

        # Sauvegarder temporairement le fichier
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Lire le fichier Excel
        df = pd.read_excel(filepath)

        # Vérifier les colonnes requises
        required_cols = ['icao_prefix', 'price']
        if not all(col in df.columns for col in required_cols):
            return jsonify(success=False, message='Colonnes manquantes. Colonnes requises: icao_prefix, price')

        # Importer les prix
        count = 0
        for _, row in df.iterrows():
            icao_prefix = row['icao_prefix']
            price = float(row['price'])
            update_price(icao_prefix, year, price)
            count += 1

        # Supprimer le fichier temporaire
        os.remove(filepath)

        return jsonify(success=True, message=f'{count} prix importes pour l\'annee {year}')

    except Exception as e:
        return jsonify(success=False, message=f'Erreur lors de l\'importation: {str(e)}')


@app.route('/export_prices/<int:year>', methods=['GET'])
def export_prices(year):
    """Exporte les prix d'une année vers Excel"""
    try:
        df_prices = get_prices_by_year(year)

        if df_prices.empty:
            return jsonify(success=False, message='Aucun prix pour cette annee')

        # Créer un fichier Excel
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'prix_pays_{year}_{timestamp}.xlsx'
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        df_prices.to_excel(filepath, index=False)

        return send_file(
            filepath,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        return jsonify(success=False, message=f'Erreur lors de l\'exportation: {str(e)}')


@app.route('/import_airports_new', methods=['POST'])
def import_airports_new():
    """Importe les aéroports depuis un fichier Airport new.txt (type AD/AH + code IATA)"""
    try:
        if 'airports_file' not in request.files:
            return jsonify(success=False, message='Aucun fichier recu')

        file = request.files['airports_file']
        if file.filename == '':
            return jsonify(success=False, message='Nom de fichier vide')

        # Récupérer l'option clear_existing
        clear_existing = request.form.get('clear_existing', 'false').lower() == 'true'

        # Sauvegarder temporairement le fichier
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Importer les aéroports (type AD/AH + code IATA)
        count = import_airports_from_new_txt(filepath, clear_existing=clear_existing)

        # Supprimer le fichier temporaire
        os.remove(filepath)

        action = "remplaces" if clear_existing else "ajoutes/mis a jour"
        return jsonify(success=True, message=f'{count} aeroports de type AD/AH avec code IATA {action} avec succes')

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify(success=False, message=f'Erreur lors de l\'importation: {str(e)}')


@app.route('/search_airports', methods=['GET'])
def search_airports_route():
    """Recherche des aéroports avec filtres"""
    try:
        search_term = request.args.get('search', None)
        country = request.args.get('country', None)
        airport_type = request.args.get('type', None)
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))

        df, total = search_airports(search_term, country, airport_type, limit, offset)

        airports = []
        for _, row in df.iterrows():
            airports.append({
                'icao_code': row['icao_code'],
                'iata_code': row['iata_code'] if pd.notna(row['iata_code']) else '',
                'name': row['name'] if pd.notna(row['name']) else '',
                'country': row['country'] if pd.notna(row['country']) else '',
                'country_name': row['country_name'] if pd.notna(row['country_name']) else row['country'],
                'type': row['type'] if pd.notna(row['type']) else '',
                'latitude': float(row['latitude']) if pd.notna(row['latitude']) else 0.0,
                'longitude': float(row['longitude']) if pd.notna(row['longitude']) else 0.0
            })

        return jsonify(success=True, airports=airports, total=total)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify(success=False, message=f'Erreur lors de la recherche: {str(e)}')


@app.route('/get_countries', methods=['GET'])
def get_countries_route():
    """Récupère la liste de tous les pays depuis la table countries"""
    try:
        countries = get_all_countries()
        return jsonify(success=True, countries=countries)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify(success=False, message=f'Erreur lors de la récupération des pays: {str(e)}')


@app.route('/add_airport', methods=['POST'])
def add_airport_route():
    """Ajoute un aéroport manuellement"""
    try:
        data = request.get_json()

        icao_code = data.get('icao_code', '').strip()
        iata_code = data.get('iata_code', '').strip()
        name = data.get('name', '').strip()
        country = data.get('country', '').strip()
        airport_type = data.get('type', 'AD').strip()
        latitude = data.get('latitude', None)
        longitude = data.get('longitude', None)

        # Convertir les coordonnées en float si elles sont fournies
        if latitude is not None and latitude != '':
            try:
                latitude = float(latitude)
            except ValueError:
                latitude = None

        if longitude is not None and longitude != '':
            try:
                longitude = float(longitude)
            except ValueError:
                longitude = None

        # Appeler la fonction d'ajout
        success, message = add_airport_manual(
            icao_code=icao_code,
            iata_code=iata_code,
            name=name,
            country=country,
            airport_type=airport_type,
            latitude=latitude,
            longitude=longitude
        )

        return jsonify(success=success, message=message)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify(success=False, message=f'Erreur lors de l\'ajout: {str(e)}')


@app.route('/get_prices_periods/<int:year>', methods=['GET'])
def get_prices_periods(year):
    """Récupère les prix avec leurs périodes de validité pour une année"""
    try:
        df_prices = get_prices_periods_by_year(year)

        # Regrouper par pays pour avoir toutes les périodes
        prices = {}
        for _, row in df_prices.iterrows():
            prefix = row['icao_prefix']
            if prefix not in prices:
                prices[prefix] = {
                    'icao_prefix': prefix,
                    'country': row['country_name'],
                    'zone': row['zone'],
                    'periods': []
                }

            if pd.notna(row['price']):
                valid_from = row['valid_from'] if pd.notna(row['valid_from']) else None
                prices[prefix]['periods'].append({
                    'valid_from': valid_from,
                    'price': float(row['price'])
                })

        # Convertir en liste triée par pays
        result = sorted(prices.values(), key=lambda x: x['country'] if x['country'] else '')

        return jsonify(success=True, prices=result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify(success=False, message=str(e))


@app.route('/add_price_period', methods=['POST'])
def add_price_period_route():
    """Ajoute un prix pour une période donnée"""
    try:
        data = request.get_json()
        icao_prefix = data.get('icao_prefix')
        year = data.get('year')
        price = data.get('price')
        valid_from = data.get('valid_from')  # Format: 'YYYY-MM-DD' ou None

        if not icao_prefix or year is None or price is None:
            return jsonify(success=False, message='Paramètres manquants')

        add_price_period(icao_prefix, year, price, valid_from)

        return jsonify(success=True, message='Prix ajouté avec succès')
    except Exception as e:
        return jsonify(success=False, message=str(e))


@app.route('/delete_price_period', methods=['POST'])
def delete_price_period():
    """Supprime un prix pour une période donnée"""
    try:
        data = request.get_json()
        icao_prefix = data.get('icao_prefix')
        year = data.get('year')
        valid_from = data.get('valid_from')  # Format: 'YYYY-MM-DD' ou None

        if not icao_prefix or year is None:
            return jsonify(success=False, message='Paramètres manquants')

        conn = get_db_connection()
        cursor = conn.cursor()

        if valid_from:
            cursor.execute('''
                DELETE FROM prices_periods
                WHERE icao_prefix = ? AND year = ? AND valid_from = ?
            ''', (icao_prefix, year, valid_from))
        else:
            cursor.execute('''
                DELETE FROM prices_periods
                WHERE icao_prefix = ? AND year = ? AND valid_from IS NULL
            ''', (icao_prefix, year))

        conn.commit()
        conn.close()

        return jsonify(success=True, message='Prix supprimé')
    except Exception as e:
        return jsonify(success=False, message=str(e))


@app.route('/import_pdf_baremes', methods=['POST'])
def import_pdf_baremes():
    """Importe les barèmes depuis un fichier PDF"""
    try:
        if 'pdf_file' not in request.files:
            return jsonify(success=False, message='Aucun fichier reçu')

        file = request.files['pdf_file']
        if file.filename == '':
            return jsonify(success=False, message='Nom de fichier vide')

        year = int(request.form.get('year', datetime.now().year))
        clear_existing = request.form.get('clear_existing', 'false').lower() == 'true'

        # Sauvegarder temporairement le fichier
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Importer les barèmes
        from .pdf_parser import import_baremes_to_database
        imported, not_found, pays_non_trouves = import_baremes_to_database(
            filepath, year=year, clear_existing=clear_existing
        )

        # Supprimer le fichier temporaire
        os.remove(filepath)

        message = f'{imported} prix importés pour l\'année {year}'
        if not_found > 0:
            message += f' ({not_found} pays non trouvés)'

        return jsonify(
            success=True,
            message=message,
            imported=imported,
            not_found=not_found,
            missing_countries=list(pays_non_trouves)
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify(success=False, message=f'Erreur lors de l\'importation: {str(e)}')


@app.route('/get_airport_stats', methods=['GET'])
def get_airport_stats():
    """Récupère les statistiques sur les aéroports"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Total d'aéroports
        cursor.execute('SELECT COUNT(*) as total FROM airports')
        total = cursor.fetchone()['total']

        # Types d'aéroports
        cursor.execute('SELECT type, COUNT(*) as count FROM airports GROUP BY type ORDER BY count DESC')
        types = [{'type': row['type'], 'count': row['count']} for row in cursor.fetchall()]

        # Pays avec le plus d'aéroports
        cursor.execute('SELECT country, COUNT(*) as count FROM airports GROUP BY country ORDER BY count DESC LIMIT 10')
        countries = [{'country': row['country'], 'count': row['count']} for row in cursor.fetchall()]

        conn.close()

        return jsonify(success=True, total=total, types=types, countries=countries)

    except Exception as e:
        return jsonify(success=False, message=f'Erreur: {str(e)}')


if __name__ == '__main__':
    import os
    HOST = os.environ.get('SERVER_HOST', 'localhost')
    try:
        PORT = int(os.environ.get('SERVER_PORT', '5555'))
    except ValueError:
        PORT = 5555
    app.run(HOST, PORT, debug=True)
