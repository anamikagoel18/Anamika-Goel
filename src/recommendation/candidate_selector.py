from __future__ import annotations

from typing import List, Tuple

from src.domain.models import Restaurant, UserPreference
from src.recommendation.scoring import score_restaurants


def select_top_candidates(
    restaurants: List[Restaurant],
    preferences: UserPreference,
) -> List[Tuple[Restaurant, float]]:
    """
    Convenience function for Phase 3:
    - Score all restaurants.
    - Sort them by score (highest first).
    - Return only the top N based on the user's limit.
    """
    scored = score_restaurants(restaurants, preferences)
    # Sort primarily by rating, then by popularity (votes)
    scored.sort(
        key=lambda pair: (
            pair[0].rating or 0.0,
            pair[0].votes or 0
        ),
        reverse=True
    )

    limit = preferences.limit
    return scored[:limit]

