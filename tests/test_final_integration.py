import sys
import os
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.getcwd())

from src.data_access.repository import InMemoryRestaurantRepository
from src.domain.models import Restaurant, UserPreference
from src.llm.llm_client import LlmClient
from src.services.recommendation_service import RecommendationService

def setup_test_service(restaurants):
    repo = InMemoryRestaurantRepository(restaurants)
    llm = LlmClient()
    llm._client = MagicMock()
    
    # helper to mock LLM responses
    def mock_llm_response(text):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = f'{{"recommendations": [{{"restaurant_id": "any", "explanation": "{text}"}}]}}'
        llm._client.chat.completions.create.return_value = mock_response

    return RecommendationService(repo, llm), llm

def test_final_integration_suite():
    print("\n================ FINAL INTEGRATION TEST SUITE ================")
    
    # TEST DATA
    # R1: Local Afghani Strict (Banashankari, Afghani, 1000, 4.2)
    # R2: Local Afghani Price-Relaxed (Banashankari, Afghani, 1500, 4.3)
    # R3: City-wide Afghani (Indiranagar, Afghani, 1200, 4.5)
    # R4: Local South Indian (Banashankari, South Indian, 100, 4.7)
    
    restaurants = [
        Restaurant(id="R1", name="Local Afghani Strict", city="Bangalore", area="Banashankari", cuisines=["Afghani"], rating=4.2, votes=100, average_cost_for_two=1000),
        Restaurant(id="R2", name="Local Afghani Relaxed Price", city="Bangalore", area="Banashankari", cuisines=["Afghani"], rating=4.3, votes=150, average_cost_for_two=1500),
        Restaurant(id="R3", name="Citywide Afghani Match", city="Bangalore", area="Indiranagar", cuisines=["Afghani"], rating=4.5, votes=200, average_cost_for_two=1200),
        Restaurant(id="R4", name="Top Local South Indian", city="Bangalore", area="Banashankari", cuisines=["South Indian"], rating=4.7, votes=500, average_cost_for_two=100)
    ]

    service, llm = setup_test_service(restaurants)

    # --- SCENARIO 1: Strict Local Match ---
    print("\n[Scenario 1] Search Afghani in Banashankari @ 4.0, Budget 1100")
    # Should find R1 only as Tier 0
    p1 = UserPreference(location="Bangalore", area="Banashankari", cuisines=["Afghani"], min_rating=4.0, price_max=1100, limit=3)
    
    # Mock LLM to return explanation for R1
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock()]
    mock_resp.choices[0].message.content = '{"recommendations": [{"restaurant_id": "R1", "explanation": "Perfect neighborhood spot."}]}'
    llm._client.chat.completions.create.return_value = mock_resp
    
    recs1 = service.get_recommendations(p1)
    assert len(recs1) == 1
    assert recs1[0].restaurant_id == "R1"
    assert "Note:" not in recs1[0].explanation, "Tier 0 should not have relaxation notes."
    print("SUCCESS: Strict local match found correctly.")

    # --- SCENARIO 2: Price Relaxation (Tier 1) ---
    print("\n[Scenario 2] Search Afghani in Banashankari @ 4.0, Budget 900")
    # R1 (1000) is > 900. But 1.5x budget (1350) covers R1. 
    # So R1 should be found as Tier 1.
    p2 = UserPreference(location="Bangalore", area="Banashankari", cuisines=["Afghani"], min_rating=4.0, price_max=900, limit=3)
    
    # Mock LLM
    mock_resp.choices[0].message.content = '{"recommendations": [{"restaurant_id": "R1", "explanation": "Worth the extra cost."}]}'
    
    recs2 = service.get_recommendations(p2)
    assert len(recs2) == 1
    assert recs2[0].restaurant_id == "R1"
    assert "slightly relaxed your price range" in recs2[0].explanation, "Tier 1 note missing."
    print("SUCCESS: Local price relaxation verified.")

    # --- SCENARIO 3: City-wide Expansion + Dynamic Template (Tier 10) ---
    print("\n[Scenario 3] Search Afghani in Hebbal @ 4.0, Budget 2000")
    # No Afghani in Hebbal. R1/R2/R3 are in Banashankari/Indiranagar.
    # Should search across Bangalore and find R3 (highest rated Afghani).
    p3 = UserPreference(location="Bangalore", area="Hebbal", cuisines=["Afghani"], min_rating=4.0, price_max=2000, limit=3)
    
    # Mock LLM for R3
    mock_resp.choices[0].message.content = '{"recommendations": [{"restaurant_id": "R3", "explanation": "Best authentic Afghani in town."}]}'
    
    recs3 = service.get_recommendations(p3)
    assert len(recs3) >= 1
    assert recs3[0].restaurant_id == "R3"
    assert "searched across Bangalore to find the best match" in recs3[0].explanation, "Dynamic template note missing."
    assert "Gey we recommend Citywide Afghani Match" # wait name is different
    assert "Citywide Afghani Match" in recs3[0].explanation
    assert "Afghani cuisine" in recs3[0].explanation
    assert "rating of 4.5" in recs3[0].explanation
    print("SUCCESS: City-wide expansion with dynamic template verified.")

    # --- SCENARIO 4: All Cuisines Mode (Broad) ---
    print("\n[Scenario 4] Search 'All Cuisines' in Banashankari @ 4.5, Budget 200")
    # R4 (South Indian, 4.7) is in Banashankari and fits budget/rating.
    p4 = UserPreference(location="Bangalore", area="Banashankari", cuisines=[], min_rating=4.5, price_max=200, limit=3)
    
    # Mock LLM for R4
    mock_resp.choices[0].message.content = '{"recommendations": [{"restaurant_id": "R4", "explanation": "Legendary breakfast spot."}]}'
    
    recs4 = service.get_recommendations(p4)
    assert len(recs4) >= 1
    assert recs4[0].restaurant_id == "R4"
    print("SUCCESS: Broad discovery mode verified.")

    # --- SCENARIO 5: Strict No-Match ---
    print("\n[Scenario 5] Search 'Ethiopian' @ 4.9")
    # No Ethiopian in DB.
    p5 = UserPreference(location="Bangalore", area="Banashankari", cuisines=["Ethiopian"], min_rating=4.9, price_max=2000, limit=3)
    
    recs5 = service.get_recommendations(p5)
    assert len(recs5) == 0, f"Expected 0 results, got {len(recs5)}"
    print("SUCCESS: Strict no-match correctly returns empty list.")

    print("\n================ ALL FINAL INTEGRATION TESTS PASSED ================")

if __name__ == "__main__":
    try:
        test_final_integration_suite()
    except Exception as e:
        print(f"\n[FAILURE] Integration tests failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
