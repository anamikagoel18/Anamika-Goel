from fastapi.testclient import TestClient

from src.api.main import app, get_recommendation_service
from src.data_access.repository import InMemoryRestaurantRepository
from src.domain.models import Recommendation, Restaurant, UserPreference
from src.services.recommendation_service import RecommendationService


class _FakeLlmClient:
    """
    Fake LLM client so API tests do not call the real Groq service.
    """

    def generate_recommendations(self, preferences, candidates):
        # Always return a single Recommendation for the top candidate
        if not candidates:
            return []
        top_restaurant, top_score = candidates[0]
        return [
            Recommendation(
                restaurant_id=top_restaurant.id,
                score=top_score,
                explanation="Fake explanation for testing.",
            )
        ]


def _build_test_service() -> RecommendationService:
    # Minimal in-memory restaurant list for the API test
    restaurants = [
        Restaurant(
            id="1",
            name="Budget Bites",
            cuisines=["North Indian", "Chinese"],
            city="Delhi",
            rating=4.0,
            average_cost_for_two=250,
        ),
        Restaurant(
            id="2",
            name="Some Other Place",
            cuisines=["Italian"],
            city="Delhi",
            rating=3.0,
            average_cost_for_two=400,
        ),
    ]
    repo = InMemoryRestaurantRepository(restaurants)
    fake_llm = _FakeLlmClient()
    return RecommendationService(repo, fake_llm)


def test_post_recommendations_endpoint_returns_expected_structure():
    # Override the dependency to use our test RecommendationService
    app.dependency_overrides[get_recommendation_service] = _build_test_service

    client = TestClient(app)

    payload = {
        "location": "Delhi",
        "cuisines": ["North Indian", "Chinese"],
        "min_rating": 3.5,
        "price_min": 100,
        "price_max": 600,
        "limit": 3,
    }

    response = client.post("/recommendations", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "preferences" in data
    assert "recommendations" in data
    assert len(data["recommendations"]) >= 1

    first = data["recommendations"][0]
    restaurant = first["restaurant"]

    assert restaurant["name"] == "Budget Bites"
    assert first["score"] > 0
    assert "explanation" in first
    assert "fake explanation" in first["explanation"].lower()

