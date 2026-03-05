import sys
import os
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.getcwd())

from src.data_access.repository import InMemoryRestaurantRepository
from src.domain.models import Restaurant, UserPreference
from src.llm.llm_client import LlmClient
from src.services.recommendation_service import RecommendationService

def test_strict_cuisine_enforcement():
    print("\n--- Testing Strict Cuisine Enforcement (Phase 4) ---")
    
    # R1: Jayanagar (Other), Afghani, 4.1 (City-wide match - Tier 10)
    # R2: Banashankari (Local), South Indian, 4.7 (Local Favorite - Should NOT appear)
    
    restaurants = [
        Restaurant(id="1", name="Citywide Afghani Match", city="Bangalore", area="Jayanagar", cuisines=["Afghani"], rating=4.1, votes=100, average_cost_for_two=1000),
        Restaurant(id="2", name="Top-Rated Local Favorite", city="Bangalore", area="Banashankari", cuisines=["South Indian"], rating=4.7, votes=500, average_cost_for_two=100),
    ]
    
    # CASE 1: Specific Cuisine (Afghani)
    print("\n[Case 1] Search for 'Afghani' in Banashankari @ 4.0")
    prefs1 = UserPreference(
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
    mock_response.choices[0].message.content = '{"recommendations": [{"restaurant_id": "1", "explanation": "Direct match."}]}'
    llm._client.chat.completions.create.return_value = mock_response
    
    service = RecommendationService(repo, llm)
    recs1 = service.get_recommendations(prefs1)
    
    print("Results:")
    for i, rec in enumerate(recs1):
        rest = [r for r in restaurants if r.id == rec.restaurant_id][0]
        print(f"{i+1}. {rest.name} | Rating: {rest.rating} | Cuisines: {rest.cuisines}")

    # Assertion: ONLY Afghani match should be present. NO Local Favorite (South Indian).
    assert len(recs1) == 1, f"ERROR: Should only have 1 match. Got {len(recs1)}"
    assert recs1[0].restaurant_id == "1", "Wrong restaurant found."
    assert "searching across all of Bangalore" in recs1[0].explanation, "Tier 10 note missing."
    print("[SUCCESS] Verified: Strict cuisine mode excludes unrelated local favorites.")

    # CASE 2: No match at all (e.g. Ethiopian @ 4.9)
    print("\n[Case 2] Search for 'Ethiopian' in Banashankari @ 4.9")
    prefs2 = UserPreference(
        location="Bangalore",
        area="Banashankari",
        cuisines=["Ethiopian"],
        min_rating=4.9,
        limit=3
    )
    recs2 = service.get_recommendations(prefs2)
    print(f"Results count: {len(recs2)}")
    assert len(recs2) == 0, "ERROR: Should return 0 results."
    print("[SUCCESS] Verified: Strict mode returns 0 results if no match for cuisine + rating exists.")

    print("\nSUCCESS: Phase 4 Strict Cuisine Enforcement verified.")

if __name__ == "__main__":
    test_strict_cuisine_enforcement()
