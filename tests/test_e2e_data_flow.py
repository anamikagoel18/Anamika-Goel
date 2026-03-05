import pytest
from src.data_ingestion.hf_client import load_restaurants_from_hf
from src.services.recommendation_service import RecommendationService
from src.domain.models import UserPreference
from src.llm.llm_client import LlmClient
import os

@pytest.mark.asyncio
async def test_e2e_data_and_filtering():
    """
    End-to-end test for data ingestion and filtering logic.
    - Loads 20,000 records from HF.
    - Verifies record count and diversity.
    - Verifies filtering logic.
    """
    # 1. Ingest Data (Limit 20k as per last request)
    print("\n[E2E] Loading 20,000 records from Hugging Face...")
    restaurants = load_restaurants_from_hf(limit=20000)
    
    # 2. Verify Count & Deduplication
    print(f"[E2E] Total restaurants loaded: {len(restaurants)}")
    assert len(restaurants) > 10000, "Should have loaded a significant amount of data"
    
    # Check for duplicates based on ID
    ids = [r.id for r in restaurants]
    assert len(ids) == len(set(ids)), "Deduplication failed: Duplicate IDs found in ingested data"
    
    # 3. Verify Diversity (Bangalore Context)
    cities = set(r.city for r in restaurants)
    print(f"[E2E] Cities present: {cities}")
    # We expect Bangalore/Bengaluru and maybe others if the dataset has them
    assert any("Bangalore" in c or "Bengaluru" in c or "BTM" in c or "HSR" in c for c in cities), "Bangalore data missing"
    
    areas = set(r.area for r in restaurants if r.area)
    print(f"[E2E] Sample Areas: {list(areas)[:10]}")
    assert len(areas) > 5, "Should have multiple areas represented"
    
    # 4. Verify Filtering Logic in RecommendationService
    # We use a fake client to avoid LLM costs during data filtering test
    class FakeLlmClient(LlmClient):
        def __init__(self, *args, **kwargs):
            # Don't call super() to avoid Groq initialization
            self._model = "fake"
            pass

        def generate_recommendations(self, prefs, candidates):
            # Just return IDs of first 3 candidates
            from src.domain.models import Recommendation
            return [Recommendation(restaurant_id=c.id, score=score, explanation="Top match") for c, score in candidates[:3]]

    from src.data_access.repository import InMemoryRestaurantRepository
    repo = InMemoryRestaurantRepository(restaurants)
    service = RecommendationService(repo, FakeLlmClient())
    
    # Test Location Filter
    # Let's find a city that exists in the data
    valid_city = list(cities)[0]
    prefs = UserPreference(location=valid_city, cuisines=[], limit=5)
    recs = service.get_recommendations(prefs)
    assert len(recs) <= 5
    for rec in recs:
        res = next(r for r in restaurants if r.id == rec.restaurant_id)
        assert valid_city.lower() in res.city.lower()
        
    # Test Rating Filter
    prefs_rating = UserPreference(location=valid_city, min_rating=4.5, limit=5)
    recs_rating = service.get_recommendations(prefs_rating)
    for rec in recs_rating:
        res = next(r for r in restaurants if r.id == rec.restaurant_id)
        assert res.rating >= 4.5
        
    print("[E2E] Backend data and filtering verified successfully!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_e2e_data_and_filtering())
