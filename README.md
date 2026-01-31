# AgriSmart 🌾

AI-powered farming assistant: **leaf disease recognition** + **Integrated Farming System (IFS)** recommendations by location. Upload a leaf image and enter a location/district; both models run **simultaneously** and results are stored in a database with a viewable **history** page.

## Features

- **Disease detection**: Upload a crop leaf image (JPG/PNG); model returns top class and confidence.
- **IFS recommender**: Enter location (village/town/city) or district; get Tamil Nadu IFS models and descriptions (geocoding via OpenStreetMap when using location).
- **Concurrent execution**: Disease and IFS run in parallel for faster response.
- **History**: All queries and results are saved (PostgreSQL or SQLite) and viewable from the **History** page in the app.

## Project structure

```
AgriSmart/
├── app.py                    # Streamlit frontend
├── requirements.txt          # Frontend deps (streamlit, pandas, requests)
├── run_backend.bat           # Start API only
├── run_frontend.bat          # Start Streamlit only
├── run_all.bat               # Start both (backend + frontend)
├── backend/
│   ├── api/                  # Unified FastAPI backend
│   │   ├── main.py           # /health, /analyze, /history, /history/{id}
│   │   ├── db.py             # DB session + create_log
│   │   ├── models.py         # QueryLog table, Pydantic schemas
│   │   ├── settings.py       # Paths, DATABASE_URL
│   │   ├── requirements.txt
│   │   └── services/
│   │       ├── disease.py    # Leaf disease model inference
│   │       └── ifs.py        # IFS recommender wrapper
│   ├── plant_disease_recognition_model/  # Disease model (.h5, classes.txt)
│   └── ifs_recommender/      # IFS CSV + recommend.py
├── .env.example
└── DEPLOY.md                 # GitHub + free hosting guide
```

## Local setup

**→ See [RUN.md](RUN.md) for step-by-step terminal commands (Windows CMD, PowerShell, Linux, macOS).**

### 1. Python

Use Python 3.11 or 3.12 (avoid 3.13 for TensorFlow compatibility).

### 2. Backend (API)

From the **project root** (AgriSmart):

```bash
pip install -r backend/api/requirements.txt
# Windows CMD: set PYTHONPATH=%CD%
# PowerShell:  $env:PYTHONPATH = (Get-Location).Path
# Linux/Mac:   export PYTHONPATH=.
python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
```

Or double‑click **run_backend.bat**.

- **Database**: By default uses SQLite (`./agrismart.db`). For PostgreSQL, set `DATABASE_URL` (see `.env.example`).
- **First request** may be slower while the disease model loads.

### 3. Frontend (Streamlit)

In another terminal, from project root:

```bash
pip install -r requirements.txt
streamlit run app.py --server.port 8501
```

Or double‑click **run_frontend.bat**.

- Set `BACKEND_URL` if the API is not at `http://localhost:8000`.

### 4. Use the app

1. Open **http://localhost:8501**.
2. In **Analyze**: upload a leaf image (JPG/PNG), enter **Location** or **District** (and optionally crop/soil type), click **Run analysis**.
3. View **Disease Detection** and **IFS Recommendations** side by side.
4. In **History**: see past queries and open a record by **Log ID**.

## Environment variables

| Variable        | Description                                      | Default              |
|----------------|--------------------------------------------------|----------------------|
| `BACKEND_URL`  | API base URL (used by Streamlit)                 | `http://localhost:8000` |
| `DATABASE_URL` | PostgreSQL or SQLite connection string          | `sqlite:///./agrismart.db` |

## API endpoints

- `GET /health` — Health check.
- `POST /analyze` — Form: `file` (image), `location`, `district`, `crop`, `soil_type`, `top_k`. Returns disease + IFS and stores in DB.
- `GET /history?limit=&offset=` — List recent log entries (summary).
- `GET /history/{id}` — Full record (disease_result, ifs_result, etc.).

## Pushing to GitHub and free deployment

See **[DEPLOY.md](DEPLOY.md)** for:

- Creating a GitHub repo and pushing your code.
- Free hosting options (Streamlit Community Cloud, Render, Railway, Fly.io).
- Free PostgreSQL (Neon, Supabase, ElephantSQL) and optional free subdomain.
