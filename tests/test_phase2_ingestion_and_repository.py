from src.data_access.repository import InMemoryRestaurantRepository
from src.data_ingestion.ingest import ingest_from_iterable
from src.data_ingestion.schema_mapping import map_raw_to_restaurant


def _sample_raw_records():
    # These dicts loosely match fields you might see in the Zomato dataset.
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


def test_schema_mapping_basic_fields_and_price_band():
    raw = _sample_raw_records()[0]
    restaurant = map_raw_to_restaurant(raw)

    assert restaurant.id == "1"
    assert restaurant.name == "Budget Bites"
    assert restaurant.city == "Delhi"
    assert restaurant.cuisines == ["North Indian", "Chinese"]
    assert restaurant.average_cost_for_two == 250
    assert restaurant.price_band == "cheap"


def test_ingest_from_iterable_creates_restaurant_list():
    raw_items = _sample_raw_records()
    restaurants = ingest_from_iterable(raw_items)

    assert len(restaurants) == 3
    names = [r.name for r in restaurants]
    assert "Budget Bites" in names
    assert "Premium Plates" in names


def test_in_memory_repository_filters_by_city_and_rating():
    restaurants = ingest_from_iterable(_sample_raw_records())
    repo = InMemoryRestaurantRepository(restaurants)

    delhi_restaurants = repo.get_by_city("Delhi")
    assert len(delhi_restaurants) == 2

    high_rated = repo.filter_by_min_rating(4.2)
    names = {r.name for r in high_rated}
    assert names == {"Premium Plates"}

