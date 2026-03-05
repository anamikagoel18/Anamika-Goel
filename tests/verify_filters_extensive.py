
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

async def run_extensive_verification():
    print("=== EXTENSIVE FILTER VERIFICATION ===")
    
    # 1. Load Data
    print("Loading full dataset (limit 2000 for speed)...")
    restaurants = load_restaurants_from_hf(limit=2000)
    repo = InMemoryRestaurantRepository(restaurants)
    llm = MockLlmClient()
    service = RecommendationService(repo, llm)

    # 2. Test Cuisine Precision
    # Find an area and cuisine that definitely exists
    print("\n[TEST] Cuisine Precision")
    target_area = "Indiranagar"
    target_cuisine = "Chinese"
    
    prefs = UserPreference(location="Bangalore", area=target_area, cuisines=[target_cuisine], limit=10)
    recs = service.get_recommendations(prefs)
    
    match_count = 0
    for rec in recs:
        res = next(r for r in restaurants if r.id == rec.restaurant_id)
        is_match = target_cuisine.lower() in [c.lower() for c in res.cuisines]
        if is_match:
            match_count += 1
            print(f"  - Match found: {res.name} ({res.area})")
        
    if llm.last_relaxation == "none":
        assert match_count > 0, f"Error: No {target_cuisine} found in {target_area} despite no relaxation."
        print(f"SUCCESS: Found {match_count} direct cuisine matches in {target_area}.")
    else:
        print(f"INFO: Relaxation triggered ({llm.last_relaxation}). This is expected if the first 2000 rows don't have matching data.")

    # 3. Test Rating Constraint
    print("\n[TEST] Rating Constraint (min_rating=4.5)")
    prefs_rating = UserPreference(location="Bangalore", min_rating=4.5, limit=5)
    recs_rating = service.get_recommendations(prefs_rating)
    
    if llm.last_relaxation == "none":
        for rec in recs_rating:
            res = next(r for r in restaurants if r.id == rec.restaurant_id)
            assert res.rating >= 4.5, f"Error: Restaurant {res.name} has rating {res.rating} < 4.5"
        print("SUCCESS: All results honor the 4.5+ rating constraint.")
    else:
        print(f"INFO: Rating relaxation triggered ({llm.last_relaxation}).")

    # 4. Test Price Accuracy
    print("\n[TEST] Price Range Accuracy (max=500)")
    prefs_price = UserPreference(location="Bangalore", price_max=500, limit=5)
    recs_price = service.get_recommendations(prefs_price)
    
    if llm.last_relaxation == "none":
        for rec in recs_price:
            res = next(r for r in restaurants if r.id == rec.restaurant_id)
            assert res.average_cost_for_two <= 500, f"Error: Restaurant {res.name} cost {res.average_cost_for_two} > 500"
        print("SUCCESS: All results honor the <= 500 price constraint.")
    else:
        print(f"INFO: Price relaxation triggered ({llm.last_relaxation}).")

    # 5. Check Area Granularity
    areas = sorted(list(set(r.area for r in restaurants if r.area)))
    print(f"\n[INFO] Neighborhod/Area options available: {len(areas)}")
    assert len(areas) > 5, "Fewer than 5 areas found, mapping might still be too broad!"
    print(f"Sample areas: {areas[:5]}")

    print("\n=== VERIFICATION COMPLETE ===")

if __name__ == "__main__":
    asyncio.run(run_extensive_verification())
