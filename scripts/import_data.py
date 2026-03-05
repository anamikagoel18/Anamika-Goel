import json
import os
import sys
from typing import List

# Add the project root to sys.path so we can import src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.data_ingestion.hf_client import load_restaurants_from_hf
from src.domain.models import Restaurant

def export_data():
    """
    Download the full dataset from Hugging Face and save it locally as JSON.
    """
    print("START: Starting full data import from Hugging Face...")
    
    # Load all records (limit=None, force_refresh=True to apply latest mapping)
    restaurants = load_restaurants_from_hf(limit=None, force_refresh=True)
    
    output_path = os.path.join("data", "restaurants.json")
    os.makedirs("data", exist_ok=True)
    
    # Convert Restaurant models to dict for JSON serialization
    data = [r.dict() for r in restaurants]
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"SUCCESS: Successfully imported {len(data)} restaurants.")
    print(f"FILE: Data saved to {output_path}")
    
    # Statistics
    cities = set(r.city for r in restaurants if r.city)
    areas = set(r.area for r in restaurants if r.area)
    
    print(f"INFO: Unique Cities/Localities found: {len(cities)}")
    print(f"INFO: Unique Areas found: {len(areas)}")
    
    # Check for Bangalore diversity
    bangalore_matches = [c for c in cities if "Bangalore" in c or "Bengaluru" in c or c in ["BTM", "HSR", "Indiranagar", "Jayanagar", "Basavanagudi"]]
    print(f"INFO: Bangalore localities detected: {len(bangalore_matches)}")

if __name__ == "__main__":
    export_data()
