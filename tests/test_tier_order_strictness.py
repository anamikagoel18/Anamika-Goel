import sys
import os
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.getcwd())

from src.data_access.repository import InMemoryRestaurantRepository
from src.domain.models import Restaurant, UserPreference
from src.llm.llm_client import LlmClient
from src.services.recommendation_service import RecommendationService

def test_tier_order_strictness():
    print("\n--- Testing Tier Order Strictness (Phase 3) ---")
    
    # R1: Jayanagar (Other), Afghani, 4.1 (City-wide match - Tier 4)
    # R2: Banashankari (Local), South Indian, 4.7 (Local Favorite - Tier 6)
    
    restaurants = [
        Restaurant(id="1", name="Citywide Afghani Match", city="Bangalore", area="Jayanagar", cuisines=["Afghani"], rating=4.1, votes=100, average_cost_for_two=1000),
        Restaurant(id="2", name="Top-Rated Local Favorite", city="Bangalore", area="Banashankari", cuisines=["South Indian"], rating=4.7, votes=500, average_cost_for_two=100),
    ]
    
    # User Preferences: Banashankari, Afghani, Min 4.0
    prefs = UserPreference(
        location="Bangalore",
        area="Banashankari",
        cuisines=["Afghani"],
        min_rating=4.0,
        limit=3
    )
    
    repo = InMemoryRestaurantRepository(restaurants)
    llm = LlmClient()
    llm._client = MagicMock()
    
    # Mock LLM response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '{"recommendations": [{"restaurant_id": "1", "explanation": "Direct match."}, {"restaurant_id": "2", "explanation": "Local fav."}]}'
    llm._client.chat.completions.create.return_value = mock_response
    
    service = RecommendationService(repo, llm)
    recs = service.get_recommendations(prefs)
    
    print("\nOrder received:")
    for i, rec in enumerate(recs):
        rest = [r for r in restaurants if r.id == rec.restaurant_id][0]
        print(f"{i+1}. {rest.name} | Rating: {rest.rating} | Explanation Start: {rec.explanation[:80]}...")

    # Assertions
    # Result #1 MUST be Citywide Afghani (Tier 4) even though it has lower rating (4.1 vs 4.7)
    assert recs[0].restaurant_id == "1", f"ERROR: City-wide match should be first. Got {recs[0].restaurant_id}"
    assert "searching across all of Bangalore" in recs[0].explanation, "Tier 4 note missing."
    
    # Result #2 MUST be Local Favorite (Tier 6)
    assert recs[1].restaurant_id == "2", "Local favorite should be second."
    assert "top-rated local favorite" in recs[1].explanation, "Tier 6 note missing."
    
    print("\nSUCCESS: Phase 3 Tier Order & Per-Candidate Notes verified.")

if __name__ == "__main__":
    test_tier_order_strictness()
