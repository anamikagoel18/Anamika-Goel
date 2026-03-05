import sys
import os
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.getcwd())

from src.data_access.repository import InMemoryRestaurantRepository
from src.domain.models import Restaurant, UserPreference
from src.llm.llm_client import LlmClient
from src.services.recommendation_service import RecommendationService

def test_contextual_fallback():
    print("\n--- Testing Contextual Fallback Messages (Phase 6) ---")
    
    # R1: Local Match (CV Raman Nagar)
    # R2: City-wide Match (Jayanagar)
    restaurants = [
        Restaurant(id="1", name="Local Andhra Spot", city="Bangalore", area="CV Raman Nagar", cuisines=["Andhra"], rating=3.7, votes=100, average_cost_for_two=300),
        Restaurant(id="2", name="Citywide Andhra Gem", city="Bangalore", area="Jayanagar", cuisines=["Andhra"], rating=4.4, votes=500, average_cost_for_two=800),
    ]
    
    repo = InMemoryRestaurantRepository(restaurants)
    llm = LlmClient()
    llm._client = MagicMock()
    
    # CASE 1: With Local Matches
    print("\n[Case 1] Some local matches present. Expecting 'supplementary' prefix.")
    prefs1 = UserPreference(
        location="Bangalore",
        area="CV Raman Nagar",
        cuisines=["Andhra"],
        min_rating=2.5,
        limit=3
    )
    
    # Mock LLM for Case 1
    mock_resp1 = MagicMock()
    mock_resp1.choices = [MagicMock()]
    mock_resp1.choices[0].message.content = '{"recommendations": [{"restaurant_id": "1", "explanation": "Local."}, {"restaurant_id": "2", "explanation": "Citywide."}]}'
    llm._client.chat.completions.create.return_value = mock_resp1
    
    service = RecommendationService(repo, llm)
    recs1 = service.get_recommendations(prefs1)
    
    # Find the city-wide recommendation (Restaurant 2)
    city_rec = [r for r in recs1 if r.restaurant_id == "2"][0]
    print(f"City-wide Explanation:\n{city_rec.explanation}")
    
    assert "To give you more top-rated options beyond your neighborhood" in city_rec.explanation
    assert "We couldn't find any" not in city_rec.explanation
    print("[SUCCESS] Verified Template B (Supplementary) for Mixed Results.")

    # CASE 2: No Local Matches
    print("\n[Case 2] No local matches. Expecting 'couldn't find any' prefix.")
    # Search in a different area where no Andhra restaurants exist
    prefs2 = UserPreference(
        location="Bangalore",
        area="Indiranagar", # No Andhra matches in our mock data for Indiranagar
        cuisines=["Andhra"],
        min_rating=2.5,
        limit=3
    )
    
    # Mock LLM for Case 2
    mock_resp2 = MagicMock()
    mock_resp2.choices = [MagicMock()]
    mock_resp2.choices[0].message.content = '{"recommendations": [{"restaurant_id": "2", "explanation": "Citywide only."}]}'
    llm._client.chat.completions.create.return_value = mock_resp2
    
    recs2 = service.get_recommendations(prefs2)
    
    city_rec2 = recs2[0]
    print(f"City-wide Explanation:\n{city_rec2.explanation}")
    
    assert "We couldn't find any restaurants with your selected cuisine and rating in your exact neighborhood" in city_rec2.explanation
    assert "To give you more top-rated options" not in city_rec2.explanation
    print("[SUCCESS] Verified Template A (No Local) for Pure City-wide results.")

if __name__ == "__main__":
    test_contextual_fallback()
