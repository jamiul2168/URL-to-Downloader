
# Universal Downloader (yt-dlp + Flask)

A simple permanent web app to download from YouTube, Facebook, Google Drive, and direct links using **yt-dlp**.

## ✨ Features
- Video or Audio (MP3) download
- Clean UI inspired by your Colab widget
- Works on Render / Railway / VPS / local
- Direct download endpoint `/file/<filename>`

## 🗂 Project Structure
```
.
├── app.py
├── requirements.txt
├── Procfile
├── templates/
│   └── index.html
└── static/
    └── style.css
```

## 🚀 Local Run
```bash
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
# Open http://127.0.0.1:7860
```

## ☁️ Deploy on Render (Recommended)
1. Push this repo to GitHub
2. Create a new **Web Service** on [https://render.com](https://render.com)
3. **Build Command**: `pip install -r requirements.txt`
4. **Start Command**: `gunicorn app:app`
5. Done ✅ (Add a custom domain via Cloudflare if you like)

## 🧩 Notes
- Large files will be served directly via `/file/<filename>`
- yt-dlp handles YouTube/Facebook/Drive extractors automatically
- For long downloads, keep the service plan/runtime limits in mind
