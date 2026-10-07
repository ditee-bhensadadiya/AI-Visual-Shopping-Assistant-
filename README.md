# AI Visual Shopping Assistant

The app uses a local Ollama vision model for product analysis on the Supabase-backed API and React app. See [SPEC.md](SPEC.md), [PHASES.md](PHASES.md), and [ARCHITECTURE.md](ARCHITECTURE.md).

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

The initial migration creates the catalog, offers, price history, upload, detection, identification, match, saved-product, and alert tables. It enables pgvector without selecting an embedding dimension, adds integrity constraints and query indexes, and enables RLS on the application tables. Public client roles can read catalog and offer data; user records are owner scoped; processing internals and embeddings have no client policies. Synthetic seed records use `example.com` placeholders and do not represent live retailer integrations.

The backend Supabase client reads `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` from the environment. `ProductRepository` provides catalog product CRUD through that client. Authentication UI, upload workflows, API routes, AI services, retailer integrations, and embedding generation are outside Phase 1.

## Phase 2: FastAPI and React foundation

Phase 2 adds a FastAPI service with `GET /api/health`, request IDs, JSON request logs, consistent HTTP/validation/unexpected-error responses, and explicit CORS origins. The React, TypeScript, Vite, Tailwind CSS, and React Router frontend has a basic responsive shell, Home and Status routes, and a live backend health indicator. The Vite development server proxies `/api` to FastAPI at `http://127.0.0.1:8000`.

Authentication UI, product search, AI, retailer integration, and other later-phase features are not implemented.

## Phase 3: Image upload

The Upload page accepts JPEG, PNG, and WebP images up to 10 MB. The FastAPI endpoint validates the file contents and size, assigns an opaque storage path, uploads the file to the private `uploads` bucket, records it with status `uploaded`, and returns a short-lived signed URL for the preview. It does not run product detection or other later-phase processing. Since authentication is Phase 10, the upload record uses a null `user_id`; apply the new migration before trying uploads against a hosted or existing local database.

The backend upload size limit is configured by `MAX_UPLOAD_BYTES` in `.env` (10 MB by default). The frontend also enforces a 10 MB limit. Preview links expire after one hour. Keep `SUPABASE_SERVICE_ROLE_KEY` on the backend only.

### Apply the Phase 3 migration

For local Supabase, apply migrations with `supabase db reset`. For a hosted project, use the Supabase dashboard SQL Editor to run `supabase/migrations/20261007000000_allow_pre_auth_uploads.sql`, or apply it through the CLI after reviewing it. This migration permits null `user_id` for uploads created before authentication; the private bucket and authenticated owner policies remain in place.

### Try an upload

Start the API and frontend using the Phase 2 commands above, open `http://127.0.0.1:5173/upload`, select a JPEG, PNG, or WebP image under 10 MB, then choose **Upload image**. A successful upload displays the private image preview, upload ID, and `uploaded` processing status. The signed preview URL expires after one hour.

## Phase 4: Local YOLO adapter

The backend retains the YOLO adapter for local experiments. YOLO's pretrained COCO model is limited to its fixed object classes and does not identify brands or product models. To install the optional YOLO detector, use `backend\.venv\Scripts\python.exe -m pip install -r backend\requirements-yolo.txt`.

## Phase 5: Local vision product recognition

The detection endpoint analyzes the full image with a local Ollama model instead of requiring a YOLO class match first. It returns approximate product boxes, descriptive product names, categories, colors, visible brands, and an optional model name. These results are estimates: a brand is returned only when the image provides reasonable visual evidence; otherwise the UI shows **Unknown**. No model can guarantee recognition of every product or brand. Ollama runs on your computer, so image analysis does not call a paid AI API. Model downloads use internet data and disk space; inference may be slower on a CPU.

Install [Ollama for Windows](https://ollama.com/download/windows). Before downloading its model, set its model directory to D: in PowerShell so the files avoid the nearly full C: drive:

```powershell
New-Item -ItemType Directory -Force -Path D:\OllamaModels | Out-Null
[Environment]::SetEnvironmentVariable("OLLAMA_MODELS", "D:\OllamaModels", "User")
```

Then sign out of Windows and sign back in (or restart Windows), start Ollama, and in PowerShell run:

```powershell
ollama pull qwen3-vl:4b-instruct
ollama list
```

The selected model uses about 3.3 GB for its model files. The 2B variant is smaller (about 1.9 GB) but may be less capable. Qwen3-VL requires a recent Ollama version; update Ollama if it does not recognize the model. Set these values in the repository root `.env`:

```dotenv
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_VISION_MODEL=qwen3-vl:4b-instruct
```

Restart the backend after changing `.env`. When **Detect products** is clicked, the backend sends the image to Ollama running on this computer. The result is saved in `detections` and `identified_products`; the original and crops remain in your Supabase project. Supabase storage is hosted and may have its own quota or pricing; the local model only removes per-image AI API charges. See [Ollama vision support](https://docs.ollama.com/capabilities/vision), [structured outputs](https://docs.ollama.com/capabilities/structured-outputs), and the [Qwen3-VL model page](https://ollama.com/library/qwen3-vl).

Ultralytics documents its open-source YOLO software and models under AGPL-3.0, with an Enterprise licensing option. Review the [Ultralytics licensing guidance](https://docs.ultralytics.com/help/contributing/#open-sourcing-your-yolo-project-under-agpl-3-0) before distributing or hosting this project; this repository does not add an application license.

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

Upload tests use a mocked Supabase client and do not create remote files. To verify a hosted upload end-to-end, apply the migration, run both services, and use the Upload page with a disposable image; the file and upload record remain in your Supabase project until you remove them.




