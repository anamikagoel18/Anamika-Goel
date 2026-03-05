from src.data_access.repository import InMemoryRestaurantRepository
from src.data_ingestion.ingest import ingest_from_iterable
from src.domain.models import UserPreference
from src.recommendation.candidate_selector import select_top_candidates
from src.recommendation.core_filtering import filter_restaurants


def _sample_raw_records():
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


def test_phase3_end_to_end_integration():
    # Ingest raw records into domain models
    restaurants = ingest_from_iterable(_sample_raw_records())
    repo = InMemoryRestaurantRepository(restaurants)

    # User preferences: looking for North Indian / Chinese food in Delhi
    prefs = UserPreference(
        location="Delhi",
        cuisines=["North Indian", "Chinese"],
        min_rating=3.5,
        price_min=100,
        price_max=600,
        limit=5,
    )

    # Phase 3 flow: filter -> score/select candidates
    filtered = filter_restaurants(repo.get_all(), prefs)
    candidates = select_top_candidates(filtered, prefs)

    # We expect Budget Bites (Delhi, North Indian/Chinese) to be the top result
    assert len(candidates) >= 1
    top_restaurant, top_score = candidates[0]
    assert top_restaurant.name == "Budget Bites"
    assert top_restaurant.city == "Delhi"
    assert top_restaurant.rating == 4.0
    assert top_score > 0

