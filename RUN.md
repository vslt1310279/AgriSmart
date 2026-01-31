# How to run AgriSmart (terminal commands)

Run everything from the **AgriSmart** project folder (the folder that contains `app.py` and the `backend` folder).

---

## 1. Install dependencies (once)

```bash
# Frontend
pip install -r requirements.txt

# Backend (includes TensorFlow; can take a few minutes)
pip install -r backend/api/requirements.txt
```

---

## 2. Start the backend

Open a terminal, go to the AgriSmart folder, then run:

**Windows (Command Prompt / CMD):**

```cmd
cd path\to\AgriSmart
set PYTHONPATH=%CD%
python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
```

**Windows (PowerShell):**

```powershell
cd path\to\AgriSmart
$env:PYTHONPATH = (Get-Location).Path
python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
```

**Linux / macOS:**

```bash
cd /path/to/AgriSmart
export PYTHONPATH=.
python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
```

Leave this terminal open. When you see:

```
Uvicorn running on http://0.0.0.0:8000
```

the backend is running. **In your browser use http://localhost:8000** (not 0.0.0.0).

---

## 3. Start the frontend

Open a **second** terminal, go to the same AgriSmart folder, then run:

**Any OS:**

```bash
cd path\to\AgriSmart
streamlit run app.py --server.port 8501
```

Then open **http://localhost:8501** in your browser.

---

## 4. Quick reference

| What        | Command (from AgriSmart folder) |
|------------|----------------------------------|
| **Backend** (CMD)   | `set PYTHONPATH=%CD%` then `python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000` |
| **Backend** (PowerShell) | `$env:PYTHONPATH = (Get-Location).Path` then `python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000` |
| **Backend** (Linux/Mac) | `export PYTHONPATH=.` then `python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000` |
| **Frontend** | `streamlit run app.py --server.port 8501` |

- Backend URL: **http://localhost:8000** (health: http://localhost:8000/health)
- Frontend URL: **http://localhost:8501**

---

## If you get a 500 error on “Run analysis”

1. Look at the **backend terminal** — the full Python traceback will appear there.
2. The **frontend** will also show the error message returned by the backend (e.g. missing model file, missing CSV, database error).
3. Typical causes:
   - **Disease model not found** — ensure `backend/plant_disease_recognition_model/plant_disease_model_working.h5` and `backend/plant_disease_recognition_model/classes.txt` exist.
   - **IFS CSV not found** — ensure `backend/ifs_recommender/ifs - TN_IFS_TNAU_Complete.csv` exists.
   - **Database error** — ensure the project folder is writable (for SQLite) or set `DATABASE_URL` for PostgreSQL.
