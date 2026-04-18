from flask import Flask, request, jsonify, send_file
import os
import tempfile
import time
import requests

app = Flask(__name__)

# Configuración de directorios temporales
TEMP_DIR = tempfile.gettempdir()
DOWNLOAD_DIR = os.path.join(TEMP_DIR, 'luckxit_tiktok')
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

TIKWM_API = "https://www.tikwm.com/api/"

def get_tiktok_info(url):
    try:
        response = requests.post(TIKWM_API, data={'url': url, 'hd': 1}, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 0:
                return data.get('data')
        return None
    except Exception as e:
        print(f"Error en TIKWM API: {e}")
        return None

# AQUÍ ESTÁ LA MAGIA: Aceptamos GET (para el DownloadManager) y POST
@app.route('/download', methods=['GET', 'POST'])
def download():
    try:
        # Detectamos cómo nos está hablando la app y extraemos los datos correctamente
        if request.method == 'POST':
            url = request.form.get('url', '').strip()
            kind = request.form.get('kind', 'video')
        else:
            url = request.args.get('url', '').strip()
            kind = request.args.get('kind', 'video')

        if not url or 'tiktok' not in url.lower():
            return jsonify({'error': 'Solo se admiten enlaces de TikTok.'}), 400

        timestamp = int(time.time() * 1000)
        
        tiktok_data = get_tiktok_info(url)
        if not tiktok_data:
            return jsonify({'error': 'No se pudo obtener información del video.'}), 500

        if kind == 'video':
            media_url = tiktok_data.get('hdplay') or tiktok_data.get('play')
            ext = 'mp4'
            mimetype = 'video/mp4'
        elif kind == 'audio':
            media_url = tiktok_data.get('music_info', {}).get('play')
            ext = 'mp3'
            mimetype = 'audio/mpeg'
        else:
            return jsonify({'error': 'Tipo de descarga inválido.'}), 400

        if not media_url:
            return jsonify({'error': 'El archivo multimedia no está disponible.'}), 404

        file_name = f'LuckXit_TikTok_{timestamp}.{ext}'
        file_path = os.path.join(DOWNLOAD_DIR, file_name)

        media_response = requests.get(media_url, timeout=60, stream=True)
        if media_response.status_code == 200:
            with open(file_path, 'wb') as f:
                for chunk in media_response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return send_file(file_path, mimetype=mimetype, as_attachment=True, download_name=file_name)
        else:
            return jsonify({'error': 'Error al descargar desde el servidor original.'}), 500

    except Exception as e:
        return jsonify({'error': f'Fallo interno: {str(e)}'}), 500

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'message': 'LUCK XIT Engine Running'})

def cleanup_temp_files():
    try:
        for file in os.listdir(DOWNLOAD_DIR):
            file_path = os.path.join(DOWNLOAD_DIR, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
    except Exception as e:
        pass

if __name__ == '__main__':
    cleanup_temp_files()
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
