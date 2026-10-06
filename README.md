# AI Visual Shopping Assistant

Phase 1 establishes the Supabase database, storage configuration, and trusted Python database access. The Phase 2 API and frontend foundation is in place; product workflows are still planned for later phases. See [SPEC.md](SPEC.md), [phases.md](phases.md), and [ARCHITECTURE.md](ARCHITECTURE.md).

## Supabase setup

### Local development

1. Install Docker Desktop and the Supabase CLI using their official installation instructions.
2. From the repository root, start the local Supabase stack:

   ```powershell
   supabase start
   supabase db reset
   ```

   `db reset` applies `supabase/migrations/` and loads the clearly synthetic fixtures in `supabase/seed.sql`.
3. Copy `.env.example` to `.env` and set `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` to the local API URL and `service_role` key printed by `supabase start`. Keep `.env` private; the service-role key bypasses RLS and is for trusted backend processes only.
4. Install the backend dependency and run the database adapter tests:

   ```powershell
   python -m venv backend\.venv
   New-Item -ItemType Directory -Force -Path D:\pip-cache,D:\pip-temp | Out-Null
   $env:PIP_CACHE_DIR = "D:\pip-cache"
   $env:TEMP = "D:\pip-temp"
   $env:TMP = "D:\pip-temp"
   backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
   cd backend
   .\.venv\Scripts\python.exe -m unittest discover -s tests -v
   ```

   After starting Supabase and setting `.env`, run the optional live round-trip test with `RUN_SUPABASE_INTEGRATION=1`; it creates and removes one uniquely named test product:

   ```powershell
   $env:RUN_SUPABASE_INTEGRATION = "1"
   .\.venv\Scripts\python.exe -m unittest tests.test_supabase_integration -v
   ```

The local stack exposes the Supabase API at `http://127.0.0.1:54321` by default. The included integration test checks connection and product CRUD with the configured backend client. The service key is intentionally required for these trusted server-side catalog write operations.

### Hosted Supabase project

Create a Supabase project, then link this directory with `supabase link --project-ref <project-ref>` and apply the migrations with `supabase db push`. Review the migration SQL before applying it to a shared or production project. Set `.env`'s URL to the project URL and its service-role key from the project's API settings; do not commit either secret. The migrations create private `uploads` and public-read `product-images` Storage buckets, public read policies for catalog/offer data, and user ownership policies for user-owned records.

## Phase 1 database contents

The initial migration creates the specification's core catalog, offers, price history, upload, detection, identification, match, saved-product, and alert tables. It enables pgvector without selecting an embedding dimension, adds integrity constraints and query indexes, and enables RLS on all application tables. Public client roles can read catalog and offer data; user records are owner scoped; processing internals and embeddings have no client policies. The synthetic seed records use `example.com` placeholders and do not represent live retailer integrations.

The backend Supabase client reads `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` from the environment. `ProductRepository` provides catalog product CRUD through that client. Authentication UI, upload workflows, API routes, AI services, retailer integrations, and embedding generation are outside Phase 1.

## Phase 2: FastAPI and React foundation

Phase 2 adds a FastAPI service with `GET /api/health`, request IDs, JSON request logs, consistent HTTP/validation/unexpected-error responses, and explicit CORS origins. The React, TypeScript, Vite, Tailwind CSS, and React Router frontend has a basic responsive shell, Home and Status routes, and a live backend health indicator. The Vite development server proxies `/api` to FastAPI at `http://127.0.0.1:8000`.

No upload flow, authentication UI, product search, AI, retailer integration, or other later-phase feature is implemented.

### Run the API

From the repository root in PowerShell:

```powershell
backend\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

The interactive API docs are at `http://127.0.0.1:8000/docs`.

### Run the frontend

In a second PowerShell window:

```powershell
New-Item -ItemType Directory -Force -Path D:\npm-cache,D:\npm-temp | Out-Null
$env:npm_config_cache = "D:\npm-cache"
$env:TEMP = "D:\npm-temp"
$env:TMP = "D:\npm-temp"
Set-Location frontend
npm.cmd install
npm.cmd run dev
```

Open `http://127.0.0.1:5173`. The page should show **API connected** while the backend is running. `BACKEND_CORS_ORIGINS` in `.env` accepts a comma-separated list; by default it allows the Vite localhost origins.

### Run checks

From the repository root:

```powershell
Set-Location backend
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
Set-Location ..\frontend
npm.cmd test
npm.cmd run build
```

With both servers running, verify the frontend proxy returns the backend response:

```powershell
Invoke-RestMethod http://127.0.0.1:5173/api/health
```




