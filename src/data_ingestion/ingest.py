from __future__ import annotations

from typing import Any, Dict, Iterable, List

from src.domain.models import Restaurant
from src.data_ingestion.schema_mapping import map_raw_to_restaurant


def ingest_from_iterable(raw_items: Iterable[Dict[str, Any]]) -> List[Restaurant]:
    """
    Beginner-friendly ingestion: take an iterable of raw dicts and convert
    them into a list of Restaurant domain models.

    In later phases this can be extended to read from Hugging Face datasets
    or a database, but for now it's just pure Python structures.
    """
    restaurants: List[Restaurant] = []
    seen_keys = set()
    for raw in raw_items:
        restaurant = map_raw_to_restaurant(raw)
        # Skip obviously invalid rows.
        if not restaurant.id or not restaurant.name:
            continue
            
        # Composite key for deduplication: Name + Area.
        # This prevents the same restaurant appearing multiple times if it delivers to many areas.
        unique_key = (restaurant.name.lower(), (restaurant.area or "Unknown").lower())
        
        if unique_key not in seen_keys:
            restaurants.append(restaurant)
            seen_keys.add(unique_key)
    return restaurants

