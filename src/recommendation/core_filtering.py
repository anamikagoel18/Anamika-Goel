from __future__ import annotations

from typing import Iterable, List

from src.domain.models import Restaurant, UserPreference


def filter_restaurants(
    restaurants: Iterable[Restaurant], preferences: UserPreference
) -> List[Restaurant]:
    """
    Phase 3 core filtering logic.

    This is intentionally simple and readable for a beginner:
    - Filter by city (substring match, case-insensitive).
    - Optionally filter by area, min_rating, price range / band, and cuisines.
    """
    result: List[Restaurant] = []

    preferred_city = preferences.location.strip().lower()
    preferred_area = preferences.area.strip().lower() if preferences.area else None
    preferred_cuisines = {c.lower() for c in preferences.cuisines}

    for restaurant in restaurants:
        # Location: match either City or Area (treat user input as a neighborhood name)
        if preferred_city:
            city_match = preferred_city in (restaurant.city or "").lower()
            area_match = preferred_city in (restaurant.area or "").lower()
            if not (city_match or area_match):
                continue

        # If a specific Area is ALSO provided, require it.
        if preferred_area and restaurant.area:
            if restaurant.area.strip().lower() != preferred_area:
                continue

        # Minimum rating
        if preferences.min_rating is not None:
            # Explicitly cast to float to avoid any hidden type mismatches
            current_rating = float(restaurant.rating or 0.0)
            required_rating = float(preferences.min_rating)
            if current_rating < required_rating:
                continue

        # Price range (if provided)
        if preferences.price_min is not None:
            if restaurant.average_cost_for_two is None or restaurant.average_cost_for_two < preferences.price_min:
                continue

        if preferences.price_max is not None:
            if restaurant.average_cost_for_two is None or restaurant.average_cost_for_two > preferences.price_max:
                continue

        # Price band (optional string like "cheap", "moderate", "expensive")
        if preferences.price_band:
            if not restaurant.price_band or restaurant.price_band.lower() != preferences.price_band.lower():
                continue

        # Cuisine intersection: if user specified cuisines, require at least one overlap
        if preferred_cuisines:
            restaurant_cuisines = {c.lower() for c in restaurant.cuisines}
            if restaurant_cuisines.isdisjoint(preferred_cuisines):
                continue

        result.append(restaurant)

    return result

