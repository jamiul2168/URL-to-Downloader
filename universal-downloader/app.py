import os, re, uuid
from flask import Flask, request, jsonify, send_file, abort
from werkzeug.utils import secure_filename
import yt_dlp

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

app = Flask(__name__)

def slugify(text: str) -> str:
    text = re.sub(r"[^\w\-. ]+", "", (text or "")).strip().replace(" ", "_")
    return secure_filename(text) or f"file_{uuid.uuid4().hex}"

def make_opts(mode: str, base_out: str):
    opts = {
        "outtmpl": os.path.join(DOWNLOAD_DIR, base_out + ".%(ext)s"),
        "restrictfilenames": True,
        "nocheckcertificate": True,
        "noprogress": True,
        "quiet": True,
        "merge_output_format": "mp4",
    }
    if mode == "audio":
        opts.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]
        })
    else:
        opts.update({"format": "bv*+ba/b"})
    return opts

@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "status": "ok",
        "message": "Universal Downloader API (Public Mode)."
    })

@app.route("/api/download", methods=["POST"])
def download_api():
    data = request.get_json(silent=True) or request.form
    url = (data.get("url") or "").strip()
    filename = slugify(data.get("filename") or "downloaded_media")
    mode = (data.get("mode") or "video").strip().lower()

    if not url:
        return jsonify({"ok": False, "error": "Please provide a valid URL."}), 400

    try:
        opts = make_opts(mode, filename)
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.extract_info(url, download=True)
        for ext in [".mp3", ".m4a", ".mp4", ".webm", ".mkv"]:
            path = os.path.join(DOWNLOAD_DIR, filename + ext)
            if os.path.exists(path):
                size = os.path.getsize(path)
                return jsonify({
                    "ok": True,
                    "file": os.path.basename(path),
                    "size": size,
                    "download_url": f"/file/{os.path.basename(path)}"
                })
        return jsonify({"ok": False, "error": "File not found after download."}), 500

    except yt_dlp.utils.DownloadError as e:
        if "Sign in" in str(e) or "login" in str(e):
            return jsonify({"ok": False, "error": "This video requires login or cookies (Private/Age Restricted)."}), 403
        return jsonify({"ok": False, "error": f"Download failed: {e}"}), 500
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/file/<path:filename>", methods=["GET"])
def serve_file(filename):
    path = os.path.join(DOWNLOAD_DIR, os.path.basename(filename))
    if not os.path.exists(path):
        abort(404)
    return send_file(path, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 7860)))



@app.route("/home", methods=["GET"])
def home():
    return render_template("index.html")

