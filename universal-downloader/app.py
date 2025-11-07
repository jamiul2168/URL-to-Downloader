import os, re, uuid
from flask import Flask, request, render_template, jsonify, send_file, abort
from werkzeug.utils import secure_filename
import yt_dlp

# === ফোল্ডার সেটআপ ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# === Flask App তৈরি ===
app = Flask(__name__)

# === Helper Function ===
def slugify(text: str) -> str:
    text = re.sub(r"[^\w\-. ]+", "", (text or "")).strip().replace(" ", "_")
    return secure_filename(text) or f"file_{uuid.uuid4().hex}"

# === yt-dlp অপশন ===
def ydl_opts(mode: str, base_out: str) -> dict:
    opts = {
        "outtmpl": os.path.join(DOWNLOAD_DIR, base_out + ".%(ext)s"),
        "restrictfilenames": True,
        "nocheckcertificate": True,
        "noprogress": True,
        "quiet": True,
        "merge_output_format": "mp4",
    }

    # ✅ Render Environment Variable থেকে cookies তৈরি
    cookie_data = os.environ.get("COOKIE_TEXT", "")
    if cookie_data:
        with open(os.path.join(BASE_DIR, "cookies.txt"), "w", encoding="utf-8") as f:
            f.write(cookie_data)
        opts["cookiefile"] = os.path.join(BASE_DIR, "cookies.txt")

    # === Audio বা Video সেটিং ===
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

# === হোমপেজ ===
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

# === ডাউনলোড API ===
@app.route("/api/download", methods=["POST"])
def api_download():
    data = request.get_json(silent=True) or request.form
    url = (data.get("url") or "").strip()
    mode = (data.get("mode") or "video").strip().lower()
    filename = slugify(data.get("filename") or "downloaded_media")

    if not url:
        return jsonify({"ok": False, "error": "No URL provided."}), 400

    try:
        opts = ydl_opts(mode, filename)
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)

            filepath = None
            if isinstance(info, dict):
                if info.get("requested_downloads"):
                    filepath = info["requested_downloads"][0].get("filepath")
                if not filepath:
                    filepath = ydl.prepare_filename(info)

        # === ফাইনাল ফাইল খোঁজা ===
        final = None
        for ext in [".mp3", ".m4a", ".mp4", ".webm", ".mkv"]:
            path = os.path.join(DOWNLOAD_DIR, filename + ext)
            if os.path.exists(path):
                final = path
                break

        if not final:
            return jsonify({"ok": False, "error": "File not found after download."}), 500

        size = os.path.getsize(final)
        return jsonify({
            "ok": True,
            "file": os.path.basename(final),
            "size": size,
            "download_url": f"/file/{os.path.basename(final)}"
        })

    except yt_dlp.utils.DownloadError as e:
        return jsonify({"ok": False, "error": f"Download error: {e}"}), 500
    except Exception as e:
        return jsonify({"ok": False, "error": f"Unexpected error: {e}"}), 500

# === ফাইল সার্ভ করা ===
@app.route("/file/<path:filename>", methods=["GET"])
def serve_file(filename):
    path = os.path.join(DOWNLOAD_DIR, os.path.basename(filename))
    if not os.path.exists(path):
        abort(404)
    return send_file(path, as_attachment=True, download_name=os.path.basename(path))

# === Flask রান করা ===
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 7860)))
