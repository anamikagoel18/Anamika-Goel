
import asyncio
import os
import sys

# Ensure src is in python path
sys.path.append(os.getcwd())

from src.domain.models import Restaurant, UserPreference, Recommendation
from src.services.recommendation_service import RecommendationService
from src.data_access.repository import InMemoryRestaurantRepository
from src.llm.llm_client import LlmClient

class MockLlmClient(LlmClient):
    def __init__(self):
        self.last_relaxation_level = None
        self.last_candidates_count = 0
        self.model = "mock"

    def generate_recommendations(self, preferences, candidates, relaxation_level="none"):
        self.last_relaxation_level = relaxation_level
        self.last_candidates_count = len(candidates)
        # Mock actual recommendation objects
        return [
            Recommendation(
                restaurant_id=r.id,
                score=score,
                explanation=f"Delicious {r.cuisines[0]} in {r.area}"
            )
            for r, score in candidates[:preferences.limit]
        ]

def create_sample_data():
    return [
        Restaurant(
            id="1", name="Res A", cuisines=["Chinese"], city="Bangalore", area="Indiranagar",
            average_cost_for_two=500.0, price_band="moderate", rating=4.5, votes=100
        ),
        Restaurant(
            id="2", name="Res B", cuisines=["Italian"], city="Bangalore", area="Indiranagar",
            average_cost_for_two=1200.0, price_band="expensive", rating=4.2, votes=80
        ),
        Restaurant(
            id="3", name="Res C", cuisines=["Chinese"], city="Bangalore", area="Koramangala",
            average_cost_for_two=300.0, price_band="cheap", rating=3.8, votes=50
        ),
        Restaurant(
            id="4", name="Res D", cuisines=["Indian"], city="Bangalore", area="Indiranagar",
            average_cost_for_two=400.0, price_band="moderate", rating=4.8, votes=200
        ),
    ]

async def run_verification():
    print("--- Starting Filter Verification ---")
    data = create_sample_data()
    repo = InMemoryRestaurantRepository(data)
    llm = MockLlmClient()
    service = RecommendationService(repo, llm)

    # 1. TEST: Strict Cuisine & Area
    print("\nTEST 1: Strict Cuisine (Chinese) & Area (Indiranagar)")
    prefs = UserPreference(location="Bangalore", area="Indiranagar", cuisines=["Chinese"], limit=5)
    recs = service.get_recommendations(prefs)
    assert len(recs) == 1
    assert recs[0].restaurant_id == "1"
    assert llm.last_relaxation_level == "none"
    print("SUCCESS: Found exact match (Res A)")

    # 2. TEST: Minimum Rating
    print("\nTEST 2: Minimum Rating (4.5) in Indiranagar")
    prefs = UserPreference(location="Indiranagar", min_rating=4.5, limit=5)
    recs = service.get_recommendations(prefs)
    assert len(recs) == 2 # Res A (4.5) and Res D (4.8)
    r_ids = [r.restaurant_id for r in recs]
    assert "1" in r_ids and "4" in r_ids
    assert llm.last_relaxation_level == "none"
    print("SUCCESS: Found exact matches for rating")

    # 3. TEST: Price Range
    print("\nTEST 3: Price Range (100-400) in Bangalore")
    prefs = UserPreference(location="Bangalore", price_min=100, price_max=400, limit=5)
    recs = service.get_recommendations(prefs)
    assert len(recs) == 2 # Res C (300) and Res D (400)
    r_ids = [r.restaurant_id for r in recs]
    assert "3" in r_ids and "4" in r_ids
    print("SUCCESS: Found exact matches for price range")

    # 4. TEST: Tiered Relaxation - Price
    # Chinese in Indiranagar with price max 200 (none exist, Res A is 500)
    # Tier 2 should relax price to 200 * 1.5 = 300 (still none)
    # Actually Tier 2 relaxes by factor 1.5. If price_max=400, it becomes 600.
    print("\nTEST 4: Tiered Relaxation - Price (Chinese, Indiranagar, Price Max 400)")
    # Res A is Chinese, Indiranagar, Price 500. So Price Max 400 fails strict.
    # Relaxed Price Max 400 * 1.5 = 600. Res A (500) now matches!
    prefs = UserPreference(location="Indiranagar", cuisines=["Chinese"], price_max=400, limit=5)
    recs = service.get_recommendations(prefs)
    assert len(recs) == 1
    assert recs[0].restaurant_id == "1"
    assert llm.last_relaxation_level == "price"
    print("SUCCESS: Price relaxation worked")

    # 5. TEST: Tiered Relaxation - Rating
    # Chinese, Indiranagar, Price Max 400, Rating 5.0
    # Tier 1 Strict: Fails (Res A is 500, Rating 4.5)
    # Tier 2 Relax Price (600): Res A matches price (500) but fails rating (4.5 < 5.0)
    # Tier 3 Relax Rating (5.0 - 0.5 = 4.5): Res A now matches!
    print("\nTEST 5: Tiered Relaxation - Rating (Chinese, Indiranagar, Price Max 400, Rating 5.0)")
    prefs = UserPreference(location="Indiranagar", cuisines=["Chinese"], price_max=400, min_rating=5.0, limit=5)
    recs = service.get_recommendations(prefs)
    assert len(recs) == 1
    assert recs[0].restaurant_id == "1"
    assert llm.last_relaxation_level == "rating"
    print("SUCCESS: Rating relaxation worked")

    # 6. TEST: Tiered Relaxation - Neighborhood Fallback
    # Ethiopian in Indiranagar (No Ethiopian exists)
    print("\nTEST 6: Neighborhood Fallback (Ethiopian, Indiranagar)")
    prefs = UserPreference(location="Indiranagar", cuisines=["Ethiopian"], limit=5)
    recs = service.get_recommendations(prefs)
    assert len(recs) > 0
    assert llm.last_relaxation_level == "neighborhood"
    # Should find Res A, B, D because they are in Indiranagar
    print("SUCCESS: Neighborhood fallback worked")

    print("\nAll Backend Filter Verifications Passed!")

if __name__ == "__main__":
    asyncio.run(run_verification())
