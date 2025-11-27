# Crew Taxation Web

Application web Flask pour le calcul automatique des indemnités d'équipage basé sur les journaux de vol.

## 📋 Description

Cette application permet de :
- 📁 Uploader des fichiers de journaux de vol (Excel .xlsx/.xls ou CSV)
- 🔄 Identifier automatiquement les rotations
- 💰 Calculer les indemnités selon les règles métier définies
- 📊 Afficher des résultats détaillés (résumé + détails par rotation)
- 📤 Exporter les résultats en Excel
- ⚙️ Gérer les prix par pays et par année
- 🔍 Filtrer les rotations selon plusieurs critères

## 🚀 Installation

### Prérequis

- Python 3.8 ou supérieur
- pip

### Installation des dépendances

```bash
pip install -r requirements.txt
```

### Initialisation de la base de données

```bash
python database.py
```

Cette commande va :
- Créer la base de données SQLite `crew_taxation.db`
- Importer les 8336 aéroports depuis `doc/airports.csv`
- Importer les 42 pays avec leurs prix depuis `doc/Country-OACI-Code.xlsx`
- Configurer les bases par défaut

## 💻 Utilisation

### Démarrage de l'application

```bash
python app.py
```

L'application sera accessible à l'adresse : **http://localhost:5555**

### Workflow d'utilisation

1. **Upload du fichier journal de vol**
   - Formats supportés : `.xlsx`, `.xls`, `.csv`
   - Formats détectés automatiquement :
     - Format standard : colonnes `Date`, `ADEP`, `ADES`, `OFF`, `ON`
     - Format LogBook : colonnes `flightDate`, `from`, `to`, `takeoffTime`, `landingTime`

2. **Sélection de l'année** (optionnel)
   - Choisir l'année des prix à utiliser pour le calcul

3. **Traitement**
   - Cliquer sur "Traiter le fichier"
   - Les rotations sont identifiées automatiquement
   - Les indemnités sont calculées selon les règles métier

4. **Consultation des résultats**
   - Onglet **Résumé** : statistiques globales et détails par pays
   - Onglet **Détails des rotations** : arborescence cliquable de chaque rotation

5. **Filtrage** (optionnel)
   - Filtrer par ID de rotation, dates, base, montant minimum

6. **Export**
   - Télécharger les résultats en Excel (4 feuilles : Détails, Résumé Rotation, Résumé Pays, Statistiques)

## ⚙️ Gestion des prix

Dans l'onglet **Configuration** → **Gérer les prix par pays** :

- **Consulter** les prix par pays et par année
- **Modifier** les prix individuellement
- **Dupliquer** les prix d'une année vers une autre
- **Importer** des prix depuis un fichier Excel (colonnes : `icao_prefix`, `price`)
- **Exporter** les prix vers Excel

## 📂 Structure du projet

```
Crew_taxation_web/
├── app.py                      # Backend Flask (routes API)
├── database.py                 # Gestion de la base SQLite
├── crew_taxation_logic.py      # Logique métier (calculs)
├── requirements.txt            # Dépendances Python
├── crew_taxation.db           # Base de données SQLite (auto-créée)
├── doc/
│   ├── airports.csv           # Liste des aéroports (IATA/OACI)
│   └── Country-OACI-Code.xlsx # Pays, zones et prix
├── templates/
│   └── index.html             # Interface web
├── static/
│   ├── script.js              # Frontend JavaScript
│   └── style.css              # Styles CSS
└── uploads/                   # Fichiers uploadés (auto-créé)
```

## 🔧 Fonctionnalités principales

### Détection automatique du format
L'application détecte automatiquement le format du fichier :
- Format standard avec colonnes `Date`, `ADEP`, `ADES`
- Format LogBook avec colonnes `flightDate`, `from`, `to`

### Calcul des indemnités
Règles métier implémentées :
- Identification des rotations (départ et retour à une base)
- Gestion des bases spéciales (LFLY, LSGG) avec rotations sur 2 jours
- Calcul par jour/nuitée selon le pays
- Escales prolongées (>7h hors Zone Euro)
- Règles spécifiques pour le dernier jour de rotation

### Gestion multi-années
- Historique des prix par année
- Duplication des prix d'une année à l'autre
- Sélection de l'année lors du traitement

### Filtres avancés
- Par ID de rotation
- Par période (date début/fin)
- Par base
- Par montant minimum

## 🗄️ Base de données

**SQLite** avec 4 tables :
- `airports` : 8336 aéroports avec codes IATA/ICAO
- `countries` : 42 pays avec préfixes OACI et zones
- `prices_history` : Historique des prix par pays/année
- `config` : Configuration (bases)

## 📝 Configuration

### Bases par défaut
Les bases par défaut sont : `LFLB`, `LFLS`, `LFLY`, `LSGG`, `LFLP`

Vous pouvez les modifier dans l'onglet **Configuration**.

### Ajout de nouvelles bases
1. Aller dans **Configuration**
2. Cliquer sur "Ajouter base"
3. Entrer le code OACI (4 lettres)

## 🐛 Dépannage

### La base de données n'existe pas
Exécutez `python database.py` pour l'initialiser.

### Erreur "File is not a zip file"
Assurez-vous que votre fichier Excel est au format `.xlsx` ou `.xls`. Si c'est un fichier CSV, utilisez l'extension `.csv`.

### Les codes IATA ne sont pas reconnus
Vérifiez que le fichier `doc/airports.csv` est présent et contient les codes IATA de vos aéroports.

## 📄 Licence

Projet personnel - Tous droits réservés

## 👤 Auteur

MARET Remy

## 🔗 Technologies utilisées

- **Backend** : Flask, Pandas, SQLite
- **Frontend** : HTML5, CSS3, JavaScript (Vanilla)
- **Base de données** : SQLite
