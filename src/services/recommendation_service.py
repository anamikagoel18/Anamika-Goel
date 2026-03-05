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
        candidates: List[Tuple[Restaurant, float]] = []
        highest_relaxation = "none"
        threshold = 3
        
        def add_unique_candidates(filtered_list: List[Restaurant], level: str):
            nonlocal highest_relaxation
            if not filtered_list:
                return False
            
            top_new = select_top_candidates(filtered_list, preferences)
            existing_ids = {r.id for r, _ in candidates}
            added_any = False
            for r, score in top_new:
                if r.id not in existing_ids:
                    candidates.append((r, score))
                    added_any = True
            
            if added_any and level != "none":
                # Only update highest_relaxation if we actually found something new in this relaxed tier
                # mapping tiers to descriptive levels for the LLM
                tier_priority = {"none": 0, "price": 1, "rating": 2, "area": 3, "area_relaxed": 4, "neighborhood": 5}
                if tier_priority.get(level, 0) > tier_priority.get(highest_relaxation, 0):
                    highest_relaxation = level
            return True

        # Tier 1: Strict
        filtered = filter_restaurants(restaurants, preferences)
        add_unique_candidates(filtered, "none")
        if len(candidates) >= threshold:
            return candidates[:preferences.limit], highest_relaxation

        # Tier 2: Relax Price
        self._logger.info("Not enough strict matches, relaxing price filter.")
        relaxed_prefs = preferences.model_copy()
        if relaxed_prefs.price_max is not None:
            relaxed_prefs.price_max *= 1.5
        filtered = filter_restaurants(restaurants, relaxed_prefs)
        add_unique_candidates(filtered, "price")
        if len(candidates) >= threshold:
            return candidates[:preferences.limit], highest_relaxation

        # Tier 3: Relax Rating
        self._logger.info("Not enough matches, relaxing rating filter.")
        if relaxed_prefs.min_rating is not None:
            relaxed_prefs.min_rating = max(0, relaxed_prefs.min_rating - 0.5)
        filtered = filter_restaurants(restaurants, relaxed_prefs)
        add_unique_candidates(filtered, "rating")
        if len(candidates) >= threshold:
            return candidates[:preferences.limit], highest_relaxation

        # Tier 4: Area Expansion (Strict - whole city)
        self._logger.info("Not enough local matches, searching city-wide.")
        city_prefs = relaxed_prefs.model_copy()
        city_prefs.area = None
        if city_prefs.location.lower() != "bangalore":
            city_prefs.location = "Bangalore"
        filtered = filter_restaurants(restaurants, city_prefs)
        add_unique_candidates(filtered, "area")
        if len(candidates) >= threshold:
            return candidates[:preferences.limit], highest_relaxation

        # Tier 5: Area Expansion (Relaxed - city-wide)
        self._logger.info("Not enough city-wide strict matches, broadening search.")
        anywhere_cuisine_prefs = UserPreference(
            location="Bangalore",
            cuisines=preferences.cuisines,
            limit=preferences.limit
        )
        filtered = filter_restaurants(restaurants, anywhere_cuisine_prefs)
        add_unique_candidates(filtered, "area_relaxed")
        if len(candidates) >= threshold:
            return candidates[:preferences.limit], highest_relaxation

        # Tier 6: Neighborhood Fallback (any cuisine)
        self._logger.info("Cuisine scarce, falling back to local favorites.")
        fallback_prefs = preferences.model_copy()
        fallback_prefs.cuisines = []
        filtered = filter_restaurants(restaurants, fallback_prefs)
        
        if not filtered:
            neighborhood_only = UserPreference(location="Bangalore", area=preferences.area, limit=preferences.limit)
            filtered = filter_restaurants(restaurants, neighborhood_only)
        
        add_unique_candidates(filtered, "neighborhood")

        return candidates[:preferences.limit], highest_relaxation

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
        
        # Final ranking step: strictly sort by rating (primary) and votes (secondary)
        # to ensure the most premium/popular choices appear first.
        restaurant_map = {r.id: r for r in self.list_restaurants()}
        recommendations.sort(
            key=lambda r: (
                restaurant_map[r.restaurant_id].rating or 0.0,
                restaurant_map[r.restaurant_id].votes or 0
            ),
            reverse=True
        )
        
        self._logger.info("Generated %d recommendations", len(recommendations))
        return recommendations

