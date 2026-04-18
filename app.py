from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)
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
        return None

@app.route('/api/get_direct_link', methods=['GET', 'POST'])
def get_direct_link():
    # Acepta GET o POST
    url = request.form.get('url', request.args.get('url', '')).strip()
    kind = request.form.get('kind', request.args.get('kind', 'video'))

    if not url or 'tiktok' not in url.lower():
        return jsonify({'error': 'Enlace inválido o no es de TikTok.'}), 400

    tiktok_data = get_tiktok_info(url)
    if not tiktok_data:
        return jsonify({'error': 'No se pudo desencriptar el video.'}), 500

    # Extraemos la ruta directa al MP4 o MP3
    if kind == 'video':
        media_url = tiktok_data.get('hdplay') or tiktok_data.get('play')
    elif kind == 'audio':
        media_url = tiktok_data.get('music_info', {}).get('play')
    else:
        return jsonify({'error': 'Formato no soportado.'}), 400

    if not media_url:
        return jsonify({'error': 'El archivo no está disponible.'}), 404

    # Le devolvemos el link directo a la App de Android
    return jsonify({'success': True, 'direct_url': media_url})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
