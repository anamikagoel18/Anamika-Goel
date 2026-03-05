import sys
import os
import json

# Add project root to path
sys.path.append(os.getcwd())

from src.data_access.repository import InMemoryRestaurantRepository
from src.data_ingestion.hf_client import load_restaurants_from_hf
from src.domain.models import UserPreference
from src.services.recommendation_service import RecommendationService
from src.recommendation.core_filtering import filter_restaurants

def debug_tiers():
    print("--- Debugging Recommendation Tiers ---")
    
    # Load data
    restaurants = load_restaurants_from_hf(limit=None)
    repo = InMemoryRestaurantRepository(restaurants)
    
    # User Preferences
    prefs = UserPreference(
        location="Bangalore",
        area="Bannerghatta Road",
        cuisines=["Afghani"],
        min_rating=4.1,
        price_max=2000.0,
        limit=3
    )

    print(f"Target: Area={prefs.area}, Cuisines={prefs.cuisines}, MinRating={prefs.min_rating}, MaxPrice={prefs.price_max}\n")

    # Trace Tiers manually
    relaxed_price = prefs.price_max * 1.5 if prefs.price_max else None
    
    tiers = [
        ("Tier 1: Local Strict", prefs),
        ("Tier 2: Local Price Relaxed", prefs.model_copy(update={"price_max": relaxed_price})),
        ("Tier 3: City-wide Strict", prefs.model_copy(update={"area": None})),
        ("Tier 4: City-wide Price Relaxed", prefs.model_copy(update={"area": None, "price_max": relaxed_price})),
        ("Tier 5: Neighborhood Favs", prefs.model_copy(update={"cuisines": []})),
        ("Tier 6: Neighborhood Favs Price Relaxed", prefs.model_copy(update={"cuisines": [], "price_max": relaxed_price})),
        ("Tier 7: Global Favorites", prefs.model_copy(update={"area": None, "cuisines": []})),
        ("Tier 8: Last Resort", prefs.model_copy(update={"area": None, "cuisines": [], "price_max": relaxed_price, "min_rating": max(0, (prefs.min_rating or 4.0) - 1.0)})),
    ]

    found_ids = set()
    for name, p in tiers:
        filtered = filter_restaurants(restaurants, p)
        new_ones = [r for r in filtered if r.id not in found_ids]
        print(f"{name}: Found {len(new_ones)} new matches (Total {len(filtered)})")
        for r in new_ones[:3]:
            print(f"  - {r.name} | {r.rating} | {r.area} | {r.average_cost_for_two}")
        for r in new_ones:
            found_ids.add(r.id)
        if len(found_ids) >= 3 and "global" not in name.lower() and "favorites" not in name.lower():
             # Simulation of early return in service
             pass
    
    # Specifically check for Sofraah
    sofraah = [r for r in restaurants if "Sofraah" in r.name][0]
    print(f"\nSofraah Check:")
    print(f"Name: {sofraah.name}, Rating: {sofraah.rating}, Area: {sofraah.area}, Cuisines: {sofraah.cuisines}, Cost: {sofraah.average_cost_for_two}")

if __name__ == "__main__":
    debug_tiers()
