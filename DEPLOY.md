# Deploy AgriSmart: GitHub + Free Hosting

## 1. Push code to GitHub

### Create a new repository

1. Go to [github.com](https://github.com) and sign in.
2. Click **New repository**.
3. Name it e.g. `AgriSmart` (or `agrismart`).
4. Choose **Public**, do **not** initialize with README (you already have one).
5. Click **Create repository**.

### Push from your machine

In PowerShell or Command Prompt, from your **AgriSmart** project folder:

```bash
git init
git add .
git commit -m "Initial commit: AgriSmart frontend + backend + disease + IFS + history"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/AgriSmart.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username. If you use SSH:

```bash
git remote add origin git@github.com:YOUR_USERNAME/AgriSmart.git
git push -u origin main
```

**Note:** If `.gitignore` is missing or wrong, add it (see project root) so you don’t commit `venv/`, `__pycache__/`, `.env`, or large model files you prefer to keep local.

---

## 2. Free hosting options

AgriSmart has two parts:

- **Frontend**: Streamlit (`app.py`).
- **Backend**: FastAPI (disease + IFS + DB). Needs more RAM/CPU and can use free PostgreSQL.

Below are **free** options. Limits (sleep, build time, RAM) apply; read each provider’s docs.

### A. Frontend: Streamlit Community Cloud (free)

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
2. **New app** → select repo `YOUR_USERNAME/AgriSmart`, branch `main`, main file `app.py`.
3. In **Advanced settings**, add:
   - **Environment variables**: `BACKEND_URL` = your backend URL (see below).
4. Deploy. Your app will be at `https://YOUR_APP_NAME.streamlit.app`.

The frontend will call the backend using `BACKEND_URL`. So you need the backend deployed somewhere and, if you use a DB, a database URL.

---

### B. Backend + DB: Render (free tier)

**Backend (Web Service)**

1. [render.com](https://render.com) → Sign up (GitHub).
2. **New** → **Web Service**.
3. Connect repo `AgriSmart`, branch `main`.
4. Settings:
   - **Build command**: `pip install -r backend/api/requirements.txt` (or add a root `requirements.txt` that includes backend deps and use `pip install -r requirements.txt`).
   - **Start command**: `python -m uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT`
   - **Root directory**: leave default (repo root).
   - **Environment variables**:
     - `DATABASE_URL` = (from the PostgreSQL step below).
     - `PYTHONPATH` = `.` (or the path to your project root so `backend.api` resolves).
5. Create. Note the URL, e.g. `https://agrismart-api.onrender.com`.

**PostgreSQL (free)**

1. On Render: **New** → **PostgreSQL**.
2. Create the database; copy the **Internal Database URL** (or **External** if your app runs elsewhere).
3. Use that as `DATABASE_URL` in the backend. If it starts with `postgres://`, the app converts it to `postgresql://` automatically.

**Important:** On free tier, the backend **spins down** after inactivity; the first request after sleep can take 30–60 seconds. Set `BACKEND_URL` in Streamlit to this Render URL.

---

### C. Backend + DB: Railway (free tier)

1. [railway.app](https://railway.app) → Login with GitHub.
2. **New Project** → **Deploy from GitHub** → select `AgriSmart`.
3. Add **PostgreSQL** from the same project (one-click).
4. Add a **Service** for the backend:
   - **Build**: e.g. `pip install -r backend/api/requirements.txt` (or your single requirements file).
   - **Start**: `python -m uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT`
   - **Root**: repo root; set `PYTHONPATH=.` if needed.
5. In **Variables**, set `DATABASE_URL` from the PostgreSQL service (Railway gives a URL).
6. Deploy; copy the public URL and use it as `BACKEND_URL` in Streamlit.

---

### D. Backend: Fly.io (free allowance)

1. Install [flyctl](https://fly.io/docs/hands-on/install-flyctl/).
2. In the repo: `fly launch` (follow prompts; don’t add Postgres yet if you want to use an external free DB).
3. Add a `Dockerfile` if needed (e.g. install Python, install deps, run uvicorn).
4. Set `DATABASE_URL` and any other secrets: `fly secrets set DATABASE_URL=...`
5. `fly deploy`. Use the generated URL as `BACKEND_URL`.

For **free PostgreSQL**, you can use **Neon** or **Supabase** (see below) and set `DATABASE_URL` on Fly.io.

---

## 3. Free PostgreSQL (if not using Render/Railway DB)

- **Neon**: [neon.tech](https://neon.tech) — free tier, copy connection string → `DATABASE_URL`.
- **Supabase**: [supabase.com](https://supabase.com) — free tier, use the **Connection string** (URI) from Project Settings → Database.
- **ElephantSQL**: [elephantsql.com](https://www.elephantsql.com) — free tier, copy URL → `DATABASE_URL`.

Use this `DATABASE_URL` in your backend (Render, Railway, Fly.io, etc.).

---

## 4. Free domain (optional)

- **Streamlit Cloud**: Your app gets `*.streamlit.app` by default (free).
- **Backend**: Render/Railway/Fly give a free subdomain (e.g. `yourapp.onrender.com`). No custom domain required.
- For a **custom free subdomain**, you can use **Freenom** (e.g. `agrismart.tk`) or **no-ip**; then point DNS to your backend/frontend. Provider docs explain how to attach a custom domain.

---

## 5. Checklist

1. **GitHub**: Repo created, code pushed (`git add .`, `git commit`, `git push`).
2. **Database**: PostgreSQL created (Render, Railway, Neon, Supabase, or ElephantSQL); `DATABASE_URL` set in backend.
3. **Backend**: Deployed (Render / Railway / Fly.io); `PYTHONPATH` and start command correct; `DATABASE_URL` and any secrets set.
4. **Frontend**: Deployed on Streamlit Community Cloud; `BACKEND_URL` set to your backend URL.
5. **Test**: Open the Streamlit app, upload an image, enter location → check disease + IFS and **History** page.

If the backend sleeps (e.g. Render free), the first request may be slow; subsequent ones should be fast until the next sleep.
