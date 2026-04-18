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

# API maestra para extraer datos de TikTok
TIKWM_API = "https://www.tikwm.com/api/"

def get_tiktok_info(url):
    try:
        # Petición a la API externa para romper la marca de agua
        response = requests.post(TIKWM_API, data={'url': url, 'hd': 1}, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 0:
                return data.get('data')
        return None
    except Exception as e:
        print(f"Error en TIKWM API: {e}")
        return None

@app.route('/download', methods=['POST'])
def download():
    try:
        url = request.form.get('url', '').strip()
        kind = request.form.get('kind', 'video')

        if not url or 'tiktok' not in url.lower():
            return jsonify({'error': 'Solo se admiten enlaces de TikTok.'}), 400

        timestamp = int(time.time() * 1000)
        
        # 1. Extraer la información
        tiktok_data = get_tiktok_info(url)
        if not tiktok_data:
            return jsonify({'error': 'No se pudo obtener información del video. Verifica el enlace.'}), 500

        # 2. Determinar si es Video o Audio
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

        # 3. Descargar temporalmente a Railway
        file_name = f'luck_xit_tiktok_{timestamp}.{ext}'
        file_path = os.path.join(DOWNLOAD_DIR, file_name)

        media_response = requests.get(media_url, timeout=60, stream=True)
        if media_response.status_code == 200:
            with open(file_path, 'wb') as f:
                for chunk in media_response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # 4. Enviar el archivo a la APK
            return send_file(file_path, mimetype=mimetype, as_attachment=True, download_name=file_name)
        else:
            return jsonify({'error': 'Error de origen al descargar el archivo.'}), 500

    except Exception as e:
        return jsonify({'error': f'Fallo interno: {str(e)}'}), 500

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'message': 'LUCK XIT TikTok Engine Running'})

def cleanup_temp_files():
    # Limpia la basura residual en el servidor cada vez que se reinicia
    try:
        for file in os.listdir(DOWNLOAD_DIR):
            file_path = os.path.join(DOWNLOAD_DIR, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
    except Exception as e:
        print(f"Error limpiando archivos: {e}")

if __name__ == '__main__':
    cleanup_temp_files()
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
