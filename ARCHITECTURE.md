## AI Restaurant Recommendation Service – Architecture

### 1. High-Level Overview

**Goal**: Build an AI-powered restaurant recommendation service that takes user preferences (price, place, rating, cuisine), calls an LLM together with structured data from the Zomato dataset on Hugging Face, and returns clear, personalized restaurant recommendations through an API.

**Key data source**: Hugging Face dataset `ManikaSaini/zomato-restaurant-recommendation`.

---

## 2. Phased Architecture

### Phase 1: Requirements & Domain Modeling

#### 1.1 Functional Scope

- **Core feature**: Given user preferences, return top-N restaurant recommendations with:
  - Name, location, rating, price, cuisines.
  - A short natural-language explanation per restaurant (from the LLM).
- **Inputs** (from clients via API):
  - `price_min`, `price_max` or a `price_band` (cheap, moderate, expensive).
  - `location` / `city` / `area`.
  - `min_rating`.
  - `cuisines` (list of preferred cuisines).
  - Optional: `limit`, `dietary_restrictions`, `sort_by` (rating, distance, popularity).
- **Outputs**:
  - List of recommendations where each item includes:
    - Structured restaurant data.
    - A numeric score.
    - An LLM-generated explanation.

#### 1.2 Domain Models (Conceptual)

- **Restaurant**
  - `id`
  - `name`
  - `cuisines` (list of strings)
  - `location` (city, area, optionally coordinates if available)
  - `average_cost_for_two` (numeric)
  - `price_band` (derived: cheap / moderate / expensive)
  - `rating` (float)
  - `votes` (int)
  - Optional: `highlights`, `url`, `menu_items` (as present in the dataset)

- **UserPreference**
  - `location` / `city` / `area`
  - `price_min`, `price_max` or `price_band`
  - `min_rating`
  - `cuisines` (list)
  - Optional: `limit`, `sort_by`, `dietary_restrictions`

- **Recommendation**
  - `restaurant_id`
  - `score` (numeric ranking score)
  - `explanation` (string from LLM)

---

### Phase 2: Data Layer & Ingestion

#### 2.1 Dataset Source

- **Source**: Hugging Face dataset `ManikaSaini/zomato-restaurant-recommendation`.
- **Access pattern**:
  - Use Hugging Face `datasets` library: `load_dataset("ManikaSaini/zomato-restaurant-recommendation")`.
  - Run ingestion as an offline or build-time step, not on every request.

#### 2.2 Data Ingestion Pipeline

**Folder**: `src/data_ingestion/`

- **`hf_client.py`**
  - Loads dataset from Hugging Face.
  - Handles caching and simple configuration (dataset name, split).

- **`schema_mapping.py`**
  - Maps raw dataset fields to the internal `Restaurant` model.
  - Normalizes:
    - `cuisines` (split on delimiter, trim, lowercase).
    - `average_cost_for_two` into `price_band`.
    - `rating` to float.
    - `location` fields (city, area).

- **`ingest.py`**
  - Orchestrates the ingestion:
    - Calls `hf_client` to fetch raw data.
    - Applies mapping and cleaning from `schema_mapping`.
    - Writes cleaned results into the chosen database.

#### 2.3 Storage Options

- **Initial (simple) storage**:
  - Local **SQLite** database.
  - Table `restaurants` with columns for all relevant restaurant fields.
  - Indexes on:
    - `city` / `location`.
    - `rating`.
    - `price_band` / `average_cost_for_two`.
    - `cuisines` (if stored in a searchable format).

- **Scalable storage (future)**:
  - **PostgreSQL** as primary relational store.
  - Optional vector store (FAISS, Qdrant, pgvector) if semantic search is needed later.

#### 2.4 Data Access Layer

**Folder**: `src/data_access/`

- **`models.py`**
  - ORM / data classes for:
    - `Restaurant` (DB model).
    - (Optional) any derived tables.

- **`repository.py`**
  - Query methods:
    - `get_restaurants(preferences: UserPreference) -> List[Restaurant]`
    - `get_restaurant_by_id(id: str) -> Restaurant`
    - `search_by_cuisine_and_price(...) -> List[Restaurant]`
  - Encapsulates raw SQL / ORM calls so higher layers do not depend on DB details.

---

### Phase 3: Recommendation Logic (Pre-LLM)

Phase 3 focuses on deterministic filtering and ranking to produce a compact candidate set that will be sent to a Groq-hosted LLM in Phase 4 for explanation generation.

#### 3.1 Rule-Based Filtering

**Folder**: `src/recommendation/`

- **`core_filtering.py`**
  - Filters restaurants based on:
    - Location (e.g. city/area).
    - Rating ≥ `min_rating`.
    - Price between `price_min` and `price_max` or matching `price_band`.
    - Cuisine intersection with `preferences.cuisines`.
  - Fallback strategies when too few candidates:
    - Relax cuisine requirement (e.g. similar cuisines or remove one constraint).
    - Slightly relax rating requirement.
    - Slightly expand price range.

#### 3.2 Scoring & Ranking

- **`scoring.py`**
  - Computes a composite score per restaurant:
    - Rating score.
    - Popularity score (based on `votes`).
    - Preference match score (cuisines, price, location).
  - Combines above with configurable weights:
    - Example: `score = w_rating * rating + w_votes * f(votes) + w_match * match_score`.
  - Returns list of restaurants with attached scores.

#### 3.3 Candidate Selection

- **`candidate_selector.py`**
  - From the scored list, selects top-N candidates (e.g. 10–20).
  - Produces a compact representation of candidates to pass into the LLM:
    - E.g. list of objects: `[{id, name, location, rating, price_band, cuisines}, ...]`.

---

### Phase 4: LLM Integration Layer

#### 4.1 LLM Client Abstraction

**Folder**: `src/llm/`

- **`llm_client.py`**
  - Interface:
    - `generate_recommendations(preferences: UserPreference, candidates: List[Restaurant]) -> List[Recommendation]`
  - Responsibilities:
    - Calls the configured LLM provider (e.g., OpenAI/Anthropic/Azure/local).
    - Handles API keys, timeouts, retry logic.
    - Normalizes the response into the internal `Recommendation` domain model.

#### 4.2 Prompt Engineering

- **`prompts.py`**
  - Defines:
    - **System prompt**: Sets behavior as a helpful restaurant recommendation assistant that must only use given candidates.
    - **User / assistant templates**:
      - Insert user preferences.
      - Insert the candidate restaurant list (structured).
      - Instruct the LLM:
        - Not to invent restaurants not in the candidate list.
        - To choose up to `limit` restaurants.
        - To output in a strict, parseable JSON format:
          ```json
          {
            "recommendations": [
              {
                "restaurant_id": "string",
                "explanation": "string"
              }
            ]
          }
          ```

#### 4.3 Response Parsing & Validation

- **`response_parser.py`**
  - Parses raw LLM output into:
    - List of `Recommendation` objects, each with `restaurant_id` and `explanation`.
  - Validates:
    - All `restaurant_id`s exist in the candidate list.
    - Output schema is respected (e.g., handle malformed JSON).
  - Fallback behavior:
    - If parsing fails, either:
      - Re-prompt the LLM with a stricter instruction.
      - Or fall back to deterministic explanations built from rules (e.g. “High rating and fits your budget”).

---

### Phase 5: Backend Service (API Layer)

#### 5.1 API Design

**Stack recommendation**: Python + FastAPI.

**Folder**: `src/api/`

- **`schemas.py`**
  - Pydantic models:
    - `PreferenceRequest`:
      - `location: str`
      - `price_min: Optional[float]`
      - `price_max: Optional[float]`
      - `price_band: Optional[str]`
      - `min_rating: Optional[float]`
      - `cuisines: List[str]`
      - `limit: Optional[int]`
    - `RestaurantResponse`:
      - `id`, `name`, `location`, `rating`, `price_band`, `cuisines`, etc.
    - `RecommendationResponseItem`:
      - `restaurant: RestaurantResponse`
      - `score: float`
      - `explanation: str`
    - `RecommendationResponse`:
      - `preferences: PreferenceRequest`
      - `recommendations: List[RecommendationResponseItem]`

- **`main.py`**
  - FastAPI application setup and routing.
  - Endpoints:
    - `POST /recommendations`
      - Accepts `PreferenceRequest`.
      - Orchestrates flow via `recommendation_service` (see below).
      - Returns `RecommendationResponse`.
    - `GET /health`
      - Returns service and dependency health (DB, LLM availability).

#### 5.2 Application Service Layer

**Folder**: `src/services/`

- **`recommendation_service.py`**
  - Function: `get_recommendations(preferences: UserPreference) -> List[Recommendation]`
  - Flow:
    1. Translate API `PreferenceRequest` into `UserPreference`.
    2. Use `data_access.repository` to get initial candidate restaurants.
    3. Apply filtering in `recommendation/core_filtering.py`.
    4. Score and rank candidates via `recommendation/scoring.py`.
    5. Select top-N via `candidate_selector.py`.
    6. Call `llm_client.generate_recommendations()` with:
       - `UserPreference`.
       - Candidate subset.
    7. Merge LLM explanations with structured restaurant data.
    8. Map domain-layer results into API `RecommendationResponse`.

- This layer isolates business logic from HTTP and DB details.

---

### Phase 6: Configuration, Logging & Observability

#### 6.1 Configuration

**Folder**: `src/config/`

- **`settings.py`**
  - Loads configuration from environment variables or `.env`:
    - DB connection string (SQLite/Postgres).
    - Hugging Face dataset parameters.
    - LLM provider API key, model name, base URL.
    - Recommendation scoring weights.
    - Max candidates to send to LLM, default limit, etc.

#### 6.2 Logging

**Folder**: `src/common/`

- **`logging.py`**
  - Sets up structured logging (e.g., `logging` or `structlog`).
  - Logs:
    - Incoming requests (with anonymized data).
    - Counts of candidates at each filtering stage.
    - LLM call metadata (latency, truncated prompt size).
    - Errors, retries, and fallbacks.

- **`exceptions.py`**
  - Centralized exception types and error-handling utilities.
  - Mapped to appropriate HTTP responses in the API layer.

#### 6.3 Basic Observability

- Metrics (can be added later via middleware or libraries):
  - Requests per endpoint.
  - Latency per endpoint.
  - LLM call latency & error rate.
  - Recommendation counts.

---

### Phase 7: Evaluation & Testing

#### 7.1 Offline Evaluation

**Folder**: `src/evaluation/`

- Scripts and notebooks to:
  - Sample user preference scenarios (e.g. synthetic queries).
  - Generate recommendations in bulk.
  - Log outputs to files for manual review or basic heuristics:
    - Coverage of user constraints.
    - Diversity of cuisines/locations.
    - Distribution of ratings/prices.

#### 7.2 Automated Testing

**Folder**: `tests/`

- **Unit tests**:
  - `test_data_ingestion.py`: schema mapping and data cleaning logic.
  - `test_recommendation.py`: filtering, scoring, candidate selection.
  - `test_llm_parser.py`: robust parsing of LLM responses (with mocked outputs).
- **Integration tests**:
  - `test_api.py`:
    - Spin up FastAPI app with an in-memory DB and a fake/mocked LLM.
    - Test `POST /recommendations` end-to-end.

---

### Phase 8: Deployment Architecture

#### 8.1 Components

- **API Service**
  - Containerized FastAPI app.
  - Depends on:
    - Relational DB (SQLite for dev, Postgres for prod).
    - External LLM API.
- **Database**
  - Dev:
    - Local SQLite file.
  - Prod:
    - Managed Postgres (or compatible RDS).

- **External Services**
  - Hugging Face:
    - Used during ingestion/build time, not required for runtime.
  - LLM provider:
    - Required at runtime for generating explanations.

#### 8.2 Topology

- **Development**
  - Docker Compose:
    - `api` service (FastAPI).
    - `db` service (Postgres if not using SQLite).
  - Local ingestion script to populate DB from Hugging Face.

- **Production**
  - Containers on a cloud platform (e.g., Kubernetes/ECS/App Service) behind a load balancer.
  - CI/CD pipeline:
    - Run tests, linting.
    - Build image.
    - Run ingestion job (if needed) or handle separately.
    - Deploy API.

#### 8.3 UI / Frontend

- **Goal**: Provide a simple web UI where users can enter their preferences (location, price range, rating, cuisines) and view the recommended restaurants and explanations.
- **Tech suggestion**: React (or any SPA framework) served as a static site or separate container.
- **Responsibilities**:
  - Render a form for user preferences.
  - Call the backend `POST /recommendations` endpoint.
  - Display the list of recommended restaurants with scores and explanations.
  - Handle loading/error states gracefully.
- **Deployment**:
  - Dev: served via local dev server (e.g., Vite/CRA) pointing to the backend API.
  - Prod: deployed as static assets behind a CDN or as its own container, configured to talk to the backend API via environment-based base URL.

---

## 3. Project Structure

Suggested Python/FastAPI-based layout:

```text
ai-restaurant-recommender/
  ARCHITECTURE.md
  requirements.txt or pyproject.toml

  src/
    config/
      settings.py

    data_ingestion/
      hf_client.py
      schema_mapping.py
      ingest.py

    data_access/
      models.py
      repository.py

    recommendation/
      core_filtering.py
      scoring.py
      candidate_selector.py

    llm/
      llm_client.py
      prompts.py
      response_parser.py

    services/
      recommendation_service.py

    api/
      main.py
      schemas.py

    common/
      logging.py
      exceptions.py

    evaluation/
      offline_eval.py (or notebooks/)

  ui/
    package.json
    src/
      App.tsx (or App.jsx)
      components/
        PreferenceForm.tsx
        RecommendationList.tsx
    public/

  tests/
    test_data_ingestion.py
    test_recommendation.py
    test_llm_parser.py
    test_api.py
```

