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
                tier_priority = {
                    "none": 0, 
                    "price": 1, 
                    "area": 2, 
                    "area_price": 3, 
                    "neighborhood_favorites": 4,
                    "neighborhood_favorites_price": 5,
                    "global_favorites": 6,
                    "rating_relaxed": 7
                }
                if tier_priority.get(level, 0) > tier_priority.get(highest_relaxation, 0):
                    highest_relaxation = level
            return True

        # Pre-calculate relaxed values
        orig_price = preferences.price_max
        relaxed_price = orig_price * 1.5 if orig_price else None

        # 1. Local Strict (Neighborhood, Cuisine, Price, Rating)
        filtered = filter_restaurants(restaurants, preferences)
        add_unique_candidates(filtered, "none")
        if len(candidates) >= threshold: return candidates[:preferences.limit], highest_relaxation

        # 2. Local Price Relaxed
        if relaxed_price:
            p2 = preferences.model_copy(update={"price_max": relaxed_price})
            add_unique_candidates(filter_restaurants(restaurants, p2), "price")
            if len(candidates) >= threshold: return candidates[:preferences.limit], highest_relaxation

        # 3. City-wide Strict
        p3 = preferences.model_copy(update={"area": None})
        add_unique_candidates(filter_restaurants(restaurants, p3), "area")
        if len(candidates) >= threshold: return candidates[:preferences.limit], highest_relaxation

        # 4. City-wide Price Relaxed
        if relaxed_price:
            p4 = preferences.model_copy(update={"area": None, "price_max": relaxed_price})
            add_unique_candidates(filter_restaurants(restaurants, p4), "area_price")
            if len(candidates) >= threshold: return candidates[:preferences.limit], highest_relaxation

        # 5. Neighborhood Favorites (Neighborhood, Any Cuisine, Strict Price, Strict Rating)
        p5 = preferences.model_copy(update={"cuisines": []})
        add_unique_candidates(filter_restaurants(restaurants, p5), "neighborhood_favorites")
        if len(candidates) >= threshold: return candidates[:preferences.limit], highest_relaxation

        # 6. Neighborhood Favorites Price Relaxed (Neighborhood, Any Cuisine, Relaxed Price, Strict Rating)
        if relaxed_price:
            p6 = preferences.model_copy(update={"cuisines": [], "price_max": relaxed_price})
            add_unique_candidates(filter_restaurants(restaurants, p6), "neighborhood_favorites_price")
            if len(candidates) >= threshold: return candidates[:preferences.limit], highest_relaxation

        # 7. Global Favorites (City-wide, Any Cuisine, Strict Price, Strict Rating)
        p7 = preferences.model_copy(update={"area": None, "cuisines": []})
        add_unique_candidates(filter_restaurants(restaurants, p7), "global_favorites")
        if len(candidates) >= threshold: return candidates[:preferences.limit], highest_relaxation

        # 8. Last Resort (Global Relaxed Rating - drop constraints to find anything)
        low_rating = max(0, (preferences.min_rating or 4.0) - 1.0)
        p8 = preferences.model_copy(update={"area": None, "cuisines": [], "price_max": relaxed_price, "min_rating": low_rating})
        add_unique_candidates(filter_restaurants(restaurants, p8), "rating_relaxed")

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

