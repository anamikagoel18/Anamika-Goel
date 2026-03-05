import pytest
from pydantic import ValidationError

from src.domain.models import Restaurant, UserPreference, Recommendation


def test_restaurant_creation_minimal():
    restaurant = Restaurant(
        id="1",
        name="Test Restaurant",
        cuisines=["North Indian", "Chinese"],
        city="Bangalore",
    )

    assert restaurant.id == "1"
    assert restaurant.name == "Test Restaurant"
    assert restaurant.city == "Bangalore"
    assert "North Indian" in restaurant.cuisines


def test_restaurant_cuisines_accepts_comma_separated_string():
    restaurant = Restaurant(
        id="2",
        name="Comma Cuisines",
        cuisines="Italian, Mexican ,  Pizza ",
        city="Mumbai",
    )

    assert restaurant.cuisines == ["Italian", "Mexican", "Pizza"]


def test_user_preference_defaults_and_normalization():
    prefs = UserPreference(
        location="Delhi",
        cuisines="North Indian, Chinese",
        dietary_restrictions="vegan, gluten-free",
    )

    assert prefs.location == "Delhi"
    assert prefs.limit == 5  # default
    assert prefs.cuisines == ["North Indian", "Chinese"]
    assert prefs.dietary_restrictions == ["vegan", "gluten-free"]


def test_user_preference_limit_validation():
    # limit must be >=1, <=50
    with pytest.raises(ValidationError):
        UserPreference(location="Delhi", limit=0)

    with pytest.raises(ValidationError):
        UserPreference(location="Delhi", limit=100)


def test_recommendation_validation():
    rec = Recommendation(restaurant_id="1", score=0.95, explanation="Great fit")
    assert rec.restaurant_id == "1"
    assert rec.score == 0.95

    with pytest.raises(ValidationError):
        Recommendation(restaurant_id="1", score=-0.1, explanation="Invalid score")

