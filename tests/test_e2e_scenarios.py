
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_scenario_1_exact_match():
    print("\n--- Scenario 1: Exact Filter Match (Precision) ---")
    payload = {
        "location": "Bangalore",
        "area": "Indiranagar",
        "cuisines": ["Italian"],
        "price_min": 500,
        "price_max": 2000,
        "min_rating": 4.0,
        "limit": 3
    }
    response = requests.post(f"{BASE_URL}/recommendations", json=payload)
    assert response.status_code == 200
    data = response.json()
    recs = data.get("recommendations", [])
    print(f"Got {len(recs)} recommendations")
    
    for rec in recs:
        rest = rec["restaurant"]
        explanation = rec.get("explanation", "")
        print(f"DEBUG: Name={rest['name']}, Cost={rest['average_cost_for_two']}, PriceMax={payload['price_max']}")
        print(f"DEBUG: Explanation='{explanation}'")
        assert rest["area"].lower() == "indiranagar"
        assert any("italian" in c.lower() for c in rest["cuisines"])
        # New check for budget-aware phrasing
        assert "within your budget" in explanation.lower()
        # Should not show a literal range if it's within budget
        assert "-" not in explanation or "budget" in explanation.lower() 
    print("SUCCESS: Scenario 1 Passed")

def test_scenario_2_cuisine_priority_expansion():
    print("\n--- Scenario 2: Cuisine Priority Expansion (Rare Cuisine) ---")
    # Afghani isn't in Indiranagar. Should return Afghani from other neighborhoods (Jayanagar, etc.)
    payload = {
        "location": "Bangalore",
        "area": "Indiranagar",
        "cuisines": ["Afghani"],
        "limit": 3
    }
    response = requests.post(f"{BASE_URL}/recommendations", json=payload)
    assert response.status_code == 200
    data = response.json()
    recs = data.get("recommendations", [])
    print(f"Got {len(recs)} recommendations")
    
    found_afghani = False
    for rec in recs:
        rest = rec["restaurant"]
        explanation = rec["explanation"]
        print(f"Match: {rest['name']} | Area: {rest['area']} | Cuisines: {rest['cuisines']}")
        # Should be Afghani but NOT in Indiranagar
        if any("afghani" in c.lower() for c in rest["cuisines"]):
            found_afghani = True
            assert rest["area"].lower() != "indiranagar"
            # Should have the "area" or "area_relaxed" note
            assert "nearby areas" in explanation.lower() or "exactly what you're looking for" in explanation.lower()
            
    assert found_afghani, "Should have prioritized Afghani cuisine by expanding area"
    print("SUCCESS: Scenario 2 Passed")

def test_scenario_3_rating_relaxation_transparency():
    print("\n--- Scenario 3: Rating Relaxation Transparency ---")
    # Search for Chinese in Indiranagar with ridiculously high rating
    payload = {
        "location": "Bangalore",
        "area": "Indiranagar",
        "cuisines": ["Chinese"],
        "min_rating": 4.9,
        "limit": 3
    }
    response = requests.post(f"{BASE_URL}/recommendations", json=payload)
    assert response.status_code == 200
    data = response.json()
    recs = data.get("recommendations", [])
    
    EXPECTED_NOTE = "Note: We slightly relaxed the minimum rating to find matches in this neighborhood."
    
    for rec in recs:
        rest = rec["restaurant"]
        explanation = rec["explanation"]
        print(f"Match: {rest['name']} | Rating: {rest['rating']} | Cost: {rest['average_cost_for_two']}")
        assert rest["area"].lower() == "indiranagar"
        assert explanation.startswith(EXPECTED_NOTE)
    print("SUCCESS: Scenario 3 Passed")

def test_scenario_4_price_relaxation_local():
    print("\n--- Scenario 4: Price Relaxation (Local) ---")
    # Search for Italian in Indiranagar with a low budget (e.g. 500)
    # Most Italian spots in Indiranagar are 1000+. This should trigger Tier 2.
    payload = {
        "location": "Bangalore",
        "area": "Indiranagar",
        "cuisines": ["Italian"],
        "price_max": 400,
        "min_rating": 4.0,
        "limit": 3
    }
    response = requests.post(f"{BASE_URL}/recommendations", json=payload)
    assert response.status_code == 200
    data = response.json()
    recs = data.get("recommendations", [])
    
    EXPECTED_NOTE = "Note: We slightly relaxed your price range to find these great options."
    
    for rec in recs:
        rest = rec["restaurant"]
        explanation = rec["explanation"]
        print(f"Match: {rest['name']} | Cost: {rest['average_cost_for_two']}")
        print(f"DEBUG: Explanation='{explanation}'")
        assert rest["area"].lower() == "indiranagar"
        assert explanation.startswith(EXPECTED_NOTE)
    print("SUCCESS: Scenario 4 Passed")

def test_scenario_5_neighborhood_fallback():
    print("\n--- Scenario 5: Neighborhood Fallback (Unknown Cuisine) ---")
    # Search for a cuisine that doesn't exist in Bangalore (e.g. Martian)
    # Should fall back to Indiranagar favorites (Tier 6).
    payload = {
        "location": "Bangalore",
        "area": "Indiranagar",
        "cuisines": ["Martian"],
        "limit": 3
    }
    response = requests.post(f"{BASE_URL}/recommendations", json=payload)
    assert response.status_code == 200
    data = response.json()
    recs = data.get("recommendations", [])
    
    EXPECTED_NOTE = "Note: I couldn't find an exact match for your cuisines here, so I've hand-picked the top-rated local favorites in your area that match your other preferences."
    
    for rec in recs:
        rest = rec["restaurant"]
        explanation = rec["explanation"]
        print(f"Match: {rest['name']} | Area: {rest['area']} | Cuisines: {rest['cuisines']}")
        assert rest["area"].lower() == "indiranagar"
        assert explanation.startswith(EXPECTED_NOTE)
    print("SUCCESS: Scenario 5 Passed")

if __name__ == "__main__":
    try:
        test_scenario_1_exact_match()
        test_scenario_2_cuisine_priority_expansion()
        test_scenario_3_rating_relaxation_transparency()
        test_scenario_4_price_relaxation_local()
        test_scenario_5_neighborhood_fallback()
        print("\nALL 5 E2E SCENARIOS PASSED!")
    except AssertionError as e:
        print(f"\nE2E SCENARIO FAILED: {e}")
    except Exception as e:
        print(f"\nAN ERROR OCCURRED: {e}")
