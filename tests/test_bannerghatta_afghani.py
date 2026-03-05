import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_bannerghatta_afghani_transparency():
    print("\n--- Testing Bannerghatta Road + Afghani Transparency ---")
    payload = {
        "location": "Bangalore",
        "area": "Bannerghatta Road",
        "cuisines": ["Afghani"],
        "limit": 3
    }
    
    response = requests.post(f"{BASE_URL}/recommendations", json=payload)
    if response.status_code != 200:
        print(f"FAILED: Backend returned status {response.status_code}")
        print(response.text)
        return

    data = response.json()
    recs = data.get("recommendations", [])
    print(f"Got {len(recs)} recommendations")
    
    EXPECTED_NOTE = "Note: I couldn't find any restaurants serving these specific cuisines in your neighborhood"
    
    success = True
    for rec in recs:
        rest = rec["restaurant"]
        explanation = rec["explanation"]
        print(f"Match: {rest['name']} | Area: {rest['area']} | Cuisines: {rest['cuisines']}")
        print(f"Explanation Preview: {explanation[:100]}...")
        
        # Verify transparency note is present
        if EXPECTED_NOTE not in explanation:
            print(f"FAILED: Missing transparency note for {rest['name']}")
            success = False
        
        # Verify it's in Jayanagar (as confirmed by data earlier)
        if rest["area"].lower() != "jayanagar":
            print(f"WARNING: Unexpected area {rest['area']} for Afghani cuisine expansion.")

    if success:
        print("SUCCESS: Bannerghatta Road + Afghani scenario verified with transparency.")
    else:
        print("FAILED: Transparency verification failed.")

if __name__ == "__main__":
    test_bannerghatta_afghani_transparency()
