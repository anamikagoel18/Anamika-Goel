
import json
import os
import sys

# Ensure src is in python path
sys.path.append(os.getcwd())

from src.data_ingestion.hf_client import load_restaurants_from_hf

def check_data():
    print("Checking for Afghani in Indiranagar...")
    # Load all restaurants
    restaurants = load_restaurants_from_hf(limit=None)
    
    # 1. Broad Check: Does Afghani exist AT ALL?
    afghani_total = [r for r in restaurants if any("afghani" in c.lower() for c in r.cuisines)]
    print(f"Total Afghani records found: {len(afghani_total)}")
    
    # 2. Neighborhood Check: Indiranagar
    indiranagar_total = [r for r in restaurants if (r.area and "indiranagar" in r.area.lower())]
    print(f"Total Indiranagar records found: {len(indiranagar_total)}")
    
    # 3. Intersection
    matches = [r for r in afghani_total if r in indiranagar_total]
    print(f"Direct matches (Afghani + Indiranagar): {len(matches)}")
    
    for m in matches:
        print(f"  - {m.name} | Rating: {m.rating} | Cost: {m.average_cost_for_two}")

    # 4. Check "₹400 for two" in Indiranagar with 4.8+
    # Belgian Waffle Factory and Milano Ice Cream
    desserts = [r for r in indiranagar_total if r.name in ["Belgian Waffle Factory", "Milano Ice Cream"]]
    for d in desserts:
        print(f"DEBUG: {d.name} | Rating: {d.rating} | Cost: {d.average_cost_for_two} | Cuisines: {d.cuisines}")

if __name__ == "__main__":
    check_data()
