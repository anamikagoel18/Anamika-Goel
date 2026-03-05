
import sys
import os

# Ensure src is in python path
sys.path.append(os.getcwd())

from src.data_ingestion.hf_client import load_restaurants_from_hf

def rebuild():
    print("Forcing full cache rebuild with granular mapping...")
    # This will use the latest schema_mapping.py which prioritizes 'location'
    restaurants = load_restaurants_from_hf(limit=None, force_refresh=True)
    print(f"Cache rebuilt successfully with {len(restaurants)} restaurants.")
    
    # Quick area check
    areas = set(r.area for r in restaurants if r.area)
    print(f"Unique areas found: {len(areas)}")

if __name__ == "__main__":
    rebuild()
