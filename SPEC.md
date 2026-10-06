# AI-Powered Visual Shopping Assistant

## 1. Project Overview

Build an AI-powered visual shopping assistant that allows users to upload screenshots, images, and videos/reels containing products.

The system should:

1. Detect products in images/videos.
2. Identify product attributes using multimodal AI.
3. Generate visual/text embeddings.
4. Perform semantic product matching.
5. Search a product catalog and retailer data.
6. Compare current prices.
7. Track historical prices.
8. Display price trends.
9. Allow users to save products.
10. Allow users to configure price alerts.

The project should be built incrementally and should be production-oriented while remaining suitable for a student portfolio project.

---

# 2. Core User Flow

## Image Flow

User uploads screenshot/image.

image
→ upload
→ product detection
→ product cropping
→ product identification
→ attribute extraction
→ embedding generation
→ semantic search
→ product matching
→ retailer matching
→ price comparison
→ price history
→ result dashboard

---

# 3. Video Flow

User uploads a video/reel.

video
→ validation
→ frame sampling
→ object detection
→ object tracking
→ duplicate removal
→ product crops
→ product identification
→ embedding generation
→ semantic matching
→ price comparison
→ results

Do not process every video frame unnecessarily.

Use frame sampling and tracking to reduce computation.

---

# 4. Technology Stack

## Frontend

- React
- TypeScript
- Vite
- Tailwind CSS
- Recharts

## Backend

- Python
- FastAPI
- Pydantic
- Uvicorn

## Database

- Supabase PostgreSQL
- SQL
- Supabase Python client

## Storage

- Supabase Storage

## Authentication

- Supabase Auth

## Computer Vision

- OpenCV
- YOLO
- PyTorch

## Multimodal AI

Use a provider abstraction so the implementation can support:

- OpenAI vision-capable models
- Gemini
- other compatible vision-language models

Do not tightly couple the entire application to one provider.

## Embeddings

- CLIP/OpenCLIP for image embeddings
- sentence-transformers or compatible text embedding model where required

## Vector Search

- PostgreSQL pgvector through Supabase

## Video

- FFmpeg
- OpenCV

## Scheduling

- Supabase Cron initially

## Deployment

- Docker
- GitHub
- Cloud deployment

---

# 5. Architecture

Frontend:

React
↓
FastAPI
↓
AI services
↓
Supabase

Supabase provides:

- PostgreSQL
- Storage
- Authentication
- pgvector
- Row Level Security
- scheduled jobs where appropriate

AI processing remains primarily in the Python backend.

---

# 6. Database Design

## users

Use Supabase Auth for authentication.

Application-specific user information may be stored separately if required.

---

## products

Fields:

- id
- name
- brand
- category
- model
- description
- color
- gender
- image_url
- created_at
- updated_at

---

## product_images

Fields:

- id
- product_id
- image_url
- image_type
- created_at

---

## product_embeddings

Fields:

- id
- product_id
- embedding
- embedding_type
- model_name
- created_at

Use pgvector for the embedding column.

---

## retailers

Fields:

- id
- name
- website
- logo_url
- created_at

---

## retailer_products

Fields:

- id
- product_id
- retailer_id
- retailer_product_name
- product_url
- external_product_id
- current_price
- currency
- availability
- created_at
- updated_at

---

## price_history

Fields:

- id
- retailer_product_id
- price
- currency
- availability
- recorded_at

---

## uploads

Fields:

- id
- user_id
- file_path
- file_type
- file_size
- processing_status
- created_at

Processing states:

- uploaded
- processing
- completed
- failed

---

## detections

Fields:

- id
- upload_id
- frame_number
- class_name
- confidence
- x1
- y1
- x2
- y2
- crop_path
- created_at

---

## identified_products

Fields:

- id
- detection_id
- brand
- category
- model
- color
- description
- confidence
- created_at

---

## product_matches

Fields:

- id
- identified_product_id
- product_id
- visual_similarity
- text_similarity
- brand_score
- category_score
- final_score
- ranking
- created_at

---

## saved_products

Fields:

- id
- user_id
- product_id
- created_at

---

## price_alerts

Fields:

- id
- user_id
- product_id
- target_price
- currency
- is_active
- created_at
- triggered_at

---

# 7. Product Matching Architecture

Product matching should not rely only on one similarity score.

Use multiple signals:

visual similarity
+
text similarity
+
brand match
+
category match
+
model similarity
+
attribute similarity

Example conceptual score:

final_score =
0.40 × visual_similarity
+
0.25 × text_similarity
+
0.15 × brand_score
+
0.10 × category_score
+
0.10 × model_score

The exact weights should remain configurable.

Do not hardcode them throughout the codebase.

---

# 8. AI Pipeline

## Detection

YOLO detects candidate products.

Output:

- class
- confidence
- bounding box

---

## Identification

A vision-language model receives the product crop.

It should return structured information:

{
  category,
  brand,
  model,
  color,
  gender,
  description,
  attributes
}

Use Pydantic validation.

Do not depend on free-form model responses.

---

# 9. Embedding Pipeline

Product image:

image
→ CLIP/OpenCLIP
→ vector
→ pgvector

Query image:

image
→ embedding
→ vector similarity search
→ top-k candidates

Use metadata filters where appropriate.

---

# 10. Video Processing

Do not run inference on every frame.

Use:

video
→ FFmpeg/OpenCV
→ frame sampling
→ detection
→ tracking
→ duplicate removal
→ unique product candidates

The sampling interval must be configurable.

---

# 11. Retailer Data

Do not invent retailer APIs.

Create a provider abstraction:

RetailerProvider

Possible implementations:

- API provider
- product feed provider
- development dataset provider

If a real retailer API is unavailable, use a development dataset.

Do not pretend a live retailer integration exists.

Respect website terms, robots policies, API terms, licensing, and rate limits.

---

# 12. Price Tracking

Every price observation should be stored.

Example:

date | retailer | price

The system should calculate:

- current price
- lowest historical price
- highest historical price
- average price
- price change
- percentage change

---

# 13. Price Alerts

Users can specify:

"Notify me when this product is below ₹X."

A scheduled process checks active alerts.

When condition is satisfied:

price <= target_price

mark the alert as triggered and send the configured notification.

---

# 14. Security Requirements

Never hardcode:

- API keys
- database passwords
- service-role keys
- authentication secrets

Use environment variables.

Use Supabase Row Level Security for user-owned data.

Never expose privileged Supabase credentials to the frontend.

---

# 15. Error Handling

Every major service must handle:

- invalid files
- unsupported formats
- oversized files
- corrupted images
- corrupted videos
- model failures
- API failures
- timeout
- rate limits
- missing product matches
- missing prices
- database errors

The API should return meaningful errors.

---

# 16. Logging

Use structured application logging.

Log:

- request ID
- processing stage
- processing duration
- errors
- model used
- confidence/similarity where appropriate

Never log secrets.

---

# 17. Testing

Each phase must include appropriate tests.

Test:

- API endpoints
- database operations
- validation
- detection output
- AI response parsing
- embedding generation
- similarity ranking
- price calculations
- video processing
- authentication authorization

---

# 18. Development Rules

Build incrementally.

Never implement multiple future phases unless explicitly requested.

After every phase:

1. Run tests.
2. Verify the application starts.
3. Verify the phase manually.
4. Explain changed files.
5. Explain commands.
6. Explain known limitations.
7. Update documentation.

Do not rewrite working code unnecessarily.

Prefer modular services.

Keep AI providers behind interfaces.

Keep retailer integrations behind interfaces.

Keep storage behind an abstraction.

---

# 19. Project Structure

visual-shopping-assistant/

├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── types/
│   │   └── utils/
│   ├── package.json
│   └── vite.config.ts
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── api/
│   │   ├── schemas/
│   │   ├── services/
│   │   │   ├── vision/
│   │   │   ├── multimodal/
│   │   │   ├── embeddings/
│   │   │   ├── matching/
│   │   │   ├── pricing/
│   │   │   └── video/
│   │   ├── database/
│   │   └── utils/
│   ├── tests/
│   └── requirements.txt
│
├── supabase/
│   ├── migrations/
│   └── seed/
│
├── data/
│   ├── sample_images/
│   ├── sample_videos/
│   └── development_products/
│
├── models/
│
├── scripts/
│
├── docs/
│
├── .env.example
├── .gitignore
├── SPEC.md
├── README.md
└── docker-compose.yml

---

# 20. Definition of Done

The project is considered complete when:

1. A user can upload a screenshot.
2. Products can be detected.
3. Products can be identified.
4. Product embeddings can be generated.
5. Similar catalog products can be retrieved.
6. Products can be ranked.
7. Retailer prices can be displayed.
8. Historical prices can be displayed.
9. Users can upload videos.
10. Products can be detected from sampled video frames.
11. Duplicate detections can be removed.
12. Users can save products.
13. Users can configure price alerts.
14. The application has authentication.
15. User data is protected using RLS.
16. Tests exist for major functionality.
17. The application can be deployed.