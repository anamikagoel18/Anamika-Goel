from __future__ import annotations

from src.config.settings import settings
from src.data_access.repository import InMemoryRestaurantRepository
from src.data_ingestion.ingest import ingest_from_iterable
from src.domain.models import UserPreference
from src.llm.llm_client import LlmClient
from src.recommendation.candidate_selector import select_top_candidates
from src.recommendation.core_filtering import filter_restaurants


def _sample_raw_records():
    # Same style of sample data we used in tests, just for manual inspection.
    return [
        {
            "Restaurant ID": 1,
            "Restaurant Name": "Budget Bites",
            "City": "Delhi",
            "Cuisines": "North Indian, Chinese",
            "Aggregate rating": 4.0,
            "Average Cost for two": 250,
            "Votes": 100,
        },
        {
            "Restaurant ID": 2,
            "Restaurant Name": "Midrange Meals",
            "City": "Delhi",
            "Cuisines": "Italian",
            "Aggregate rating": 3.5,
            "Average Cost for two": 500,
            "Votes": 50,
        },
        {
            "Restaurant ID": 3,
            "Restaurant Name": "Premium Plates",
            "City": "Mumbai",
            "Cuisines": "Continental",
            "Aggregate rating": 4.5,
            "Average Cost for two": 900,
            "Votes": 200,
        },
    ]


def main():
    if not settings.groq_api_key:
        print("ERROR: GROQ_API_KEY is not set in your .env file.")
        return

    # 1) Ingest raw data into Restaurant models
    raw_items = _sample_raw_records()
    restaurants = ingest_from_iterable(raw_items)

    # 2) Wrap them in the in-memory repository
    repo = InMemoryRestaurantRepository(restaurants)

    # 3) Create a user preference to test with
    prefs = UserPreference(
        location="Delhi",
        cuisines=["North Indian", "Chinese"],
        min_rating=3.5,
        price_min=100,
        price_max=600,
        limit=3,
    )

    # 4) Phase 3: filter and rank
    filtered = filter_restaurants(repo.get_all(), prefs)
    candidates = select_top_candidates(filtered, prefs)

    # 5) Phase 4: call Groq via LlmClient to generate explanations
    llm_client = LlmClient()
    recommendations = llm_client.generate_recommendations(prefs, candidates)

    # 6) Print results so you can manually inspect them
    print(f"User preferences: {prefs!r}\n")
    print("Final recommendations from Groq LLM:\n")

    # Map restaurant_id back to full restaurant info for display
    restaurant_by_id = {r.id: r for r, _ in candidates}

    for rec in recommendations:
        restaurant = restaurant_by_id.get(rec.restaurant_id)
        if not restaurant:
            continue
        print(
            f"- {restaurant.name} (city={restaurant.city}, rating={restaurant.rating}, "
            f"avg_cost_for_two={restaurant.average_cost_for_two}, cuisines={restaurant.cuisines})"
        )
        print(f"  Explanation: {rec.explanation}\n")


if __name__ == "__main__":
    main()

