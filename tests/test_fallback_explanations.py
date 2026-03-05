import sys
import os
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.getcwd())

from src.domain.models import Restaurant, UserPreference
from src.llm.llm_client import LlmClient

def test_fallback_explanation_template():
    print("\n--- Testing Dynamic Fallback Explanations (Phase 5) ---")
    
    # Setup
    preferences = UserPreference(
        location="Bangalore",
        area="Banashankari",
        cuisines=["Afghani"],
        min_rating=4.0,
        price_max=2000.0,
        limit=3
    )
    
    # Tier 10 candidate (City-wide Strict)
    restaurant = Restaurant(
        id="123",
        name="Gufha - The President Hotel",
        city="Bangalore",
        area="Jayanagar",
        cuisines=["Afghani", "North Indian"],
        rating=4.1,
        votes=1000,
        average_cost_for_two=1200
    )
    
    candidates = [(restaurant, 0.95, 10)] # Score 0.95, Tier 10
    
    llm = LlmClient()
    llm._client = MagicMock()
    
    # Mock LLM response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '{"recommendations": [{"restaurant_id": "123", "explanation": "It has excellent kebabs and authentic flavors."}]}'
    llm._client.chat.completions.create.return_value = mock_response
    
    recs = llm.generate_recommendations_v2(preferences, candidates)
    
    # Assertions
    assert len(recs) == 1
    exp = recs[0].explanation
    print(f"\nGenerated Explanation:\n{exp}")
    
    # Check for core template components
    assert "We couldn't find any restaurants with your selected cuisine and rating in your exact neighborhood" in exp
    assert "Gufha - The President Hotel" in exp
    assert "Afghani cuisine" in exp
    assert "rating of 4.1" in exp
    assert "fits within your budget" in exp
    assert "kebabs" in exp.lower() # LLM part
    
    print("\n[SUCCESS] Verified: Dynamic template correctly replaces all variables and merges with LLM content.")

if __name__ == "__main__":
    test_fallback_explanation_template()
