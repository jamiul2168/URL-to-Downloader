
import os
import re
import uuid
import shutil
from flask import Flask, request, render_template, jsonify, send_file, abort
from werkzeug.utils import secure_filename
import yt_dlp

# --- Config ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Limit single file size you want to keep (in bytes). Large files can still be streamed to users.
MAX_KEEP_BYTES = 2 * 1024 * 1024 * 1024  # 2 GB

app = Flask(__name__)

# Utility to produce a safe filename
def slugify(text):
    text = re.sub(r"[^\w\-\. ]+", "", text).strip().replace(" ", "_")
    return secure_filename(text) or f"file_{uuid.uuid4().hex}"

def build_ydl_opts(fmt_choice, base_out):
    opts = {
        "outtmpl": os.path.join(DOWNLOAD_DIR, base_out + ".%(ext)s"),
        "restrictfilenames": True,
        "noprogress": True,
        "nocheckcertificate": True,
        "quiet": True,
        "merge_output_format": "mp4",
    }
    if fmt_choice == "audio":
        opts.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]
        })
    else:
        # best video+audio
        opts.update({"format": "bv*+ba/b"})
    return opts

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/api/download", methods=["POST"])
def api_download():
    data = request.get_json(silent=True) or request.form
    url = (data.get("url") or "").strip()
    mode = (data.get("mode") or "video").strip().lower()  # "video" or "audio"

    if not url:
        return jsonify({"ok": False, "error": "No URL provided."}), 400

    # base name (safe)
    base_name = slugify(data.get("filename") or "downloaded_media")
    ydl_opts = build_ydl_opts(mode, base_name)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            # Build expected output path
            if "requested_downloads" in info and info["requested_downloads"]:
                # For some sites, yt-dlp returns list entries
                filepath = info["requested_downloads"][0].get("filepath")
            else:
                filepath = ydl.prepare_filename(info)

        if not filepath or not os.path.exists(filepath):
            # Some postprocessors change extension; try to guess
            candidates = list(filter(os.path.exists, [
                filepath or "",
                os.path.join(DOWNLOAD_DIR, base_name + ".mp3"),
                os.path.join(DOWNLOAD_DIR, base_name + ".m4a"),
                os.path.join(DOWNLOAD_DIR, base_name + ".mp4"),
                os.path.join(DOWNLOAD_DIR, base_name + ".webm"),
                os.path.join(DOWNLOAD_DIR, base_name + ".mkv"),
            ]))
            if candidates:
                filepath = candidates[0]

        if not filepath or not os.path.exists(filepath):
            return jsonify({"ok": False, "error": "Download finished but file not found."}), 500

        file_id = uuid.uuid4().hex
        final_name = os.path.basename(filepath)
        size_bytes = os.path.getsize(filepath)

        # Optionally cleanup older files to save space
        try:
            for f in os.listdir(DOWNLOAD_DIR):
                p = os.path.join(DOWNLOAD_DIR, f)
                if os.path.isfile(p) and (os.path.getsize(p) > MAX_KEEP_BYTES):
                    os.remove(p)
        except Exception:
            pass

        return jsonify({
            "ok": True,
            "file": final_name,
            "size": size_bytes,
            "download_url": f"/file/{final_name}"
        }), 200

    except yt_dlp.utils.DownloadError as e:
        return jsonify({"ok": False, "error": f"Download error: {e}" }), 500
    except Exception as e:
        return jsonify({"ok": False, "error": f"Unexpected error: {str(e)}"}), 500

@app.route("/file/<path:filename>", methods=["GET"])
def serve_file(filename):
    safe_path = os.path.join(DOWNLOAD_DIR, os.path.basename(filename))
    if not os.path.exists(safe_path):
        abort(404)
    # Serve as attachment (download)
    return send_file(safe_path, as_attachment=True, download_name=os.path.basename(safe_path))

if __name__ == "__main__":
    # For local run; Render will use gunicorn via Procfile
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 7860)))
