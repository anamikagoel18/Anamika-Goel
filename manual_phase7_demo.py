from __future__ import annotations

from src.data_access.repository import InMemoryRestaurantRepository
from src.domain.models import Restaurant
from src.evaluation.offline_eval import build_sample_scenarios, run_offline_evaluation
from src.services.recommendation_service import RecommendationService
from src.domain.models import Recommendation


class _FakeLlmClient:
    """
    Simple fake LLM client so manual Phase 7 testing does not depend on Groq.
    """

    def generate_recommendations(self, preferences, candidates):
        if not candidates:
            return []
        top_restaurant, top_score = candidates[0]
        return [
            Recommendation(
                restaurant_id=top_restaurant.id,
                score=top_score,
                explanation="Offline evaluation explanation.",
            )
        ]


def _build_eval_service() -> RecommendationService:
    restaurants = [
        Restaurant(
            id="1",
            name="Budget Bites",
            cuisines=["North Indian", "Chinese"],
            city="Delhi",
            rating=4.0,
            average_cost_for_two=250,
        ),
        Restaurant(
            id="2",
            name="Italian Eats",
            cuisines=["Italian"],
            city="Delhi",
            rating=3.5,
            average_cost_for_two=500,
        ),
    ]
    repo = InMemoryRestaurantRepository(restaurants)
    fake_llm = _FakeLlmClient()
    return RecommendationService(repo, fake_llm)


def main():
    service = _build_eval_service()
    scenarios = build_sample_scenarios()

    results = run_offline_evaluation(service, scenarios)

    print("Offline evaluation summaries:\n")
    for summary in results:
        prefs = summary["preferences"]
        print(f"- Scenario for location={prefs['location']}, cuisines={prefs['cuisines']}")
        print(f"  num_recommendations: {summary['num_recommendations']}")
        print(f"  restaurant_ids: {summary['restaurant_ids']}\n")


if __name__ == "__main__":
    main()

