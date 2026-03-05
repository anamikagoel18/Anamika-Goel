from src.domain.models import Recommendation, Restaurant, UserPreference
from src.data_access.repository import InMemoryRestaurantRepository
from src.services.recommendation_service import RecommendationService
from src.evaluation.offline_eval import build_sample_scenarios, run_offline_evaluation


class _FakeLlmClient:
    """
    Fake LLM client that always returns one recommendation for the first candidate.
    """

    def generate_recommendations(self, preferences, candidates):
        if not candidates:
            return []
        top_restaurant, top_score = candidates[0]
        return [
            Recommendation(
                restaurant_id=top_restaurant.id,
                score=top_score,
                explanation="Evaluation test explanation.",
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


def test_run_offline_evaluation_returns_summary_for_each_scenario():
    service = _build_eval_service()
    scenarios = build_sample_scenarios()

    results = run_offline_evaluation(service, scenarios)

    assert len(results) == len(scenarios)

    for summary in results:
        assert "preferences" in summary
        assert "num_recommendations" in summary
        assert "restaurant_ids" in summary

