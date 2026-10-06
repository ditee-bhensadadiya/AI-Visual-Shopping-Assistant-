# AI Visual Shopping Assistant

Phase 1 establishes the Supabase database, storage configuration, and trusted Python database access. This repository does not yet contain the API or frontend; those begin in Phase 2. See [SPEC.md](SPEC.md), [phases.md](phases.md), and [ARCHITECTURE.md](ARCHITECTURE.md).

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
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r backend/requirements.txt
   cd backend
   python -m unittest discover -s tests -v
   ```

The local stack exposes the Supabase API at `http://127.0.0.1:54321` by default. To manually check connectivity and CRUD, from `backend` with the environment loaded, use the `ProductRepository` and `get_supabase_client()` from `app.database`. The service key is intentionally required for these trusted server-side catalog write operations.

### Hosted Supabase project

Create a Supabase project, then link this directory with `supabase link --project-ref <project-ref>` and apply the migrations with `supabase db push`. Review the migration SQL before applying it to a shared or production project. Set `.env`'s URL to the project URL and its service-role key from the project's API settings; do not commit either secret. The migrations create private `uploads` and public-read `product-images` Storage buckets, public read policies for catalog/offer data, and user ownership policies for user-owned records.

## Phase 1 database contents

The initial migration creates the specification's core catalog, offers, price history, upload, detection, identification, match, saved-product, and alert tables. It enables pgvector without selecting an embedding dimension, adds integrity constraints and query indexes, and enables RLS on all application tables. Public client roles can read catalog and offer data; user records are owner scoped; processing internals and embeddings have no client policies. The synthetic seed records use `example.com` placeholders and do not represent live retailer integrations.

The backend Supabase client reads `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` from the environment. `ProductRepository` provides catalog product CRUD through that client. Authentication UI, upload workflows, API routes, AI services, retailer integrations, and embedding generation are outside Phase 1.
