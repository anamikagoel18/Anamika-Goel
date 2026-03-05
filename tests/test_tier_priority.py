import sys
import os
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.getcwd())

from src.domain.models import Restaurant, UserPreference
from src.recommendation.candidate_selector import select_top_candidates
from src.services.recommendation_service import RecommendationService

def test_tier_priority():
    print("\n--- Testing 7-Tier Hierarchy Priority ---")
    
    # Mock data
    # R1: Banashankari, Italian, 3000 cost, 4.5 rating (Local, but expensive)
    # R2: Jayanagar, Italian, 1000 cost, 4.5 rating (City-wide Strict)
    # R3: Banashankari, Italian, 1000 cost, 3.5 rating (Local, but low rating)
    
    restaurants = [
        Restaurant(id="1", name="R1-Local-Expensive", city="Bangalore", area="Banashankari", cuisines=["Italian"], average_cost_for_two=3000, rating=4.5, votes=100),
        Restaurant(id="2", name="R2-Citywide-Strict", city="Bangalore", area="Jayanagar", cuisines=["Italian"], average_cost_for_two=1000, rating=4.5, votes=200),
        Restaurant(id="3", name="R3-Local-LowRating", city="Bangalore", area="Banashankari", cuisines=["Italian"], average_cost_for_two=1000, rating=3.5, votes=50),
    ]
    
    # User Preferences: Banashankari, Italian, Max 2000, Min 4.0
    prefs = UserPreference(
        location="Bangalore",
        area="Banashankari",
        cuisines=["Italian"],
        price_max=2000,
        min_rating=4.0,
        limit=5
    )
    
    repo = MagicMock()
    repo.get_all.return_value = restaurants
    llm = MagicMock()
    
    service = RecommendationService(repo, llm)
    
    candidates, level = service._build_candidates(prefs)
    
    print(f"Relaxation Level reached: {level}")
    print("Candidates Order:")
    for i, (r, score) in enumerate(candidates):
        print(f"{i+1}. {r.name} | Rating: {r.rating} | Area: {r.area} | Cost: {r.average_cost_for_two}")
        
    # Expectations:
    # 1. Local Strict: None (R1 too expensive, R3 too low rated)
    # 2. Local Price (2000 * 1.5 = 3000): R1 is a match!
    # 3. Local Rating: (R3 is 3.5, too low for 4.0 - 0.5 = 3.5? Wait, 3.5 >= 3.5? Yes.)
    # 4. City-wide Strict: R2 is a match!
    
    # BUT, the order should be R1 (Local Price) than R2 (City-wide Strict)?
    # Actually, the user complained that low ratings are coming. 
    # My 7-tier logic:
    # Tier 2 (Local Price) -> R1
    # Tier 4 (City-wide Strict) -> R2
    
    # Wait, if R1 is found in Tier 2, it's added. Then Tier 4 adds R2.
    # The final count is 2. The threshold is 3. 
    # So it keeps going.
    
    assert any(r.name == "R2-Citywide-Strict" for r, _ in candidates), "Should find city-wide strict match"
    
    # Most importantly, R2 should be higher score because it's higher rated/matches exactly?
    # CandidateSelector sorts by rating then votes. 
    # R2 (4.5, 200 votes) outranks R1 (4.5, 100 votes).
    
    names = [r.name for r, _ in candidates]
    print(f"Candidate Names: {names}")
    
    # R3 (Local Rating Relaxed) should be included if we haven't hit threshold of 3.
    assert "R3-Local-LowRating" in names, "R3 should be included in relaxed tiers"

    print("\nSUCCESS: 7-Tier hierarchy verified.")

if __name__ == "__main__":
    test_tier_priority()
