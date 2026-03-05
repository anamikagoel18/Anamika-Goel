from __future__ import annotations

from typing import List, Dict, Any

from src.domain.models import UserPreference, Recommendation
from src.services.recommendation_service import RecommendationService


def build_sample_scenarios() -> List[UserPreference]:
    """
    Very simple helper that returns a few hard-coded preference scenarios
    to use in offline evaluation.
    """
    return [
        UserPreference(
            location="Delhi",
            cuisines=["North Indian", "Chinese"],
            min_rating=3.5,
            price_min=100,
            price_max=600,
            limit=3,
        ),
        UserPreference(
            location="Delhi",
            cuisines=["Italian"],
            min_rating=3.0,
            price_min=200,
            price_max=700,
            limit=3,
        ),
    ]


def run_offline_evaluation(
    service: RecommendationService,
    scenarios: List[UserPreference],
) -> List[Dict[str, Any]]:
    """
    Run the recommendation service over a list of preference scenarios
    and return a simple, serializable summary for each scenario.

    This can later be extended to write results to disk, compute metrics, etc.
    """
    results: List[Dict[str, Any]] = []

    for prefs in scenarios:
        recs: List[Recommendation] = service.get_recommendations(prefs)
        results.append(
            {
                "preferences": prefs.model_dump(),
                "num_recommendations": len(recs),
                "restaurant_ids": [r.restaurant_id for r in recs],
            }
        )

    return results

