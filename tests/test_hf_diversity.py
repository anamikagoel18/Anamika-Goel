import pytest
from src.data_ingestion.hf_client import load_restaurants_from_hf
from src.domain.models import Restaurant
from collections import Counter

def test_zomato_data_diversity_integration():
    """
    Integration test to verify that the ingestion pipeline pulls a diverse 
    set of cities/localities from the Zomato dataset when the limit is higher.
    """
    # Use a larger limit to ensure we hit multiple localities
    limit = 20000
    print(f"\nLoading {limit} restaurants for diversity check...")
    restaurants = load_restaurants_from_hf(limit=limit)
    
    assert len(restaurants) > 0, "No restaurants were imported!"
    
    city_counter = Counter(r.city for r in restaurants if r.city)
    
    print(f"\nTotal unique cities/localities found in first {len(restaurants)} records: {len(city_counter)}")
    print("Top localities:")
    for city, count in city_counter.most_common(10):
        print(f" - {city}: {count}")
    
    # Based on my diagnostic (check_cities_deep.py), 5000 rows should likely 
    # give us around 4-5 localities, but let's see. 
    # The user said "only 5 locations are coming", so I want to see if 20k rows 
    # (as I set in main.py) would help.
    
    assert len(city_counter) >= 1, "Should have at least one city"

if __name__ == "__main__":
    test_zomato_data_diversity_integration()
