from __future__ import annotations

from typing import List, Tuple

from src.common.logging import get_logger
from src.data_access.repository import InMemoryRestaurantRepository
from src.domain.models import Recommendation, Restaurant, UserPreference
from src.llm.llm_client import LlmClient
from src.recommendation.candidate_selector import select_top_candidates
from src.recommendation.core_filtering import filter_restaurants


class RecommendationService:
    """
    Application service that orchestrates:
    - fetching restaurants from a repository
    - Phase 3 filtering / scoring
    - Phase 4 LLM explanation generation
    """

    def __init__(
        self,
        repo: InMemoryRestaurantRepository,
        llm_client: LlmClient,
    ) -> None:
        self._repo = repo
        self._llm_client = llm_client
        self._logger = get_logger(self.__class__.__name__)

    def _build_candidates(
        self, preferences: UserPreference
    ) -> Tuple[List[Tuple[Restaurant, float]], str]:
        restaurants = self._repo.get_all()
        
        # Tier 1: Strict
        filtered = filter_restaurants(restaurants, preferences)
        if filtered:
            return select_top_candidates(filtered, preferences), "none"

        # Tier 2: Relax Price
        self._logger.info("No exact matches, relaxing price filter.")
        relaxed_prefs = preferences.model_copy()
        if relaxed_prefs.price_max is not None:
            relaxed_prefs.price_max *= 1.5
        filtered = filter_restaurants(restaurants, relaxed_prefs)
        if filtered:
            return select_top_candidates(filtered, preferences), "price"

        # Tier 3: Relax Rating
        self._logger.info("No price match, relaxing rating filter.")
        if relaxed_prefs.min_rating is not None:
            relaxed_prefs.min_rating = max(0, relaxed_prefs.min_rating - 0.5)
        filtered = filter_restaurants(restaurants, relaxed_prefs)
        if filtered:
            return select_top_candidates(filtered, preferences), "rating"

        # Tier 4: Area Expansion (Strict - same cuisine, whole city)
        self._logger.info("No local matches for cuisine, searching city-wide (strict constraints).")
        city_prefs = relaxed_prefs.model_copy()
        city_prefs.area = None
        if city_prefs.location.lower() != "bangalore":
            city_prefs.location = "Bangalore"
            
        filtered = filter_restaurants(restaurants, city_prefs)
        if filtered:
            return select_top_candidates(filtered, preferences), "area"

        # Tier 5: Area Expansion (Relaxed - same cuisine, whole city)
        self._logger.info("No strict city-wide matches, absolute search for cuisine anywhere.")
        anywhere_cuisine_prefs = UserPreference(
            location="Bangalore",
            cuisines=preferences.cuisines,
            limit=preferences.limit
        )
        filtered = filter_restaurants(restaurants, anywhere_cuisine_prefs)
        if filtered:
            return select_top_candidates(filtered, preferences), "area_relaxed"

        # Tier 6: Neighborhood Favorites (any cuisine)
        self._logger.info("No cuisine match found city-wide, falling back to local neighborhood favorites.")
        fallback_prefs = preferences.model_copy()
        fallback_prefs.cuisines = [] # Ignore cuisine to find local favorites
        
        filtered = filter_restaurants(restaurants, fallback_prefs)
        
        if not filtered:
            # Absolute local fallback if even favorites are too expensive/low rated
            neighborhood_only = UserPreference(location=preferences.location, area=preferences.area, limit=preferences.limit)
            filtered = filter_restaurants(restaurants, neighborhood_only)
            
        if filtered:
            return select_top_candidates(filtered, preferences), "neighborhood"

        # Final absolute fallback if somehow everything failed
        return [], "none"

    def list_restaurants(self) -> List[Restaurant]:
        """
        Expose all restaurants for cases (like the API layer) where we need
        to map restaurant IDs in recommendations back to full restaurant info.
        """
        return self._repo.get_all()
    def get_recommendations(self, preferences: UserPreference) -> List[Recommendation]:
        self._logger.info(
            "Generating recommendations",
            extra={"location": preferences.location, "cuisines": preferences.cuisines},
        )
        candidates, relaxation_level = self._build_candidates(preferences)
        # Delegates to Groq LLM client for explanations
        recommendations = self._llm_client.generate_recommendations(
            preferences, candidates, relaxation_level=relaxation_level
        )
        self._logger.info("Generated %d recommendations", len(recommendations))
        return recommendations

