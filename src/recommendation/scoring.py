from __future__ import annotations

from typing import Iterable, List, Tuple

from src.domain.models import Restaurant, UserPreference


def score_restaurant(restaurant: Restaurant, preferences: UserPreference) -> float:
    """
    Simple, beginner-friendly scoring function.

    In later phases you can tune these weights; for now we just combine:
    - rating
    - popularity (votes)
    - cuisine match count
    """
    score = 0.0

    # Rating weight
    if restaurant.rating is not None:
        score += restaurant.rating  # rating out of 5, typically

    # Popularity weight (very light)
    if restaurant.votes is not None:
        score += min(restaurant.votes / 100.0, 5.0)

    # Cuisine match bonus
    preferred_cuisines = {c.lower() for c in preferences.cuisines}
    if preferred_cuisines:
        restaurant_cuisines = {c.lower() for c in restaurant.cuisines}
        matches = len(preferred_cuisines & restaurant_cuisines)
        # Weight increased from 0.5 to 10.0 to ensure matching cuisines outrank non-matches
        score += matches * 10.0

    return score


def score_restaurants(
    restaurants: Iterable[Restaurant], preferences: UserPreference
) -> List[Tuple[Restaurant, float]]:
    """
    Score all restaurants and return (restaurant, score) pairs.
    """
    return [(r, score_restaurant(r, preferences)) for r in restaurants]

