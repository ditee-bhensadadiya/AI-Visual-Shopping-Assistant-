# AI Visual Shopping Assistant — Architecture and Phase 0 Plan

## Status

This document records the Phase 0 architecture and implementation plan. It does not implement application features. The repository currently contains `phases.md` and `spac.md`; it has no `SPEC.md`, source code, dependency manifests, tests, migrations, or Git metadata. `spac.md` is treated as the project specification because its contents match the specification referenced by the phases document. Rename it to `SPEC.md` in a documentation cleanup if desired; no source document was changed for this plan.

## Product scope

The product accepts user supplied product images and videos, identifies candidate products, finds similar catalog items, compares retailer prices, presents price history, and eventually supports saved products and price alerts. The system is intended to be modular and suitable for a student portfolio while following production oriented practices.

The phases define the delivery boundary. Phase 0 establishes architecture and a plan only. Supabase foundation is Phase 1; FastAPI and React foundation is Phase 2; image upload and all AI, catalog, pricing, video, authentication, and deployment features are later phases. No feature implementation belongs in Phase 0.

## Proposed system architecture

```text
Browser (React + TypeScript)
        │ HTTPS / JSON API
        ▼
FastAPI application (Python)
  ├── API routes, validation, errors, request logging
  ├── application services and workflow coordination
  ├── provider interfaces (vision, embeddings, retailer)
  └── persistence/storage adapters
        │
        ├── Supabase PostgreSQL (+ pgvector)
        ├── Supabase Storage
        └── Supabase Auth (introduced with user features)
```

The browser is a presentation and interaction layer and must not receive privileged Supabase credentials. The Python backend owns orchestration and AI processing. Postgres is the source of truth for catalog, processing, match, and price records. Storage holds uploaded media and generated crops. Provider interfaces isolate external model and retailer integrations so implementations can be replaced without spreading provider details through application code.

Long running image and video work should be represented by persisted processing status and executed outside the synchronous request path when the workload warrants it. The initial foundation should keep the execution model simple; a queue/worker is a later architectural decision based on measured processing time and hosting constraints, not a Phase 0 dependency. Video processing samples configurable frames and must not infer on every frame.

## Proposed repository layout

```text
frontend/                 React + TypeScript + Vite application
  src/{components,pages,hooks,services,types,utils}/
backend/                  Python API and domain services
  app/{api,schemas,services,database,utils}/
  app/services/{vision,multimodal,embeddings,matching,pricing,video}/
  tests/
supabase/
  migrations/
  seed/
data/                     small, licensed development fixtures only
docs/                     architecture and operational documentation
scripts/                  repeatable developer/maintenance tasks
.env.example              names and safe placeholders only
docker-compose.yml        local orchestration when introduced
README.md
SPEC.md                   canonical product specification (currently spac.md)
PHASES.md                 canonical phase plan (currently phases.md)
```

Create directories as their phase needs them; this is a target structure, not a Phase 0 scaffolding task. Keep model weights and user uploads out of source control. Document fixture provenance and licensing before adding sample media or catalog data.

## Main boundaries and responsibilities

- **Frontend:** upload/result experiences, navigation, accessible responsive UI, and typed API calls. It does not implement AI processing or access privileged database credentials.
- **API/application layer:** HTTP contracts, validation, authorization, stable error responses, request identifiers, and coordination of domain workflows.
- **Domain services:** detection, identification, embeddings, retrieval/ranking, retailer offer normalization, and price calculations. Each external capability is accessed through a narrow interface.
- **Persistence:** migrations define the relational schema and RLS policies. A backend adapter centralizes database access. Storage access is similarly isolated. Use server-side credentials only in trusted backend contexts.
- **Supabase:** PostgreSQL, Storage, Auth, RLS, and pgvector. Auth can be configured as infrastructure before user-facing authentication is built; user features are Phase 10.
- **External providers:** vision-language and retailer providers are replaceable adapters. A development retailer dataset is explicit and must never be presented as live retailer inventory.

## Data model direction

The specification's entities are a useful starting point: products, product images, product embeddings, retailers, retailer products/offers, price history, uploads, detections, identified products, product matches, saved products, and price alerts. Phase 1 should create only the subset needed for its accepted database foundation and keep migrations incremental. Later phases add records as workflows arrive.

Key relationships: a user owns uploads, saved products, and alerts; an upload has detections; a detection may yield an identified product; identified products have ranked matches to catalog products; catalog products have retailer offers; each offer has price observations. Use UUID identifiers, foreign keys, timestamps, explicit currency and availability, and constraints/indexes that support ownership, lookup, and history queries. Embedding dimensions and model identity must be explicit and consistent with the selected embedding model. Avoid committing to a vector dimension until the model is selected.

RLS must protect user-owned rows. Define policies alongside schema migrations and test them with distinct user identities before exposing user data. Public catalog read access and backend-only writes should be deliberate policy choices. Never expose service-role credentials to the frontend or log credentials.

## Dependency plan

No dependencies are installed or declared in the current repository. Add dependencies in the phase that first needs them, pin compatible versions, and document local setup. Expected categories from the specification:

| Area | Candidate dependencies | Introduced |
|---|---|---|
| Backend API/configuration | FastAPI, Pydantic, Uvicorn, Supabase Python client | Phase 1/2 (Supabase client in Phase 1; API stack in Phase 2) |
| Database | Supabase PostgreSQL; pgvector extension | Phase 1 |
| Frontend | React, TypeScript, Vite, Tailwind CSS, router, HTTP client | Phase 2 |
| Visual detection | OpenCV, YOLO implementation, PyTorch | Phase 4 |
| Multimodal identification | Provider SDK behind internal interface | Phase 5 |
| Embedding and similarity | CLIP/OpenCLIP or selected compatible model; pgvector | Phase 6 (pgvector extension setup in Phase 1) |
| Video | FFmpeg and OpenCV | Phase 9 |
| Charts | Recharts | Phase 8/11 |
| Scheduling/deployment | Supabase Cron, Docker, deployment platform tooling | As required in later phases |

These are candidate technologies, not selected versions or claims of integration. Before adopting a package, check current compatibility, licensing, platform support, model hardware needs, and whether it is needed by the current phase. Keep heavyweight ML dependencies out of the base API installation until their phase.

## Cross-cutting decisions

1. **Incremental delivery:** implement only the current phase's acceptance criteria; do not pull future feature work forward.
2. **Typed contracts:** use Pydantic request/response and model-output schemas; keep frontend API types aligned with documented API contracts.
3. **Provider isolation:** vision-language, embedding, detection, retailer, database, and storage integrations sit behind interfaces/adapters where replacement is plausible.
4. **Security:** secrets come from environment/configuration, privileged keys remain server side, uploads are validated, and RLS is tested as user features are added.
5. **Observability:** structured logs carry request/processing identifiers, stage and duration; never log secrets or raw sensitive media.
6. **Honest data:** distinguish development fixtures from live offers; do not invent retailer API integrations or imply real time accuracy without a verified source.
7. **Media processing:** validate type, size, and decodability; bound resource use; sample video frames at a configurable interval; retain only media required by product behavior and documented retention policy.
8. **Ranking:** combine visual, text, brand, category, model, and attribute signals through configurable weights; persist enough component scores to explain and tune ranking.

## Phase-by-phase implementation plan

### Phase 0 — Architecture (current)

- Inspect repository and source documents.
- Record baseline, target architecture, boundaries, dependency categories, data model direction, security considerations, and phased implementation plan in this document.
- No application code, scaffolding, dependencies, schema, or tests.
- Exit: architecture document is reviewable and implementation begins only when Phase 1 is requested.

### Phase 1 — Supabase foundation

- Decide/configure Supabase project and local development approach; document required environment variables with safe placeholders.
- Add migration and seed organization; enable pgvector; introduce initial schema in small migrations.
- Configure RLS and Storage buckets/policies appropriate to initial data ownership.
- Add a backend Supabase client abstraction and CRUD operations for the Phase 1 schema.
- Add database tests for CRUD, constraints, and access policies; keep YOLO, VLM, embeddings generation, video processing, and retailer APIs out.
- Acceptance: backend can connect and perform the specified CRUD operations.

### Phase 2 — API and web foundations

- Add FastAPI configuration, health endpoint, consistent error handling, structured logging, and controlled CORS.
- Add React/TypeScript/Vite/Tailwind app, routing, layout, and a centralized typed API service.
- Establish local developer commands and environment documentation.
- Acceptance: frontend successfully communicates with backend.

### Phase 3 — Image upload

- Add upload UI, client/server validation, upload endpoint, storage integration, upload record, and processing status.
- Enforce file size/type limits and meaningful errors; keep authorization rules aligned with available auth setup.
- Acceptance: user can upload an image and see it represented in the application.

### Phase 4 — Product detection

- Add detector interface and YOLO adapter, validated detection schema, bounding-box/crop persistence, and API/UI visualization.
- Acceptance: detected products and boxes are displayed for uploaded images.

### Phase 5 — Product identification

- Add provider interface, selected VLM adapter, structured Pydantic output, confidence handling, and persistence.
- Acceptance: a detected crop yields validated product attributes.

### Phase 6 — Embeddings and matching

- Select model/dimension, generate and store embeddings, add pgvector retrieval and metadata filters, and implement configurable multi-signal ranking.
- Acceptance: ranked catalog candidates are returned and component scores are inspectable.

### Phase 7 — Catalog and retailer comparison

- Add retailer provider abstraction, development dataset, offer normalization, currency-aware comparison, and best available price selection.
- Add a real provider only when its API/feed and usage terms are verified.
- Acceptance: multiple offers and the best available price are displayed where fixture data supports it.

### Phase 8 — Historical prices

- Persist observations, schedule collection through the chosen supported mechanism, calculate current/low/high/average/change statistics, and chart history.
- Acceptance: a product has a historical price view.

### Phase 9 — Video processing

- Validate videos, sample configurable frames with FFmpeg/OpenCV, run detection/tracking, deduplicate candidates, and reuse identification/matching workflows.
- Bound runtime, file size, and resource consumption; do not process every frame.
- Acceptance: a video produces deduplicated product candidates.

### Phase 10 — Authentication and user features

- Add Supabase Auth flows, protected frontend routes, saved products, search history if retained in scope, and price alerts.
- Tighten/test RLS for every user-owned record and implement alert evaluation/notification behavior.
- Acceptance: users can access only their own private data.

### Phase 11 — Dashboard and UX

- Build Home, Upload, Processing, Results, Product Details, Price History, Saved Products, Alerts, and Profile experiences as supported by implemented backend features.
- Add responsive layouts, accessible states, product/offer displays, and charts.
- Acceptance: coherent usable end-to-end product experience.

### Phase 12 — Verification and deployment

- Run unit, integration, API, frontend, and security checks; configure Docker and deployment; document environment, operations, monitoring, and recovery.
- Acceptance: a new developer can configure and run the project and understand the architecture; deployment is verified.

## Phase 0 completion and next decisions

Phase 0 is complete when this document is accepted as the architecture baseline. Before or during Phase 1, decide the Supabase project/local workflow, deployment target constraints, initial schema subset, and development seed data. Before the corresponding later phases, select model/provider versions, embedding dimensions, retailer sources, video limits, and retention policy. These choices depend on current provider capabilities and project constraints and should be verified when implementation reaches them.

## Known limitations

- The product specification and phase plan are currently named `spac.md` and `phases.md`, while their contents refer to `SPEC.md` and `PHASES.md`.
- No source code, runtime environment, dependency manifest, Supabase project, or Git repository was present to validate against.
- Technology names are proposed by the supplied specification; dependency versions, provider availability, costs, and deployment details remain unverified and intentionally undecided in Phase 0.
