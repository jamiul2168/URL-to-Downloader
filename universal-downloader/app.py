from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import os

# --- Flask Setup ---
app = Flask(__name__)
CORS(app)  # ✅ Allow all frontend origins (Vercel etc.)

DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)


@app.route('/')
def home():
    """Basic health check route"""
    return jsonify({
        "message": "Universal Downloader API (Public Mode).",
        "status": "ok"
    })


@app.route('/api/download', methods=['POST'])
def download_video():
    """Main downloader API endpoint"""
    try:
        data = request.get_json()
        url = data.get("url")
        mode = data.get("mode", "video")
        filename = data.get("filename", "media")

        if not url:
            return jsonify({"ok": False, "error": "No URL provided."}), 400

        output_path = os.path.join(DOWNLOAD_FOLDER, f"{filename}.%(ext)s")

        # --- yt-dlp options ---
        ydl_opts = {
            "outtmpl": output_path,
            "quiet": True,
            "format": "bestvideo+bestaudio/best"
        }

        if mode == "audio":
            ydl_opts.update({
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }]
            })

        # --- Download process ---
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            real_file = ydl.prepare_filename(info)

        # --- For audio mode, convert to .mp3 ---
        if mode == "audio" and not real_file.endswith(".mp3"):
            base = os.path.splitext(real_file)[0]
            real_file = f"{base}.mp3"

        return jsonify({
            "ok": True,
            "file": os.path.basename(real_file),
            "title": info.get("title", "Unknown Title")
        })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/file/<path:filename>')
def serve_file(filename):
    """Serve downloaded file"""
    file_path = os.path.join(DOWNLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return jsonify({"ok": False, "error": "File not found"}), 404


if __name__ == '__main__':
    # Render automatically sets PORT env var
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
