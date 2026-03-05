import sys
import os
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.getcwd())

from src.domain.models import Restaurant, UserPreference
from src.recommendation.candidate_selector import select_top_candidates

def test_ranking_logic():
    print("\n--- Testing Multi-Level Ranking Logic ---")
    
    # Mock restaurants
    # R1: 4.5 rating, 100 votes
    # R2: 4.5 rating, 200 votes (Should be higher than R1)
    # R3: 4.6 rating, 10 votes (Should be highest overall)
    # R4: 4.0 rating, 1000 votes (Should be lowest)
    
    restaurants = [
        Restaurant(id="1", name="R1", city="Bangalore", area="Area1", cuisines=["Indian"], rating=4.5, votes=100),
        Restaurant(id="2", name="R2", city="Bangalore", area="Area1", cuisines=["Indian"], rating=4.5, votes=200),
        Restaurant(id="3", name="R3", city="Bangalore", area="Area1", cuisines=["Indian"], rating=4.6, votes=10),
        Restaurant(id="4", name="R4", city="Bangalore", area="Area1", cuisines=["Indian"], rating=4.0, votes=1000),
    ]
    
    prefs = UserPreference(location="Bangalore", area="Area1", limit=10)
    
    candidates = select_top_candidates(restaurants, prefs)
    
    print("Ranking Order:")
    for i, (r, score) in enumerate(candidates):
        print(f"{i+1}. {r.name} | Rating: {r.rating} | Votes: {r.votes}")
        
    # Assertions
    assert candidates[0][0].name == "R3", "R3 (4.6) should be first"
    assert candidates[1][0].name == "R2", "R2 (4.5, 200 votes) should be second"
    assert candidates[2][0].name == "R1", "R1 (4.5, 100 votes) should be third"
    assert candidates[3][0].name == "R4", "R4 (4.0) should be fourth"
    
    print("\nSUCCESS: Multi-Level Ranking (Rating > Votes) verified in candidate selection.")

if __name__ == "__main__":
    try:
        test_ranking_logic()
    except AssertionError as e:
        print(f"\nFAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)
