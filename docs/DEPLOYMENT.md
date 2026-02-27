# Deployment Guide — Backend (Render / Railway / Fly.io), Database, Frontend (Vercel), Demo Link

This guide covers deploying the OLAP BI Platform to meet:

- **Backend** on cloud (Render / Railway / Fly.io)
- **Database** (DuckDB embedded with backend; optional Supabase/Postgres for audit)
- **Frontend** on Vercel
- **Working public demo link**

---

## 1. Backend (Render / Railway / Fly.io)

The backend is **FastAPI + DuckDB**. DuckDB is in-process (no separate DB server). Data is loaded from `sales_data.csv` at startup into a local DuckDB file.

### 1.1 Render

1. Push your repo to GitHub.
2. Go to [Render](https://render.com) → **New** → **Web Service**.
3. Connect the repo.
4. **Settings:**
   - **Runtime:** Docker
   - **Dockerfile path:** `backend/Dockerfile`
   - **Root directory:** leave empty (build context = repo root)
   - **Instance type:** Free (or paid)
5. **Environment:**
   - `DATABASE_PATH` = `/app/data/olap.duckdb`
   - `CSV_PATH` = `/app/data/sales_data.csv`
   - `PORT` is set by Render automatically.
6. Deploy. Note the URL, e.g. `https://olap-bi-api.onrender.com`.

**Using `render.yaml` (Blueprint):**  
If your repo has `render.yaml` at root, you can use **New** → **Blueprint** and connect the repo; Render will create the web service from the spec.

### 1.2 Railway

1. [Railway](https://railway.app) → **New Project** → **Deploy from GitHub** (select repo).
2. **Add service** → **Dockerfile**.
   - Dockerfile path: `backend/Dockerfile`
   - Build context: `.` (repo root)
3. **Variables:** Add `DATABASE_PATH=/app/data/olap.duckdb`, `CSV_PATH=/app/data/sales_data.csv`.
4. **Settings** → **Networking** → **Generate domain**. Copy the public URL.

### 1.3 Fly.io

```bash
# From repo root
fly launch --no-deploy --name olap-bi-api
# When prompted: don't add Postgres, use existing Dockerfile.
```

Create or edit `fly.toml` at repo root:

```toml
app = "olap-bi-api"

[build]
  dockerfile = "backend/Dockerfile"
  [build.args]

[env]
  DATABASE_PATH = "/app/data/olap.duckdb"
  CSV_PATH = "/app/data/sales_data.csv"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  processes = ["app"]
```

Then:

```bash
fly deploy
fly open
```

Your backend URL will be `https://olap-bi-api.fly.dev` (or the app name you chose).

---

## 2. Database

### 2.1 OLAP data (DuckDB)

The **OLAP database is DuckDB**, deployed with the backend:

- On startup, the backend runs `init_db()`: creates the star schema in `/app/data/olap.duckdb` and loads `sales_data.csv` if the fact table is empty.
- `sales_data.csv` is generated in the Docker image by `python data/generate_dataset.py` (see `backend/Dockerfile`).
- No separate “database server” is required for OLAP; the database is **embedded in the backend** on Render/Railway/Fly.

### 2.2 Optional: Supabase (Postgres) for audit / “deployed database”

If the requirement is to use **Supabase or Cloud Postgres** explicitly:

1. Create a project at [Supabase](https://supabase.com).
2. In **SQL Editor**, run:

```sql
CREATE TABLE IF NOT EXISTS analytics_log (
  id         BIGSERIAL PRIMARY KEY,
  query      TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

3. In **Settings** → **API**, copy **Project URL** and **anon public** key.
4. In your **backend** env (Render/Railway/Fly), add:
   - `SUPABASE_URL` = your project URL  
   - `SUPABASE_ANON_KEY` = anon key  
5. The backend will log each NL query to `analytics_log` (see `backend/tools/supabase_log.py`). This satisfies “deploy database (Supabase / Cloud Postgres)” while keeping OLAP on DuckDB.

---

## 3. Frontend (Vercel)

1. Push the repo to GitHub.
2. Go to [Vercel](https://vercel.com) → **Add New** → **Project** → import the repo.
3. **Framework Preset:** Vite.
4. **Root Directory:** `frontend`.
5. **Build Command:** `npm run build` (default).
6. **Output Directory:** `dist` (default).
7. **Environment variable:**
   - Name: `VITE_API_URL`  
   - Value: your **backend public URL** (e.g. `https://olap-bi-api.onrender.com` or `https://olap-bi-api.fly.dev`).  
   Do **not** add a trailing slash.
8. Deploy. Vercel will give you a URL like `https://olap-project-xxx.vercel.app`.

The frontend uses `VITE_API_URL` to call the backend (e.g. `/api/query/`, `/api/olap/...`). CORS is allowed from any origin in the backend; restrict in production if needed.

---

## 4. Public demo link

After deployment:

- **Frontend (demo):** `https://your-project.vercel.app`  
  Use this as the **working public demo link**.
- **Backend (API):** `https://your-backend.onrender.com` (or Railway/Fly URL).  
  Optional: link to **API docs** `https://your-backend.onrender.com/docs`.

Checklist:

1. Backend `/health` returns `{"status":"ok"}`.
2. Frontend loads and shows the chat.
3. Sending a query in the chat returns results (tables/charts/summary).

---

## 5. Quick reference

| Item        | Where              | URL / Env |
|------------|--------------------|-----------|
| Backend    | Render / Railway / Fly | e.g. `https://olap-bi-api.onrender.com` |
| Database   | DuckDB in backend  | `DATABASE_PATH`, `CSV_PATH` in backend env |
| Optional DB| Supabase (Postgres)| `SUPABASE_URL`, `SUPABASE_ANON_KEY` in backend |
| Frontend   | Vercel             | `VITE_API_URL` = backend URL |
| Demo link  | Vercel frontend URL| e.g. `https://olap-bi.vercel.app` |

---

## 6. Troubleshooting

- **Backend 502 / no response:** Ensure the Docker image builds and the app listens on `0.0.0.0` and the port given by the platform (`PORT`).
- **Frontend “network error”:** Set `VITE_API_URL` to the exact backend URL (no trailing slash). Ensure backend CORS allows your Vercel origin.
- **Database not loading:** In Docker, `sales_data.csv` must exist at `CSV_PATH`; the Dockerfile runs `python data/generate_dataset.py` to create it. If you use a custom CSV, mount it or set `CSV_PATH` to a URL the backend can fetch (would require a small code change to support URL).
