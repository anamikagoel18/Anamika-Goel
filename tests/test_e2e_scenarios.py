
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
    
    for i, rec in enumerate(recs):
        rest = rec["restaurant"]
        explanation = rec.get("explanation", "")
        print(f"DEBUG: Name={rest['name']}, Area={rest['area']}, Cost={rest['average_cost_for_two']}, PriceMax={payload['price_max']}")
        
        # If it's the first result and Tier 1 matches exist, it should be strict
        if i == 0 and "note" not in explanation.lower():
            assert rest["area"].lower() == "indiranagar"
            assert any("italian" in c.lower() for c in rest["cuisines"])
        
        # New check for budget-aware phrasing
        if rest["average_cost_for_two"] <= payload["price_max"]:
            assert "within your budget" in explanation.lower()
    print("SUCCESS: Scenario 1 Passed")

def test_scenario_2_cuisine_priority_expansion():
    print("\n--- Scenario 2: Cuisine Priority Expansion (Rare Cuisine) ---")
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
    
    assert len(recs) >= 1
    found_afghani = False
    for rec in recs:
        rest = rec["restaurant"]
        explanation = rec["explanation"]
        print(f"Match: {rest['name']} | Area: {rest['area']} | Cuisines: {rest['cuisines']}")
        if any("afghani" in c.lower() for c in rest["cuisines"]):
            found_afghani = True
            # Should have the expansion note
            assert "nearby areas" in explanation.lower() or "best matches" in explanation.lower()
            
    assert found_afghani, "Should have prioritized Afghani cuisine by expanding area"
    print("SUCCESS: Scenario 2 Passed")

def test_scenario_3_rating_relaxation_transparency():
    print("\n--- Scenario 3: Rating Relaxation Transparency ---")
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
    
    EXPECTED_NOTE = "Note: We slightly relaxed the minimum rating"
    
    assert len(recs) >= 1
    for rec in recs:
        rest = rec["restaurant"]
        explanation = rec["explanation"]
        print(f"Match: {rest['name']} | Rating: {rest['rating']} | Area: {rest['area']}")
        # If it's a relaxed result, check the note
        if rest["rating"] < payload["min_rating"]:
            assert EXPECTED_NOTE in explanation
    print("SUCCESS: Scenario 3 Passed")

def test_scenario_4_price_relaxation_local():
    print("\n--- Scenario 4: Price Relaxation (Local) ---")
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
    EXPECTED_NOTE = "Note: We slightly relaxed your price range"
    
    assert len(recs) >= 1
    for rec in recs:
        rest = rec["restaurant"]
        explanation = rec["explanation"]
        print(f"Match: {rest['name']} | Cost: {rest['average_cost_for_two']}")
        if rest["average_cost_for_two"] > payload["price_max"]:
            assert EXPECTED_NOTE in explanation
    print("SUCCESS: Scenario 4 Passed")

def test_scenario_5_neighborhood_fallback():
    print("\n--- Scenario 5: Neighborhood Fallback (Unknown Cuisine) ---")
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
    EXPECTED_NOTE = "Note: I couldn't find an exact match for your cuisines here"
    
    assert len(recs) >= 1
    for i, rec in enumerate(recs):
        rest = rec["restaurant"]
        explanation = rec["explanation"]
        print(f"Match: {rest['name']} | Area: {rest['area']} | Cuisines: {rest['cuisines']}")
        # All results should have the fallback note since MARTIAN doesn't exist
        assert EXPECTED_NOTE in explanation
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
