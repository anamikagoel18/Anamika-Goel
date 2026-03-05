import sys
import os
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.getcwd())

from src.data_access.repository import InMemoryRestaurantRepository
from src.domain.models import Restaurant, UserPreference
from src.llm.llm_client import LlmClient
from src.services.recommendation_service import RecommendationService

def test_dynamic_fallback_explanation():
    print("\n--- Testing Dynamic Fallback Explanations (Phase 5) ---")
    
    # R1: Jayanagar (Other), Afghani, 4.1 (City-wide match - Tier 10)
    restaurants = [
        Restaurant(id="1", name="Gufha - The President Hotel", city="Bangalore", area="Jayanagar", cuisines=["Afghani"], rating=4.1, votes=100, average_cost_for_two=1200),
    ]
    
    # Search for 'Afghani' in Basavanagudi @ 2.9 (No match in neighborhood)
    prefs = UserPreference(
        location="Bangalore",
        area="Basavanagudi",
        cuisines=["Afghani"],
        min_rating=2.9,
        price_max=2000,
        limit=3
    )
    
    repo = InMemoryRestaurantRepository(restaurants)
    llm = LlmClient()
    llm._client = MagicMock()
    
    # Mock LLM response - even if LLM gives something else, we now force our template for Tier 10
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '{"recommendations": [{"restaurant_id": "1", "explanation": "It has great food."}]}'
    llm._client.chat.completions.create.return_value = mock_response
    
    service = RecommendationService(repo, llm)
    recs = service.get_recommendations(prefs)
    
    print(f"Results count: {len(recs)}")
    assert len(recs) == 1
    
    explanation = recs[0].explanation
    print(f"Generated Explanation:\n{explanation}")
    
    expected_start = "We couldn't find any restaurants with your selected cuisine and rating in your exact neighborhood, so we searched across Bangalore to find the best match."
    expected_mid = "We recommend Gufha - The President Hotel because it serves Afghani cuisine you prefer, has a strong rating of 4.1, and fits within your budget."
    
    assert expected_start in explanation
    assert "Gufha - The President Hotel" in explanation
    assert "Afghani" in explanation
    assert "4.1" in explanation
    assert explanation.strip().endswith("fits within your budget.")
    
    print("[SUCCESS] Verified: Dynamic fallback template is correctly populated and applied.")

if __name__ == "__main__":
    test_dynamic_fallback_explanation()
