#!/usr/bin/env python3
from flask import Flask, jsonify, request, send_file, send_from_directory
from werkzeug.utils import secure_filename
import os
import mimetypes
from datetime import datetime
import stat

app = Flask(__name__)

# Configurazione
BASE_DIR = "/home/mottu/file"
UPLOAD_FOLDER = BASE_DIR
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Assicurati che la directory esista
os.makedirs(BASE_DIR, exist_ok=True)

def get_file_info(filepath):
    """Ottieni informazioni dettagliate su un file o directory"""
    try:
        stat_result = os.stat(filepath)
        return {
            'name': os.path.basename(filepath),
            'path': filepath,
            'is_directory': os.path.isdir(filepath),
            'size': stat_result.st_size if not os.path.isdir(filepath) else 0,
            'modified': datetime.fromtimestamp(stat_result.st_mtime).isoformat(),
            'permissions': oct(stat_result.st_mode)[-3:]
        }
    except Exception as e:
        return None

@app.route('/')
def index():
    """Homepage con informazioni API"""
    return jsonify({
        'message': 'File Server API',
        'version': '1.0',
        'endpoints': {
            'GET /files': 'Lista file e cartelle',
            'GET /files/<path>': 'Lista contenuto di una cartella specifica',
            'GET /download/<path>': 'Scarica un file',
            'POST /upload': 'Carica un file',
            'POST /mkdir': 'Crea una cartella'
        }
    })

@app.route('/files', methods=['GET'])
@app.route('/files/<path:subpath>', methods=['GET'])
def list_files(subpath=''):
    """Lista file e cartelle in una directory"""
    try:
        target_path = os.path.join(BASE_DIR, subpath) if subpath else BASE_DIR
        
        # Verifica che il path sia all'interno della directory base
        if not os.path.abspath(target_path).startswith(os.path.abspath(BASE_DIR)):
            return jsonify({'error': 'Accesso negato'}), 403
            
        if not os.path.exists(target_path):
            return jsonify({'error': 'Directory non trovata'}), 404
            
        if not os.path.isdir(target_path):
            return jsonify({'error': 'Il path non è una directory'}), 400
        
        items = []
        for item in os.listdir(target_path):
            item_path = os.path.join(target_path, item)
            file_info = get_file_info(item_path)
            if file_info:
                # Aggiungi il path relativo per l'API
                relative_path = os.path.relpath(item_path, BASE_DIR)
                file_info['relative_path'] = relative_path
                items.append(file_info)
        
        # Ordina: prima le directory, poi i file
        items.sort(key=lambda x: (not x['is_directory'], x['name'].lower()))
        
        return jsonify({
            'current_path': subpath,
            'items': items,
            'total': len(items)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<path:filepath>', methods=['GET'])
def download_file(filepath):
    """Scarica un file"""
    try:
        full_path = os.path.join(BASE_DIR, filepath)
        
        # Verifica sicurezza del path
        if not os.path.abspath(full_path).startswith(os.path.abspath(BASE_DIR)):
            return jsonify({'error': 'Accesso negato'}), 403
            
        if not os.path.exists(full_path):
            return jsonify({'error': 'File non trovato'}), 404
            
        if os.path.isdir(full_path):
            return jsonify({'error': 'Impossibile scaricare una directory'}), 400
        
        return send_file(full_path, as_attachment=True)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    """Carica un file"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Nessun file selezionato'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Nessun file selezionato'}), 400
        
        # Path di destinazione (opzionale)
        target_dir = request.form.get('path', '')
        
        if file:
            filename = secure_filename(file.filename)
            if not filename:
                return jsonify({'error': 'Nome file non valido'}), 400
            
            # Crea il path completo
            upload_path = os.path.join(BASE_DIR, target_dir) if target_dir else BASE_DIR
            
            # Verifica sicurezza del path
            if not os.path.abspath(upload_path).startswith(os.path.abspath(BASE_DIR)):
                return jsonify({'error': 'Accesso negato'}), 403
            
            # Crea la directory se non esiste
            os.makedirs(upload_path, exist_ok=True)
            
            file_path = os.path.join(upload_path, filename)
            file.save(file_path)
            
            file_info = get_file_info(file_path)
            return jsonify({
                'message': 'File caricato con successo',
                'file_info': file_info
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/mkdir', methods=['POST'])
def create_directory():
    """Crea una nuova directory"""
    try:
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({'error': 'Nome directory richiesto'}), 400
        
        dir_name = secure_filename(data['name'])
        parent_path = data.get('path', '')
        
        if not dir_name:
            return jsonify({'error': 'Nome directory non valido'}), 400
        
        # Crea il path completo
        base_path = os.path.join(BASE_DIR, parent_path) if parent_path else BASE_DIR
        new_dir_path = os.path.join(base_path, dir_name)
        
        # Verifica sicurezza del path
        if not os.path.abspath(new_dir_path).startswith(os.path.abspath(BASE_DIR)):
            return jsonify({'error': 'Accesso negato'}), 403
        
        if os.path.exists(new_dir_path):
            return jsonify({'error': 'Directory già esistente'}), 400
        
        os.makedirs(new_dir_path)
        
        dir_info = get_file_info(new_dir_path)
        return jsonify({
            'message': 'Directory creata con successo',
            'directory_info': dir_info
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/delete/<path:filepath>', methods=['DELETE'])
def delete_item(filepath):
    """Elimina un file o directory"""
    try:
        full_path = os.path.join(BASE_DIR, filepath)
        
        # Verifica sicurezza del path
        if not os.path.abspath(full_path).startswith(os.path.abspath(BASE_DIR)):
            return jsonify({'error': 'Accesso negato'}), 403
            
        if not os.path.exists(full_path):
            return jsonify({'error': 'File o directory non trovata'}), 404
        
        if os.path.isdir(full_path):
            import shutil
            shutil.rmtree(full_path)
        else:
            os.remove(full_path)
        
        return jsonify({'message': 'Eliminato con successo'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File troppo grande (max 16MB)'}), 413

if __name__ == '__main__':
    print(f"Server avviato. Directory base: {BASE_DIR}")
    print("Endpoints disponibili:")
    print("  GET  /files - Lista file")
    print("  GET  /download/<path> - Scarica file")
    print("  POST /upload - Carica file")
    print("  POST /mkdir - Crea directory")
    print("  DELETE /delete/<path> - Elimina file/directory")
    
    # Avvia il server su tutte le interfacce per permettere connessioni esterne
    app.run(host='0.0.0.0', port=5000, debug=True)