"""
This script runs the application using a development server.
It contains the definition of routes and views for the application.
"""

from flask import Flask, render_template, request, jsonify
import pandas as pd
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# Make the WSGI interface available at the top level so wfastcgi can get it.
wsgi_app = app.wsgi_app


@app.route('/')
def index():
    """Renders a sample page."""
    return render_template('index.html')


@app.route('/upload_excel', methods=['POST'])
def upload_excel():
    global df_excel
    if 'excel_file' not in request.files:
        return jsonify(success=False, message='Aucun fichier recu.')
    
    file = request.files['excel_file']
    if file.filename == '':
        return jsonify(success=False, message='Nom de fichier vide.')

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    print(filepath)
    file.save(filepath)

    try:
        df_excel = pd.read_excel(filepath)
        df_excel = df_excel.dropna(subset=['ADEP', 'ADES'])
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, message=str(e))

if __name__ == '__main__':
    import os
    HOST = os.environ.get('SERVER_HOST', 'localhost')
    try:
        PORT = int(os.environ.get('SERVER_PORT', '5555'))
    except ValueError:
        PORT = 5555
    app.run(HOST, PORT)

