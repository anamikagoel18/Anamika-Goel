from __future__ import annotations

from typing import Any, Dict, Optional

from src.domain.models import Restaurant


def _derive_price_band(average_cost_for_two: Optional[float]) -> Optional[str]:
    """
    Very simple heuristic to bucket price into cheap / moderate / expensive.
    """
    if average_cost_for_two is None:
        return None
    if average_cost_for_two < 300:
        return "cheap"
    if average_cost_for_two < 700:
        return "moderate"
    return "expensive"


def map_raw_to_restaurant(raw: Dict[str, Any]) -> Restaurant:
    """
    Map a raw record (e.g. from the Zomato HF dataset) into our Restaurant domain model.
    Normalized for the ManikaSaini/zomato-restaurant-recommendation dataset which is all Bangalore.
    """
    # Use url as a fallback for ID if specific ID fields are missing.
    restaurant_id = str(raw.get("Restaurant ID") or raw.get("id") or raw.get("url") or "")
    name = str(raw.get("Restaurant Name") or raw.get("name") or "").strip()

    # The dataset "ManikaSaini/zomato-restaurant-recommendation" is 100% Bangalore data.
    # location contains more specific area (94 unique values).
    # listed_in(city) contains the broader neighborhood (30 unique values).
    city = "Bangalore"
    neighborhood = raw.get("location") or raw.get("listed_in(city)") or raw.get("City") or raw.get("city")
    
    # Ensure it's a string and handle potential NaN from pandas/HF
    if neighborhood is None or (isinstance(neighborhood, float) and str(neighborhood) == "nan"):
        area = "Unknown"
    else:
        area = str(neighborhood).strip()
    
    cuisines_raw = raw.get("Cuisines") or raw.get("cuisines")
    if cuisines_raw is None or (isinstance(cuisines_raw, float) and str(cuisines_raw) == "nan"):
        cuisines_raw = []
    if isinstance(cuisines_raw, str):
        # Normalize to Title Case for consistency in filters
        cuisines = [c.strip().title() for c in cuisines_raw.split(",") if c.strip()]
    else:
        cuisines = [str(c).title() for c in cuisines_raw]
    
    # Handle several rating formats (e.g., float, or string like "4.1/5", "NEW").
    rating_raw = raw.get("Aggregate rating") or raw.get("rating") or raw.get("rate")
    rating = None
    if rating_raw is not None:
        if isinstance(rating_raw, str):
            # Parse prefix from "4.1/5"
            parts = rating_raw.split("/")
            try:
                rating = float(parts[0])
            except (ValueError, IndexError):
                rating = None
        else:
            try:
                rating = float(rating_raw)
            except (ValueError, TypeError):
                rating = None

    votes_raw = raw.get("Votes") or raw.get("votes")
    votes = None
    if votes_raw is not None:
        try:
            votes = int(float(votes_raw))
        except (ValueError, TypeError):
            votes = None
    
    # Handle cost strings that might contain commas, e.g., "1,200".
    cost_raw = raw.get("Average Cost for two") or raw.get(
        "average_cost_for_two"
    ) or raw.get("approx_cost(for two people)")
    
    average_cost_for_two = None
    if cost_raw is not None:
        if isinstance(cost_raw, str):
            clean_cost = cost_raw.replace(",", "")
            try:
                average_cost_for_two = float(clean_cost)
            except ValueError:
                average_cost_for_two = None
        else:
            try:
                average_cost_for_two = float(cost_raw)
            except (ValueError, TypeError):
                average_cost_for_two = None

    price_band = _derive_price_band(average_cost_for_two)

    return Restaurant(
        id=restaurant_id,
        name=name,
        cuisines=cuisines,
        city=city,
        area=area,
        average_cost_for_two=average_cost_for_two,
        price_band=price_band,
        rating=rating,
        votes=votes,
        url=raw.get("url"),
    )

