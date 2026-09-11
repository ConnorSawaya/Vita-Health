# Vita Health

Barcode food scanner + AI health analysis (Streamlit). Created by Connor Sawaya, shreeyuvan, James.

## What it is
Scan a product barcode (camera) or load the offline demo product, get a health score + analysis, keep scan history in `ai_analysis_history.json`, ask follow-ups in chat.

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
python -m py_compile app.py ai.py
python -c "import os; os.environ.pop('OPENROUTER_API_KEY',None); import ai; print(ai.ai_analysis('')[0:40]); print(ai.handle_follow_up('hi')[0:40])"
```

## Env vars
- `OPENROUTER_API_KEY` (optional). Without it the app runs in OFFLINE/MOCK mode with sample analysis. Never commit `.env`.

## Offline/demo
No key and no camera needed: press **Load demo product (offline)**. Camera scanning needs pyzbar + opencv system libs; if missing the app shows DEMO mode instead of crashing.

## Deploy
Local-first. Any Streamlit host works (`streamlit run app.py --server.port $PORT --server.address 0.0.0.0`). No cloud DB, no auth.
