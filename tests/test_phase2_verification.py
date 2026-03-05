import sys
import os
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.getcwd())

from src.data_access.repository import InMemoryRestaurantRepository
from src.domain.models import Restaurant, UserPreference
from src.llm.llm_client import LlmClient
from src.services.recommendation_service import RecommendationService

def test_rating_strictness():
    print("\n--- Testing Rating Strictness & Hierarchy Priority (Phase 2) ---")
    
    # R1: Banaswadi, Afghani, 3.8 rating (Exact cuisine match, but low rating)
    # R2: Jayanagar, Afghani, 4.1 rating (City-wide match)
    # R3: Banaswadi, Italian, 4.5 rating (Local favorite, non-cuisine match)
    # R4: Bangalore, Any, 4.6 rating (Global favorite)
    
    restaurants = [
        Restaurant(id="1", name="Low-Rated Afghani", city="Bangalore", area="Banaswadi", cuisines=["Afghani"], rating=3.8, votes=100, average_cost_for_two=1000),
        Restaurant(id="2", name="Strict Afghani Citywide", city="Bangalore", area="Jayanagar", cuisines=["Afghani"], rating=4.1, votes=200, average_cost_for_two=1200),
        Restaurant(id="3", name="High-Rated Local Favorite", city="Bangalore", area="Banaswadi", cuisines=["Italian"], rating=4.5, votes=500, average_cost_for_two=1500),
        Restaurant(id="4", name="Elite Global Favorite", city="Bangalore", area="Indiranagar", cuisines=["North Indian"], rating=4.8, votes=1000, average_cost_for_two=1800),
    ]
    
    # User Preferences: Banaswadi, Afghani, Min 4.1
    prefs = UserPreference(
        location="Bangalore",
        area="Banaswadi",
        cuisines=["Afghani"],
        min_rating=4.1,
        limit=3
    )
    
    repo = InMemoryRestaurantRepository(restaurants)
    # Mock LLM to return dummy data that we can check for uniqueness
    llm = LlmClient()
    llm._client = MagicMock()
    
    # Simulate LLM response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = (
        '{"recommendations": ['
        '{"restaurant_id": "2", "explanation": "This fits your Afghani craving and matches your 4.1 rating."},'
        '{"restaurant_id": "3", "explanation": "This fits your Afghani craving and matches your 4.1 rating."},'
        '{"restaurant_id": "4", "explanation": "This fits your Afghani craving and matches your 4.1 rating."}'
        ']}'
    )
    llm._client.chat.completions.create.return_value = mock_response
    
    service = RecommendationService(repo, llm)
    
    recs = service.get_recommendations(prefs)
    
    print("\nRecommendations received:")
    for i, rec in enumerate(recs):
        rest = repo.get_all()[0] # Dummmy find
        for r in restaurants:
            if r.id == rec.restaurant_id:
                rest = r
        print(f"{i+1}. {rest.name} | Rating: {rest.rating} | Explanation: {rec.explanation[:100]}...")

    # Assertions
    ids = [r.restaurant_id for r in recs]
    
    # 1. Low-Rated Afghani (3.8) should NOT be in the top 3 because 4.1+ alternatives exist.
    assert "1" not in ids, "ERROR: Low-rated restaurant (3.8) included despite 4.1+ alternatives available."
    
    # 2. Strict Afghani Citywide (4.1) should be included (matches cuisine + rating).
    assert "2" in ids, "Strict Afghani Citywide (4.1) should be found."
    
    # 3. High-Rated Local Favorite (4.5) should be included (matches area + rating, higher priority than low-rated cuisine).
    assert "3" in ids, "High-Rated Local Favorite (4.5) should be found as fallback."
    
    # 4. Elite Global Favorite (4.8) should be included.
    assert "4" in ids, "Elite Global Favorite (4.8) should be found."
    
    # 5. Explanations should be unique (Uniqueness check in LlmClient)
    exps = [r.explanation for r in recs]
    assert len(set(exps)) == len(exps), "ERROR: Duplicate explanations found across different restaurants."
    
    print("\nSUCCESS: Phase 2 Hierarchy & Uniqueness verified.")

if __name__ == "__main__":
    test_rating_strictness()
