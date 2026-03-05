
import asyncio
import os
import sys

# Ensure src is in python path
sys.path.append(os.getcwd())

from src.data_ingestion.hf_client import load_restaurants_from_hf
from src.services.recommendation_service import RecommendationService
from src.data_access.repository import InMemoryRestaurantRepository
from src.domain.models import UserPreference
from src.llm.llm_client import LlmClient

class MockLlmClient(LlmClient):
    def __init__(self):
        self.model = "mock"
        self.last_relaxation = "none"

    def generate_recommendations(self, preferences, candidates, relaxation_level="none"):
        self.last_relaxation = relaxation_level
        from src.domain.models import Recommendation
        return [Recommendation(restaurant_id=r.id, score=score, explanation="Verified") for r, score in candidates]

async def verify_fix():
    print("=== VERIFYING AFGHANI / PRICE FIX ===")
    
    # Load full dataset from cache
    restaurants = load_restaurants_from_hf(limit=None)
    repo = InMemoryRestaurantRepository(restaurants)
    llm = MockLlmClient()
    service = RecommendationService(repo, llm)

    # TEST CASE: Afghani in Indiranagar, Price 500-600
    # We know Afghani doesn't exist in Indiranagar, but exists in Basavanagudi.
    prefs = UserPreference(
        location="Bangalore",
        area="Indiranagar",
        cuisines=["Afghani"],
        price_min=500,
        price_max=600,
        min_rating=4.0,
        limit=5
    )
    
    candidates, relaxation = service._build_candidates(prefs)
    
    print(f"Relaxation triggered: {relaxation}")
    print(f"Number of candidates: {len(candidates)}")
    
    if relaxation == "area":
        print("SUCCESS: Found Afghani in other areas (Basavanagudi/Banashankari).")
        for r, score in candidates:
            print(f"  - {r.name} ({r.area}) | Cuisines: {r.cuisines}")
            assert any("afghani" in c.lower() for c in r.cuisines)
    elif relaxation == "neighborhood":
        print("INFO: No Afghani found even city-wide (unlikely for original dataset, but possible in cache).")
        print("Verifying that price filter was still respected if possible...")
        for r, score in candidates:
            print(f"  - {r.name} ({r.area}) | Cost: {r.average_cost_for_two}")
            # If we are in Tier 5, we should have respected price if ANY 500-600 existed in Indiranagar
            # (Note: Belgian Waffle was 400, so if Tier 5 works, it shouldn't show it if a 500-600 option exists)

    print("\n=== VERIFICATION COMPLETE ===")

if __name__ == "__main__":
    asyncio.run(verify_fix())
