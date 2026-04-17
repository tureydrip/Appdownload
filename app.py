from flask import Flask, request, jsonify, send_file
import yt_dlp
import os
import tempfile
import time
import requests

app = Flask(__name__)
TEMP_DIR = tempfile.gettempdir()
DOWNLOAD_DIR = os.path.join(TEMP_DIR, 'luckxit_api')
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

TIKWM_API = "https://www.tikwm.com/api/"

@app.route('/api/download', methods=['GET'])
def api_download():
    url = request.args.get('url', '').strip()
    kind = request.args.get('kind', 'audio') 

    if not url:
        return "Falta la URL", 400

    timestamp = int(time.time() * 1000)

    try:
        # --- LÓGICA TIKTOK ---
        if 'tiktok.com' in url.lower():
            res = requests.post(TIKWM_API, data={'url': url, 'hd': 1}, timeout=30)
            if res.status_code == 200:
                data = res.json().get('data', {})
                video_url = data.get('hdplay') or data.get('play')
                if video_url:
                    video_path = os.path.join(DOWNLOAD_DIR, f'tiktok_{timestamp}.mp4')
                    vid_res = requests.get(video_url, stream=True)
                    with open(video_path, 'wb') as f:
                        for chunk in vid_res.iter_content(chunk_size=8192): f.write(chunk)
                    return send_file(video_path, as_attachment=True, download_name=f'tiktok_{timestamp}.mp4')

        # --- LÓGICA YOUTUBE (Videos, Shorts y Audio) ---
        if 'youtube.com' in url.lower() or 'youtu.be' in url.lower():
            ext = 'mp3' if kind == 'audio' else 'mp4'
            output_template = os.path.join(DOWNLOAD_DIR, f'yt_{timestamp}.%(ext)s')
            
            ydl_opts = {
                'outtmpl': output_template,
                'quiet': True,
                'no_warnings': True,
                'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None
            }

            if kind == 'audio':
                ydl_opts['format'] = 'm4a/bestaudio/ext:m4a/ba/best'
                ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]
            else:
                # Formato optimizado para Shorts y Videos MP4
                ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                
            # Buscar el archivo generado
            for file in os.listdir(DOWNLOAD_DIR):
                if file.startswith(f'yt_{timestamp}') and file.endswith(f'.{ext}'):
                    return send_file(os.path.join(DOWNLOAD_DIR, file), as_attachment=True, download_name=f'luckxit_{timestamp}.{ext}')

        return "No se pudo procesar el enlace", 500

    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
