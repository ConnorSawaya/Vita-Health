# Vita Health

Barcode food scanner + AI health analysis (Streamlit). Created by Connor Sawaya, shreeyuvan, James.

## What it is
Scan a product barcode (camera) or load the offline demo product, get a health score + analysis, and ask follow-ups in chat. Scan and chat history stays in the current Streamlit browser session's memory; it is not written to a shared server file and is cleared when the session ends.

## Install
```bash
pip install -r requirements.txt
cp .env.example .env   # optional, for live AI
```

## Run (one command)
```bash
streamlit run app.py
```

## Test
```bash
python -m unittest discover -s tests -v
python -m py_compile app.py ai.py
```

## Env vars
- `OPENROUTER_API_KEY` (optional). Without it the app runs in OFFLINE/MOCK mode with sample analysis. Never commit `.env`.

## Offline/demo
No key and no camera needed: press **Load demo product (offline)**. Camera scanning needs pyzbar + opencv system libs; if missing the app shows DEMO mode instead of crashing.

## Deploy
The app can run on a Streamlit host (`streamlit run app.py --server.port $PORT --server.address 0.0.0.0`). Keep `OPENROUTER_API_KEY` in the host's server-side environment settings; never put it in browser code or commit it. Scan and chat history is session-only and is not persisted. No cloud DB or account system is used.
