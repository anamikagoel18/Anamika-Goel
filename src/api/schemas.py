from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class PreferenceRequest(BaseModel):
    location: str
    area: Optional[str] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    price_band: Optional[str] = None
    min_rating: Optional[float] = None
    cuisines: List[str] = Field(default_factory=list)
    limit: Optional[int] = Field(default=5, ge=1, le=50)


class RestaurantResponse(BaseModel):
    id: str
    name: str
    city: str
    area: Optional[str] = None
    rating: Optional[float] = None
    price_band: Optional[str] = None
    average_cost_for_two: Optional[float] = None
    cuisines: List[str] = Field(default_factory=list)


class RecommendationResponseItem(BaseModel):
    restaurant: RestaurantResponse
    score: float
    explanation: str


class RecommendationResponse(BaseModel):
    preferences: PreferenceRequest
    recommendations: List[RecommendationResponseItem]

