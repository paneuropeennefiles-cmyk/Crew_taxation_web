# -*- coding: utf-8 -*-
"""
Point d'entrée principal pour l'application Crew Taxation Web
"""

import sys
import os

# Ajouter le dossier src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.app import app

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
