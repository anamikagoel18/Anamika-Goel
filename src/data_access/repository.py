from __future__ import annotations

from typing import List

from src.domain.models import Restaurant


class InMemoryRestaurantRepository:
    """
    Very simple, beginner-friendly repository that just wraps a Python list.

    Later this can be replaced by a real database-backed implementation without
    changing the rest of the code that depends on this interface.
    """

    def __init__(self, restaurants: List[Restaurant]) -> None:
        self._restaurants = list(restaurants)

    def get_all(self) -> List[Restaurant]:
        return list(self._restaurants)

    def get_by_city(self, city: str) -> List[Restaurant]:
        city_lower = city.lower()
        return [r for r in self._restaurants if r.city.lower() == city_lower]

    def filter_by_min_rating(self, min_rating: float) -> List[Restaurant]:
        return [
            r for r in self._restaurants if r.rating is not None and r.rating >= min_rating
        ]

