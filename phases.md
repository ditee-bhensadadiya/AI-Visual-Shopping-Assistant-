# AI Visual Shopping Assistant — Development Phases

## Phase 0 — Architecture

Goal:

Understand the repository and establish the architecture.

Tasks:

- Inspect repository.
- Read SPEC.md.
- Create architecture documentation.
- Identify dependencies.
- Create implementation plan.
- Do not implement application features.

Deliverable:

Architecture document.

---

# Phase 1 — Supabase Foundation

Goal:

Connect the application to Supabase.

Tasks:

- Configure Supabase project.
- Configure environment variables.
- Create database migrations.
- Create tables.
- Enable pgvector.
- Configure Row Level Security.
- Create Storage buckets.
- Create seed data.
- Create Supabase client abstraction.
- Add database tests.

Do not implement:

- YOLO
- VLM
- embeddings generation
- video processing
- retailer APIs

Acceptance:

The backend can connect to Supabase and perform CRUD operations.

---

# Phase 2 — FastAPI + React Foundation

Goal:

Create the application foundation.

Backend:

- FastAPI
- configuration
- health endpoint
- error handling
- logging
- CORS

Frontend:

- React
- TypeScript
- Tailwind
- routing
- API service
- basic layout

Acceptance:

Frontend and backend communicate successfully.

---

# Phase 3 — Image Upload

Goal:

Allow users to upload images.

Tasks:

- Upload UI
- File validation
- FastAPI upload endpoint
- Supabase Storage
- Upload database record
- Processing status

Acceptance:

User can upload an image and see the uploaded image.

---

# Phase 4 — YOLO Product Detection

Goal:

Detect products in uploaded images.

Pipeline:

image
→ YOLO
→ bounding boxes
→ confidence
→ crop

Tasks:

- YOLO service
- detector abstraction
- detection schema
- detection database records
- crop storage
- API endpoint
- frontend visualization

Acceptance:

Detected products are displayed with bounding boxes.

---

# Phase 5 — Multimodal Product Identification

Goal:

Understand what the detected product is.

Pipeline:

product crop
→ vision-language model
→ structured product attributes

Tasks:

- multimodal provider interface
- provider implementation
- Pydantic output schema
- confidence handling
- database storage

Acceptance:

A detected product produces structured attributes.

---

# Phase 6 — Embeddings + Semantic Matching

Goal:

Match detected products against the product catalog.

Pipeline:

product image
→ embedding
→ pgvector
→ similarity search
→ ranked candidates

Tasks:

- embedding service
- product embedding storage
- pgvector similarity query
- top-k retrieval
- metadata filtering
- ranking service

Acceptance:

The system returns ranked catalog matches.

---

# Phase 7 — Product Catalog + Retailer Price Comparison

Goal:

Connect matched products to retailer offers.

Tasks:

- retailer abstraction
- retailer product records
- development dataset
- price normalization
- comparison engine
- best-price selection

Acceptance:

The system displays multiple retailer prices and identifies the best available price.

---

# Phase 8 — Historical Price Tracking

Goal:

Track price changes.

Tasks:

- price_history table
- scheduled price collection
- price snapshots
- historical statistics
- Recharts visualization

Display:

- current price
- lowest price
- highest price
- average price
- price trend

Acceptance:

A product displays a historical price chart.

---

# Phase 9 — Video / Reel Processing

Goal:

Analyze uploaded videos.

Pipeline:

video
→ frame sampling
→ YOLO
→ tracking
→ duplicate removal
→ product identification

Tasks:

- video validation
- FFmpeg integration
- configurable frame sampling
- detection across frames
- tracking
- duplicate detection
- unique product extraction

Acceptance:

A video containing products produces unique product candidates.

---

# Phase 10 — Authentication + User Features

Goal:

Add user-specific functionality.

Tasks:

- Supabase Auth
- signup
- login
- logout
- protected routes
- saved products
- search history
- price alerts

Configure RLS carefully.

Acceptance:

Each user can access only their own private data.

---

# Phase 11 — Dashboard + UX

Goal:

Build polished user experience.

Pages:

- Home
- Upload
- Processing
- Results
- Product Details
- Price History
- Saved Products
- Alerts
- Profile

Add:

- loading states
- empty states
- error states
- responsive design
- product cards
- price comparison UI
- charts

Acceptance:

The application feels like a usable product rather than a technical demo.

---

# Phase 12 — Testing + Deployment

Goal:

Prepare for production.

Tasks:

- unit tests
- integration tests
- API tests
- frontend tests
- security review
- environment configuration
- Docker
- deployment
- logging
- monitoring
- README
- architecture documentation

Acceptance:

A fresh developer can clone the repository, configure environment variables, run the project, and understand the architecture.