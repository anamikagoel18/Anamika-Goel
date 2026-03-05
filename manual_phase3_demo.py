from __future__ import annotations

from src.data_access.repository import InMemoryRestaurantRepository
from src.data_ingestion.ingest import ingest_from_iterable
from src.domain.models import UserPreference
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
        limit=5,
    )

    # 4) Filter and rank
    filtered = filter_restaurants(repo.get_all(), prefs)
    candidates = select_top_candidates(filtered, prefs)

    # 5) Print results so you can manually inspect them
    print(f"User preferences: {prefs!r}\n")
    print("Recommended candidates (before LLM step):\n")
    for restaurant, score in candidates:
        print(
            f"- {restaurant.name} | city={restaurant.city} | rating={restaurant.rating} | "
            f"avg_cost_for_two={restaurant.average_cost_for_two} | cuisines={restaurant.cuisines} | "
            f"score={score:.2f}"
        )


if __name__ == "__main__":
    main()

