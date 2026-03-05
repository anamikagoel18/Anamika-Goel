from __future__ import annotations

from typing import Dict, List

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.schemas import (
    PreferenceRequest,
    RecommendationResponse,
    RecommendationResponseItem,
    RestaurantResponse,
)
from src.data_access.repository import InMemoryRestaurantRepository
from src.data_ingestion.ingest import ingest_from_iterable
from src.data_ingestion.hf_client import load_restaurants_from_hf
from src.domain.models import UserPreference
from src.llm.llm_client import LlmClient
from src.services.recommendation_service import RecommendationService

app = FastAPI(title="AI Restaurant Recommendation Service")

# Allow the React dev server (localhost:5173) to call this API during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _sample_raw_records() -> List[Dict]:
    """
    For now, we use the same hard-coded sample data as earlier phases.
    Later this can be replaced by a proper data store.
    """
    return [
        {
            "Restaurant ID": 1,
            "Restaurant Name": "Budget Bites",
            "City": "Delhi",
            "Cuisines": "North Indian, Chinese",
            "Aggregate rating": 4.0,
            "Average Cost for two": 250,
            "Votes": 100,
        },
        {
            "Restaurant ID": 2,
            "Restaurant Name": "Midrange Meals",
            "City": "Delhi",
            "Cuisines": "Italian",
            "Aggregate rating": 3.5,
            "Average Cost for two": 500,
            "Votes": 50,
        },
        {
            "Restaurant ID": 3,
            "Restaurant Name": "Premium Plates",
            "City": "Mumbai",
            "Cuisines": "Continental",
            "Aggregate rating": 4.5,
            "Average Cost for two": 900,
            "Votes": 200,
        },
    ]


# Simple, in-memory repository for now.
# Load the full dataset (now cached locally for speed)
# Use force_refresh=True once to apply the new granular area mapping
_restaurants = load_restaurants_from_hf(limit=None, force_refresh=True)
if not _restaurants:
    raise RuntimeError("Failed to load any restaurants from Hugging Face Zomato dataset.")

_repo = InMemoryRestaurantRepository(_restaurants)
_llm_client = LlmClient()
_service = RecommendationService(_repo, _llm_client)


def get_recommendation_service() -> RecommendationService:
    """
    Dependency injection hook so tests can override the service.
    """
    return _service


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/cities", response_model=List[str])
def list_cities(
    service: RecommendationService = Depends(get_recommendation_service),
) -> List[str]:
    """
    Return the list of unique areas (neighborhoods) from the loaded restaurant data.
    """
    # In this Bangalore dataset, 'area' contains the 30+ neighborhoods like Indiranagar, HSR, etc.
    areas = sorted({(r.area or "").strip() for r in service.list_restaurants() if r.area})
    return areas


@app.get("/cuisines", response_model=List[str])
def list_cuisines(
    service: RecommendationService = Depends(get_recommendation_service),
) -> List[str]:
    """
    Return the list of unique cuisine names from the loaded restaurant data.
    """
    all_cuisines = set()
    for r in service.list_restaurants():
        for c in r.cuisines:
            clean_c = c.strip()
            if clean_c:
                all_cuisines.add(clean_c)
    result = sorted(list(all_cuisines))
    print(f"DEBUG: Serving {len(result)} unique cuisines.")
    return result


@app.post("/recommendations", response_model=RecommendationResponse)
def create_recommendations(
    request: PreferenceRequest,
    service: RecommendationService = Depends(get_recommendation_service),
) -> RecommendationResponse:
    # Convert request schema into domain-level UserPreference
    prefs = UserPreference(
        location=request.location,
        area=request.area,
        price_min=request.price_min,
        price_max=request.price_max,
        price_band=request.price_band,
        min_rating=request.min_rating,
        cuisines=request.cuisines,
        limit=request.limit or 5,
    )

    recommendations = service.get_recommendations(prefs)

    # Map restaurant_id back to full restaurant info using the same repository
    # that the service was constructed with (important for tests and DI).
    restaurant_by_id = {r.id: r for r in service.list_restaurants()}

    response_items: List[RecommendationResponseItem] = []
    for rec in recommendations:
        restaurant = restaurant_by_id.get(rec.restaurant_id)
        if not restaurant:
            continue
        response_items.append(
            RecommendationResponseItem(
                restaurant=RestaurantResponse(
                    id=restaurant.id,
                    name=restaurant.name,
                    city=restaurant.city,
                    area=restaurant.area,
                    rating=restaurant.rating,
                    price_band=restaurant.price_band,
                    average_cost_for_two=restaurant.average_cost_for_two,
                    cuisines=restaurant.cuisines,
                ),
                score=rec.score,
                explanation=rec.explanation,
            )
        )

    return RecommendationResponse(preferences=request, recommendations=response_items)

