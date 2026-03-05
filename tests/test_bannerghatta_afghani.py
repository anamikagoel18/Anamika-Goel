import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from src.data_access.repository import InMemoryRestaurantRepository
from src.data_ingestion.hf_client import load_restaurants_from_hf
from src.domain.models import UserPreference
from src.services.recommendation_service import RecommendationService
from src.llm.llm_client import LlmClient

def test_reproduction():
    print("--- Reproducing Bannerghatta Road Afghani Issue ---")
    
    # Load real data
    restaurants = load_restaurants_from_hf(limit=None)
    repo = InMemoryRestaurantRepository(restaurants)
    
    # We don't need real LLM for this part of the trace
    llm = LlmClient()
    service = RecommendationService(repo, llm)
    
    # Exact preferences from user report
    prefs = UserPreference(
        location="Bangalore",
        area="Bannerghatta Road",
        cuisines=["Afghani"],
        min_rating=4.1,
        price_max=2000.0,
        limit=6
    )

    print(f"Preferences: {prefs}\n")

    # Trace _build_candidates
    candidates, level = service._build_candidates(prefs)
    
    print(f"Relaxation Level reached: {level}")
    print(f"Total candidates found: {len(candidates)}")
    for i, (r, score) in enumerate(candidates):
        print(f"{i+1}. {r.name} | Rating: {r.rating} | Area: {r.area} | Cuisines: {r.cuisines}")

    # Check if Sofraah (3.8) is in there
    ids = [r.id for r, _ in candidates]
    sofraah_matches = [id for id in ids if "sofraah" in id.lower()]
    if sofraah_matches:
        print("\n!!! BUG DETECTED: Sofraah (3.8) found in candidates despite 4.1+ alternatives !!!")
    else:
        print("\n[✓] Sofraah (3.8) not in candidates. Logic seems correct on this install.")

if __name__ == "__main__":
    test_reproduction()
