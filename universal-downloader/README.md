# Universal Downloader (Flask + yt-dlp)

## Local
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
python app.py
# open http://127.0.0.1:7860

## Render Deploy
- Build Command: pip install -r requirements.txt
- Start Command: gunicorn app:app
