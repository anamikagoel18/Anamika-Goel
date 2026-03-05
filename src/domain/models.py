from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class Restaurant(BaseModel):
    """
    Core restaurant entity used throughout the system.

    This is a domain-level model (Phase 1) and is intentionally storage-agnostic.
    """

    id: str
    name: str
    cuisines: List[str] = Field(default_factory=list)
    city: str
    area: Optional[str] = None
    average_cost_for_two: Optional[float] = None
    price_band: Optional[str] = Field(
        default=None,
        description="Derived bucket such as 'cheap', 'moderate', or 'expensive'.",
    )
    rating: Optional[float] = None
    votes: Optional[int] = None
    highlights: List[str] = Field(default_factory=list)
    url: Optional[str] = None
    menu_items: List[str] = Field(default_factory=list)

    @field_validator("cuisines", mode="before")
    @classmethod
    def _normalize_cuisines(cls, value):
        if value is None:
            return []
        if isinstance(value, str):
            # Allow comma-separated string as a convenience
            parts = [part.strip() for part in value.split(",") if part.strip()]
            return parts
        return value


class UserPreference(BaseModel):
    """
    Captures a single recommendation request's user preferences.
    """

    location: str = Field(description="City or general location")
    area: Optional[str] = Field(
        default=None, description="More specific area or neighborhood within the city."
    )
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    price_band: Optional[str] = Field(
        default=None, description="Optional bucket: cheap / moderate / expensive."
    )
    min_rating: Optional[float] = None
    cuisines: List[str] = Field(default_factory=list)
    limit: int = Field(default=5, ge=1, le=50)
    sort_by: Optional[str] = Field(
        default=None,
        description="Optional preference for sorting, e.g. 'rating', 'distance', 'popularity'.",
    )
    dietary_restrictions: List[str] = Field(default_factory=list)

    @field_validator("cuisines", "dietary_restrictions", mode="before")
    @classmethod
    def _normalize_string_lists(cls, value):
        if value is None:
            return []
        if isinstance(value, str):
            parts = [part.strip() for part in value.split(",") if part.strip()]
            return parts
        return value


class Recommendation(BaseModel):
    """
    Result of a recommendation run at the domain level.
    """

    restaurant_id: str
    score: float = Field(ge=0.0)
    explanation: str

