# -*- coding: utf-8 -*-
"""
Module contenant toute la logique métier pour le calcul des indemnités d'équipage
Adapté depuis Crew_Taxation.py pour utiliser la base de données SQLite
"""

import pandas as pd
from datetime import datetime, timedelta
import re
from .database import get_db_connection, iata_to_icao, get_price_for_prefix, get_country_info, get_price_for_prefix_with_date

def convertir_iata_en_oaci_df(df, colonnes_a_convertir=['ADEP', 'ADES']):
    """
    Remplace les codes IATA par les codes OACI dans les colonnes spécifiées du DataFrame
    en utilisant la base de données

    :param df: DataFrame contenant les colonnes à convertir
    :param colonnes_a_convertir: Liste des colonnes du df à convertir
    :return: DataFrame avec les codes convertis
    """
    df = df.copy()
    for col in colonnes_a_convertir:
        df[col] = df[col].apply(lambda x: iata_to_icao(x) if pd.notna(x) else x)
    return df

def get_icao_mappings(year=None):
    """
    Récupère les mappings ICAO depuis la base de données

    Returns:
        tuple: (icao_to_country, icao_to_indem, icao_to_zone)
    """
    if year is None:
        year = datetime.now().year

    conn = get_db_connection()
    query = '''
        SELECT c.icao_prefix, c.country_name, c.zone,
               COALESCE(p.price, 0) as price
        FROM countries c
        LEFT JOIN prices_history p ON c.icao_prefix = p.icao_prefix AND p.year = ?
    '''
    cursor = conn.cursor()
    cursor.execute(query, (year,))

    icao_to_country = {}
    icao_to_indem = {}
    icao_to_zone = {}

    for row in cursor.fetchall():
        prefix = row['icao_prefix']
        icao_to_country[prefix] = row['country_name']
        icao_to_indem[prefix] = row['price']
        icao_to_zone[prefix] = row['zone']

    conn.close()
    return icao_to_country, icao_to_indem, icao_to_zone

def parse_flight_log(fichier):
    """
    Parse un fichier Excel ou CSV de journal de vol

    :param fichier: Chemin vers le fichier Excel/CSV
    :return: DataFrame avec les vols parsés
    """
    # Gérer les fichiers CSV
    if fichier.lower().endswith('.csv'):
        try:
            df = pd.read_csv(fichier)

            # Détecter le format du CSV et adapter les colonnes
            # Format 1 : Colonnes standards (Date, ADEP, ADES, OFF, ON, Flight No.)
            # Format 2 : Format LogBook (flightDate, from, to, takeoffTime, landingTime, flightNumber)

            if 'flightDate' in df.columns and 'from' in df.columns:
                # Format LogBook détecté - conversion nécessaire
                print("Format LogBook détecté, conversion des colonnes...")

                # Créer le nouveau DataFrame avec les colonnes attendues
                df_converted = pd.DataFrame()

                # Convertir la date de 2025/01/03 vers 03-01-2025
                df_converted['Date'] = pd.to_datetime(df['flightDate']).dt.strftime('%d-%m-%Y')

                # Colonnes aéroports
                df_converted['ADEP'] = df['from']
                df_converted['ADES'] = df['to']

                # Extraire les heures de takeoffTime et landingTime
                # Format: "2025/01/03 14:02" -> "14:02"
                def extract_time(dt_str):
                    if pd.isna(dt_str) or dt_str == '':
                        return ''
                    try:
                        # Si c'est un datetime complet
                        if ' ' in str(dt_str):
                            return str(dt_str).split(' ')[1]
                        return str(dt_str)
                    except:
                        return ''

                df_converted['OFF'] = df['takeoffTime'].apply(extract_time)
                df_converted['ON'] = df['landingTime'].apply(extract_time)

                # Flight number
                df_converted['Flight No.'] = df['flightNumber']

                df = df_converted
                print(f"Conversion terminée: {len(df)} vols convertis")

            # Traitement standard
            try:
                df = df.dropna(subset=['ADEP', 'ADES'])
                df = convertir_iata_en_oaci_df(df)
                cols_to_drop = ['Reg.','Function','COM','Distance [NM]', 'Aircraft Type','Night','LND','Flight time','Block']
                cols_to_drop = [col for col in cols_to_drop if col in df.columns]
                return df.drop(columns=cols_to_drop)
            except Exception as e:
                print(f"Erreur lors du traitement standard: {e}")
                return df
        except Exception as e:
            raise Exception(f"Erreur lors de la lecture du fichier CSV: {e}")

    # Déterminer le moteur approprié selon l'extension du fichier
    engine = None
    if fichier.lower().endswith('.xlsx'):
        engine = 'openpyxl'
    elif fichier.lower().endswith('.xls'):
        engine = 'xlrd'
    else:
        # Essayer de détecter automatiquement
        try:
            engine = 'openpyxl'
            df_test = pd.read_excel(fichier, sheet_name=0, header=None, engine=engine, nrows=1)
        except:
            engine = 'xlrd'

    # Lecture préliminaire pour trouver l'index de la ligne d'en-tête
    try:
        df_temp = pd.read_excel(fichier, sheet_name=0, header=None, engine=engine)

        # Chercher l'indice de la ligne commençant par "Date"
        header_index = None
        for i, row in df_temp.iterrows():
            # Vérifie si la première cellule de la ligne contient "Date"
            if isinstance(row[0], str) and row[0].startswith("Date"):
                header_index = i
                break

        if header_index is None:
            print("Attention: Ligne d'en-tête 'Date' non trouvée. Lecture du fichier sans modification.")
            df = pd.read_excel(fichier, sheet_name=0, engine=engine)
        else:
            print(f"En-tête trouvée à la ligne {header_index}. Lecture à partir de cette ligne.")
            # Lire le fichier en utilisant la ligne trouvée comme en-tête
            df = pd.read_excel(fichier, sheet_name=0, header=header_index, engine=engine)
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier avec engine={engine}: {e}")
        # Essayer avec l'autre moteur
        try:
            alt_engine = 'xlrd' if engine == 'openpyxl' else 'openpyxl'
            print(f"Tentative avec engine={alt_engine}")
            df_temp = pd.read_excel(fichier, sheet_name=0, header=None, engine=alt_engine)

            header_index = None
            for i, row in df_temp.iterrows():
                if isinstance(row[0], str) and row[0].startswith("Date"):
                    header_index = i
                    break

            if header_index is None:
                df = pd.read_excel(fichier, sheet_name=0, engine=alt_engine)
            else:
                df = pd.read_excel(fichier, sheet_name=0, header=header_index, engine=alt_engine)
        except Exception as e2:
            print(f"Erreur lors de la lecture du fichier avec engine={alt_engine}: {e2}")
            raise Exception(f"Impossible de lire le fichier Excel. Formats supportés: .xlsx, .xls. Erreur: {e}")

    try:
        # Supprime les lignes où ADEP ou ADES sont vides ou NaN
        df = df.dropna(subset=['ADEP', 'ADES'])

        # Conversion IATA en OACI si nécessaire
        df = convertir_iata_en_oaci_df(df)

        # Supprime les colonnes suivantes si elles existent
        cols_to_drop = ['Reg.','Function','COM','Distance [NM]', 'Aircraft Type','Night','LND','Flight time','Block']
        cols_to_drop = [col for col in cols_to_drop if col in df.columns]
        log_flight = df.drop(columns=cols_to_drop)

        return log_flight
    except Exception as e:
        print(f"Erreur lors du traitement des données: {e}")
        print("Retour du DataFrame non traité")
        return df

def identifier_rotations(df, bases):
    """
    Identifie les rotations dans un journal de vol

    :param df: DataFrame avec les vols
    :param bases: Liste des codes OACI des bases
    :return: DataFrame avec une colonne Rotation_ID
    """
    df = df.copy()

    # Création d'une colonne DateTime pour trier chronologiquement les vols
    df['DateTime'] = pd.to_datetime(df['Date'] + ' ' + df['OFF'], format='%d-%m-%Y %H:%M')

    # Tri des vols par date et heure de départ
    df = df.sort_values('DateTime').reset_index(drop=True)

    # Création d'une colonne Date_only pour regrouper les vols par jour
    df['Date_only'] = df['DateTime'].dt.date

    # Liste des bases avec règle spéciale (la rotation peut se poursuivre le lendemain)
    special_bases = ['LFLY', 'LSGG']

    rotation_id = 0  # Compteur de rotation
    rotation_ids = [None] * len(df)  # Liste des IDs de rotation à affecter
    current_rotation_indexes = []  # Index des vols appartenant à la rotation en cours

    # Regroupement des vols par jour
    grouped_days = df.groupby('Date_only')
    all_dates = sorted(grouped_days.groups.keys())  # Liste des dates triées

    # Boucle principale sur chaque jour
    for i, date in enumerate(all_dates):
        day_flights = grouped_days.get_group(date)  # Vols du jour

        # --- Cas spécial : prolongation d'une rotation depuis la veille ---
        if i > 0 and not current_rotation_indexes:
            prev_date = all_dates[i - 1]

            # Si les deux jours sont consécutifs
            if (date - prev_date).days == 1:
                prev_day_flights = grouped_days.get_group(prev_date)

                if not prev_day_flights.empty:
                    last_flight = prev_day_flights.iloc[-1]  # Dernier vol de la veille

                    # Si ce vol est arrivé sur une base spéciale, et que le premier vol du jour suivant part de cette même base
                    if (last_flight['ADES'] in special_bases and
                        not day_flights.empty and
                        day_flights['ADEP'].iloc[0] == last_flight['ADES']):

                        # On récupère l'ID de rotation du vol précédent
                        prev_rotation_ids = df[df['Date_only'] == prev_date]['Rotation_ID'].tolist()
                        if prev_rotation_ids and prev_rotation_ids[-1] is not None:
                            current_rotation_id = prev_rotation_ids[-1]
                            rotation_id = int(current_rotation_id[3:]) - 1  # Récupère le numéro de rotation
                            current_rotation_indexes = [idx for idx, rid in enumerate(rotation_ids) if rid == current_rotation_id]

                        # On ajoute les vols du jour à la même rotation
                        current_rotation_indexes.extend(day_flights.index.tolist())
                        continue  # Passer directement au jour suivant

        # --- Début d'une nouvelle rotation ---
        if not current_rotation_indexes:
            # Si le premier vol du jour part d'une base autorisée
            if not day_flights.empty and day_flights['ADEP'].iloc[0] in bases:
                current_rotation_indexes.extend(day_flights.index.tolist())
        else:
            # Sinon, on poursuit la rotation existante avec les vols du jour
            current_rotation_indexes.extend(day_flights.index.tolist())

        # --- Vérification de fin de rotation ---
        if not day_flights.empty:
            last_flight = day_flights.iloc[-1]

            # Conditions de fin de rotation :
            # - Le dernier vol arrive à une base classique
            # - Ou bien une base spéciale mais aucun vol compatible le jour suivant
            if (last_flight['ADES'] in bases and
                (
                    last_flight['ADES'] not in special_bases or  # Base classique
                    i == len(all_dates) - 1 or  # Dernier jour de données
                    (i < len(all_dates) - 1 and (all_dates[i + 1] - date).days > 1) or  # Pas de vol le jour suivant
                    (i < len(all_dates) - 1 and grouped_days.get_group(all_dates[i + 1])['ADEP'].iloc[0] != last_flight['ADES'])  # Vol suivant ne part pas de la même base spéciale
                )):

                # Attribuer un ID à la rotation en cours
                rotation_label = f"ROT{rotation_id + 1:03d}"
                for idx in current_rotation_indexes:
                    rotation_ids[idx] = rotation_label
                current_rotation_indexes = []  # Réinitialiser la rotation
                rotation_id += 1  # Incrémenter l'identifiant

    # Si une rotation est restée ouverte à la fin des données, on lui attribue aussi un ID
    if current_rotation_indexes:
        rotation_label = f"ROT{rotation_id + 1:03d}"
        for idx in current_rotation_indexes:
            rotation_ids[idx] = rotation_label

    # Ajout de la colonne dans le DataFrame
    df['Rotation_ID'] = rotation_ids

    # Nettoyage des colonnes temporaires
    df = df.drop(columns=['DateTime', 'Date_only'])

    return df

def calcul_indemnites_par_rotation(df, bases, oaci_country, icao_to_zone, bareme_indemnites):
    """
    Calcule les indemnités pour chaque rotation selon les règles métier

    :param df: DataFrame avec les vols et Rotation_ID
    :param bases: Liste des bases
    :param oaci_country: Dictionnaire ICAO prefix -> pays
    :param icao_to_zone: Dictionnaire ICAO prefix -> zone
    :param bareme_indemnites: Dictionnaire ICAO prefix -> prix (fallback)
    :return: DataFrame enrichi avec les indemnités
    """
    def get_price_for_date(prefix, date_obj):
        """
        Récupère le prix pour un préfixe ICAO à une date donnée.
        Utilise les prix par période si disponibles, sinon le barème statique.
        """
        if pd.isna(date_obj):
            return bareme_indemnites.get(prefix, 0)

        # Essayer d'abord les prix par période
        try:
            price = get_price_for_prefix_with_date(prefix, date_obj)
            if price > 0:
                return price
        except:
            pass

        # Fallback sur le barème statique
        return bareme_indemnites.get(prefix, 0)

    df = df.copy()
    df['Date_obj'] = pd.to_datetime(df['Date'], format='%d-%m-%Y', errors='coerce')
    df['JourSansVol'] = df.get('JourSansVol', False)

    df['ON_time'] = pd.to_datetime(df['ON'], format='%H:%M').dt.time
    df['OFF_time'] = pd.to_datetime(df['OFF'], format='%H:%M').dt.time

    df['Indemnite_Jour'] = None
    df['Zone'] = None
    df['Pays_Indemnisation'] = None
    df['Diagnostic'] = None  # Colonne pour les alertes/diagnostics

    for rot_id in df['Rotation_ID'].unique():
        df_rot = df[df['Rotation_ID'] == rot_id].copy()

        date_min = df_rot['Date_obj'].min()
        date_max = df_rot['Date_obj'].max()

        # Sauter les rotations où date_min ou date_max est NaT
        if pd.isna(date_min) or pd.isna(date_max):
            continue

        tous_les_jours = pd.date_range(date_min, date_max, freq='D')
        jours_vol = df_rot['Date_obj'].unique()

        for jour in tous_les_jours:
            if jour not in jours_vol:
                ligne_off = {
                    'Date_obj': jour,
                    'Rotation_ID': rot_id,
                    'JourSansVol': True
                }
                df = pd.concat([df, pd.DataFrame([ligne_off])], ignore_index=True)

    df = df.sort_values(by=['Rotation_ID', 'Date_obj', 'OFF'], na_position='first').reset_index(drop=True)
    df['JourSansVol'] = df['JourSansVol'].fillna(False)

    for rot_id in df['Rotation_ID'].unique():
        df_rot = df[df['Rotation_ID'] == rot_id].copy()
        jours = sorted(df_rot['Date_obj'].dropna().unique())
        duree_rotation = len(jours)

        escales_prolongees = False
        escale_prolongee_prefix = None
        escale_prolongee_pays = None
        escale_prolongee_zone = None
        escale_prolongee_valeur = None

        for jour in jours:
            vols_jour = df_rot[(df_rot['Date_obj'] == jour) & (~df_rot['JourSansVol'])].copy()
            vols_jour = vols_jour.sort_values(by='OFF')
            vols_jour.reset_index(inplace=True)

            for i in range(len(vols_jour) - 1):
                on_time = vols_jour.loc[i, 'ON']
                off_time_next = vols_jour.loc[i + 1, 'OFF']
                ades_intermediaire = vols_jour.loc[i, 'ADES']

                try:
                    delta = (pd.to_datetime(off_time_next) - pd.to_datetime(on_time)).total_seconds() / 3600
                except:
                    delta = 0

                prefix = ades_intermediaire[:2]
                zone_prefix = icao_to_zone.get(prefix, '')

                if delta >= 7 and zone_prefix != 'Europe':
                    escales_prolongees = True
                    escale_prolongee_prefix = prefix
                    escale_prolongee_pays = oaci_country.get(prefix, '')
                    escale_prolongee_zone = zone_prefix
                    escale_prolongee_valeur = get_price_for_date(prefix, jour)

                    idx = vols_jour.loc[i, 'index']
                    df.loc[idx, 'Indemnite_Jour'] = escale_prolongee_valeur
                    df.loc[idx, 'Zone'] = escale_prolongee_zone
                    df.loc[idx, 'Pays_Indemnisation'] = escale_prolongee_pays

        vols_non_off = df_rot[~df_rot['JourSansVol']].copy()

        # Appliquer indemnité chaque fin de journée (nuitée)
        for jour in jours[:-1]:  # tous sauf dernier jour
            vols_jour = df_rot[(df_rot['Date_obj'] == jour) & (~df_rot['JourSansVol'])].copy()
            if not vols_jour.empty:
                ades_nuit = vols_jour.iloc[-1]['ADES']
                prefix = ades_nuit[:2]
                zone = icao_to_zone.get(prefix, '')
                valeur = get_price_for_date(prefix, jour)
                pays = oaci_country.get(prefix, '')
                idx = vols_jour.index[-1]
                df.loc[idx, 'Indemnite_Jour'] = valeur
                df.loc[idx, 'Zone'] = zone
                df.loc[idx, 'Pays_Indemnisation'] = pays

                # Diagnostic si problème
                diagnostic_msgs = []
                if not pays:
                    diagnostic_msgs.append(f"⚠️ Préfixe ICAO '{prefix}' (de {ades_nuit}) introuvable dans la base pays")
                if valeur == 0 and pays:
                    diagnostic_msgs.append(f"⚠️ Aucun prix défini pour {pays} ({prefix}) pour cette année")
                if diagnostic_msgs:
                    df.loc[idx, 'Diagnostic'] = ' | '.join(diagnostic_msgs)

        # Indemnisation des jours vides
        vols_jour_dict = df_rot[~df_rot['JourSansVol']].groupby('Date_obj')
        for jour in jours:
            if df_rot[df_rot['Date_obj'] == jour]['JourSansVol'].all():
                jours_precedents = [d for d in jours if d < jour]
                dernier_vol = None
                for d in reversed(jours_precedents):
                    vols = df_rot[(df_rot['Date_obj'] == d) & (~df_rot['JourSansVol'])]
                    if not vols.empty:
                        dernier_vol = vols.iloc[-1]
                        break
                if dernier_vol is not None:
                    ades = dernier_vol['ADES']
                    prefix = ades[:2]
                    zone = icao_to_zone.get(prefix, '')
                    valeur = get_price_for_date(prefix, jour)
                    pays = oaci_country.get(prefix, '')
                    idx = df[(df['Rotation_ID'] == rot_id) & (df['Date_obj'] == jour)].index
                    df.loc[idx, 'Indemnite_Jour'] = valeur
                    df.loc[idx, 'Zone'] = zone
                    df.loc[idx, 'Pays_Indemnisation'] = pays
                    df.loc[idx, 'ADEP'] = ades
                    df.loc[idx, 'ADES'] = ades
                    df.loc[idx, 'Flight No.'] = 'Jour sans vol'
                    df.loc[idx, 'Date'] = pd.to_datetime(jour).strftime('%d-%m-%Y')

                    # Diagnostic si problème
                    diagnostic_msgs = []
                    if not pays:
                        diagnostic_msgs.append(f"⚠️ Préfixe ICAO '{prefix}' (de {ades}) introuvable dans la base pays")
                    if valeur == 0 and pays:
                        diagnostic_msgs.append(f"⚠️ Aucun prix défini pour {pays} ({prefix}) pour cette année")
                    if diagnostic_msgs:
                        df.loc[idx, 'Diagnostic'] = ' | '.join(diagnostic_msgs)

        # Dernier jour de rotation : appliquer la règle avec les nouveaux cas
        if not vols_non_off.empty:
            idx_dernier_vol = vols_non_off.index[-1]
            dernier_ades = vols_non_off.iloc[-1]['ADES']
            dernier_jour = jours[-1] if jours else None
            prefix_jour = dernier_ades[:2]
            zone_jour = icao_to_zone.get(prefix_jour, '')
            valeur_jour = get_price_for_date(prefix_jour, dernier_jour)

            if duree_rotation == 1:  # Rotation d'une journée
                if not escales_prolongees:
                    # Cas 1.1: Rotation d'une journée sans escale prolongée
                    df.loc[idx_dernier_vol, 'Indemnite_Jour'] = 0.5 * valeur_jour
                    df.loc[idx_dernier_vol, 'Zone'] = zone_jour
                    df.loc[idx_dernier_vol, 'Pays_Indemnisation'] = oaci_country.get(prefix_jour, '')
                else:
                    # Cas 1.2: Rotation d'une journée avec escale prolongée
                    df.loc[idx_dernier_vol, 'Indemnite_Jour'] = escale_prolongee_valeur
                    df.loc[idx_dernier_vol, 'Zone'] = escale_prolongee_zone
                    df.loc[idx_dernier_vol, 'Pays_Indemnisation'] = escale_prolongee_pays
            else:  # Rotation de plusieurs jours
                # Vérifier si le jour précédent a des vols
                vols_jour_avant = vols_non_off[vols_non_off['Date_obj'] == jours[-2]]

                # Si le jour précédent a des vols, utiliser son ADES pour l'indemnité
                if not vols_jour_avant.empty:
                    ades_nuit = vols_jour_avant.iloc[-1]['ADES']
                    prefix_nuit = ades_nuit[:2]
                    zone_nuit = icao_to_zone.get(prefix_nuit, '')
                    valeur_nuit = get_price_for_date(prefix_nuit, jours[-2])
                    pays = oaci_country.get(prefix_nuit, '')

                    if zone_nuit == 'Europe' and not escales_prolongees:
                        # Cas 2.1: Dernière nuitée en Europe sans escale prolongée
                        df.loc[idx_dernier_vol, 'Indemnite_Jour'] = 0.5 * valeur_nuit
                        df.loc[idx_dernier_vol, 'Zone'] = zone_nuit
                        df.loc[idx_dernier_vol, 'Pays_Indemnisation'] = pays
                    elif zone_nuit == 'Europe' and escales_prolongees:
                        # Cas 2.2: Dernière nuitée en Europe avec escale prolongée
                        df.loc[idx_dernier_vol, 'Indemnite_Jour'] = escale_prolongee_valeur
                        df.loc[idx_dernier_vol, 'Zone'] = escale_prolongee_zone
                        df.loc[idx_dernier_vol, 'Pays_Indemnisation'] = escale_prolongee_pays
                    else:
                        # Cas 2.3: Dernière nuitée hors Europe
                        df.loc[idx_dernier_vol, 'Indemnite_Jour'] = valeur_nuit
                        df.loc[idx_dernier_vol, 'Zone'] = zone_nuit
                        df.loc[idx_dernier_vol, 'Pays_Indemnisation'] = pays
                # Sinon, trouver le dernier jour avec vol avant le dernier jour
                else:
                    # Trouver le dernier jour avant le dernier avec un vol
                    jours_precedents = [d for d in jours[:-1] if d < jours[-1]]  # Tous les jours sauf le dernier
                    dernier_jour_avec_vol = None
                    ades_nuit = None

                    for d in reversed(jours_precedents):
                        vols = df_rot[(df_rot['Date_obj'] == d) & (~df_rot['JourSansVol'])]
                        if not vols.empty:
                            dernier_jour_avec_vol = d
                            ades_nuit = vols.iloc[-1]['ADES']
                            break

                    if ades_nuit is not None:
                        prefix_nuit = ades_nuit[:2]
                        zone_nuit = icao_to_zone.get(prefix_nuit, '')
                        valeur_nuit = get_price_for_date(prefix_nuit, dernier_jour_avec_vol)
                        pays = oaci_country.get(prefix_nuit, '')

                        if zone_nuit == 'Europe' and not escales_prolongees:
                            # Cas 2.1: Dernière nuitée en Europe sans escale prolongée
                            df.loc[idx_dernier_vol, 'Indemnite_Jour'] = 0.5 * valeur_nuit
                            df.loc[idx_dernier_vol, 'Zone'] = zone_nuit
                            df.loc[idx_dernier_vol, 'Pays_Indemnisation'] = pays
                        elif zone_nuit == 'Europe' and escales_prolongees:
                            # Cas 2.2: Dernière nuitée en Europe avec escale prolongée
                            df.loc[idx_dernier_vol, 'Indemnite_Jour'] = escale_prolongee_valeur
                            df.loc[idx_dernier_vol, 'Zone'] = escale_prolongee_zone
                            df.loc[idx_dernier_vol, 'Pays_Indemnisation'] = escale_prolongee_pays
                        else:
                            # Cas 2.3: Dernière nuitée hors Europe
                            df.loc[idx_dernier_vol, 'Indemnite_Jour'] = valeur_nuit
                            df.loc[idx_dernier_vol, 'Zone'] = zone_nuit
                            df.loc[idx_dernier_vol, 'Pays_Indemnisation'] = pays
                    else:
                        # Cas improbable - traiter comme une rotation d'un jour
                        if not escales_prolongees:
                            df.loc[idx_dernier_vol, 'Indemnite_Jour'] = 0.5 * valeur_jour
                            df.loc[idx_dernier_vol, 'Zone'] = zone_jour
                            df.loc[idx_dernier_vol, 'Pays_Indemnisation'] = oaci_country.get(prefix_jour, '')
                        else:
                            df.loc[idx_dernier_vol, 'Indemnite_Jour'] = escale_prolongee_valeur
                            df.loc[idx_dernier_vol, 'Zone'] = escale_prolongee_zone
                            df.loc[idx_dernier_vol, 'Pays_Indemnisation'] = escale_prolongee_pays

    df = df.sort_values(by=['Rotation_ID', 'Date_obj', 'OFF'], na_position='first').reset_index(drop=True)

    # Diagnostic global : vérifier toutes les lignes qui ont des problèmes d'indemnité
    for idx in df.index:
        # D'abord vérifier si ADEP ou ADES contiennent des codes IATA non convertis (3 caractères au lieu de 4)
        diagnostic_msgs = []

        if 'ADEP' in df.columns and pd.notna(df.loc[idx, 'ADEP']):
            adep = str(df.loc[idx, 'ADEP']).strip()
            if len(adep) == 3:
                diagnostic_msgs.append(f"❌ Code IATA non converti en ICAO: ADEP '{adep}' - Aéroport manquant dans la base de données")

        if 'ADES' in df.columns and pd.notna(df.loc[idx, 'ADES']):
            ades = str(df.loc[idx, 'ADES']).strip()
            if len(ades) == 3:
                diagnostic_msgs.append(f"❌ Code IATA non converti en ICAO: ADES '{ades}' - Aéroport manquant dans la base de données")

        # Si on a trouvé des codes IATA non convertis, les signaler immédiatement
        if diagnostic_msgs:
            if pd.isna(df.loc[idx, 'Diagnostic']) or df.loc[idx, 'Diagnostic'] is None or df.loc[idx, 'Diagnostic'] == '':
                df.loc[idx, 'Diagnostic'] = ' | '.join(diagnostic_msgs)
            else:
                # Ajouter aux diagnostics existants
                df.loc[idx, 'Diagnostic'] = df.loc[idx, 'Diagnostic'] + ' | ' + ' | '.join(diagnostic_msgs)
            continue  # Passer à la ligne suivante, ce problème est prioritaire

        if pd.notna(df.loc[idx, 'Indemnite_Jour']) and df.loc[idx, 'Indemnite_Jour'] != 0:
            # Il y a une indemnité, vérifions si tout est OK
            if pd.isna(df.loc[idx, 'Diagnostic']) or df.loc[idx, 'Diagnostic'] is None:
                pays = df.loc[idx, 'Pays_Indemnisation']
                zone = df.loc[idx, 'Zone']

                # Identifier l'aéroport concerné
                if 'ADES' in df.columns and pd.notna(df.loc[idx, 'ADES']):
                    aeroport = df.loc[idx, 'ADES']
                    prefix = aeroport[:2] if len(str(aeroport)) >= 2 else ''

                    diagnostic_msgs = []
                    if not pays or pays == '' or pd.isna(pays):
                        diagnostic_msgs.append(f"⚠️ Préfixe ICAO '{prefix}' (de {aeroport}) introuvable dans la base pays")
                    if not zone or zone == '' or pd.isna(zone):
                        diagnostic_msgs.append(f"⚠️ Zone non définie pour '{prefix}'")

                    if diagnostic_msgs:
                        df.loc[idx, 'Diagnostic'] = ' | '.join(diagnostic_msgs)

        # Cas spécial : indemnité à 0 mais devrait avoir une valeur
        elif pd.notna(df.loc[idx, 'Indemnite_Jour']) and df.loc[idx, 'Indemnite_Jour'] == 0:
            if pd.isna(df.loc[idx, 'Diagnostic']) or df.loc[idx, 'Diagnostic'] is None:
                pays = df.loc[idx, 'Pays_Indemnisation']
                if pays and pays != '' and not pd.isna(pays):
                    if 'ADES' in df.columns and pd.notna(df.loc[idx, 'ADES']):
                        aeroport = df.loc[idx, 'ADES']
                        prefix = aeroport[:2] if len(str(aeroport)) >= 2 else ''
                        df.loc[idx, 'Diagnostic'] = f"⚠️ Aucun prix défini pour {pays} ({prefix}) pour cette année"

    return df
