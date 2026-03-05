import sys
import os
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.getcwd())

from src.data_access.repository import InMemoryRestaurantRepository
from src.data_ingestion.hf_client import load_restaurants_from_hf
from src.domain.models import UserPreference
from src.llm.llm_client import LlmClient
from src.services.recommendation_service import RecommendationService

def reproduce_issue():
    print("\n--- Reproducing Banashankari + Afghani Transparency Issue ---")
    
    # Load real data
    restaurants = load_restaurants_from_hf(limit=None)
    repo = InMemoryRestaurantRepository(restaurants)
    
    # Force a failure in the internal LLM call to trigger the internal fallback logic
    llm_client = LlmClient()
    # Mocking the client and the chat completion
    llm_client._client = MagicMock()
    llm_client._client.chat.completions.create.side_effect = Exception("Simulated API Error")
    
    service = RecommendationService(repo, llm_client)
    
    prefs = UserPreference(
        location="Bangalore",
        area="Banashankari", # User's context
        cuisines=["Afghani"],
        min_rating=4.1,
        price_max=2000.0,
        limit=3
    )
    
    candidates, level = service._build_candidates(prefs)
    print(f"Relaxation Level reached: {level}")
    print(f"Candidates found: {len(candidates)}")
    for r, score in candidates:
        print(f"- {r.name} | Rating: {r.rating} | Area: {r.area}")

    recs = service.get_recommendations(prefs)
    
    print(f"\nFinal Recommendations ({len(recs)} total):")
    for rec in recs:
        print(f"- Restaurant ID: {rec.restaurant_id}")
        print(f"  Explanation: {rec.explanation}")
        if "Note:" not in rec.explanation:
            print("  !!! MISSING NOTE !!!")
        else:
            print("  [✓] Note Present")

if __name__ == "__main__":
    try:
        reproduce_issue()
    except Exception as e:
        print(f"Error during reproduction: {e}")
