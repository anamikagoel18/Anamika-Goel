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
    ) -> List[Tuple[Restaurant, float, int]]:
        """
        Builds candidates following strict cuisine/rating rules:
        - If Cuisine is selected: STRICT cuisine and rating match.
        - Tiers: Local -> City-wide -> Stop.
        - If 'All' (Empty list): 6-tier fallback logic.
        """
        restaurants = self._repo.get_all()
        candidates: List[Tuple[Restaurant, float, int]] = []
        threshold = 3
        
        def add_tier_candidates(filtered_list: List[Restaurant], tier_index: int):
            if not filtered_list:
                return False
            
            top_new = select_top_candidates(filtered_list, preferences)
            existing_ids = {r.id for r, _, _ in candidates}
            added_any = False
            for r, score in top_new:
                if r.id not in existing_ids:
                    candidates.append((r, score, tier_index))
                    added_any = True
            return added_any

        # Pre-calculate relaxed values
        orig_price = preferences.price_max
        relaxed_price = orig_price * 1.5 if orig_price else None
        
        # Branch based on whether a specific cuisine is selected
        has_specific_cuisine = len(preferences.cuisines) > 0

        if has_specific_cuisine:
            # --- STRICT CUISINE MODE ---
            # Tier 0: Local Strict
            add_tier_candidates(filter_restaurants(restaurants, preferences), 0)
            if len(candidates) >= threshold: return candidates[:preferences.limit]

            # Tier 1: Local Price Relaxed
            if relaxed_price:
                p1 = preferences.model_copy(update={"price_max": relaxed_price})
                add_tier_candidates(filter_restaurants(restaurants, p1), 1)
                if len(candidates) >= threshold: return candidates[:preferences.limit]

            # Tier 10: City-wide Strict (Exact Cuisine)
            p2 = preferences.model_copy(update={"area": None})
            add_tier_candidates(filter_restaurants(restaurants, p2), 10)
            if len(candidates) >= threshold: return candidates[:preferences.limit]

            # Tier 11: City-wide Price Relaxed (Exact Cuisine)
            if relaxed_price:
                p3 = preferences.model_copy(update={"area": None, "price_max": relaxed_price})
                add_tier_candidates(filter_restaurants(restaurants, p3), 11)

            return candidates[:preferences.limit]

        else:
            # --- BROAD DISCOVERY MODE ("All" Cuisines) ---
            orig_rating = preferences.min_rating or 4.0
            relaxed_rating = max(0, orig_rating - 0.5)

            # Tier 0: Local Strict (Area, Any Cuisine, Budget, Rating)
            add_tier_candidates(filter_restaurants(restaurants, preferences), 0)
            if len(candidates) >= threshold: return candidates[:preferences.limit]

            # Tier 1: Local Price Relaxed
            if relaxed_price:
                p1 = preferences.model_copy(update={"price_max": relaxed_price})
                add_tier_candidates(filter_restaurants(restaurants, p1), 1)
                if len(candidates) >= threshold: return candidates[:preferences.limit]

            # Tier 2: Local Rating Relaxed
            p2 = preferences.model_copy(update={"min_rating": relaxed_rating})
            add_tier_candidates(filter_restaurants(restaurants, p2), 2)
            if len(candidates) >= threshold: return candidates[:preferences.limit]

            # Tier 20: City-wide Broad (Any Cuisine, Budget, Rating)
            p3 = preferences.model_copy(update={"area": None})
            add_tier_candidates(filter_restaurants(restaurants, p3), 20)

            return candidates[:preferences.limit]

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
        candidates = self._build_candidates(preferences)
        
        # Delegates to Groq LLM client for explanations
        # Note: We pass the tier info to the LLM client by mapping candidates to a (Restaurant, Score) structure
        # but the LLM Client needs to know the tier for the note. 
        # For now, we'll keep it simple and just use the individual candidate tier if we refactor LlmClient.
        recommendations = self._llm_client.generate_recommendations_v2(
            preferences, candidates
        )
        
        # Final ranking step: STRICTLY sort by Tier (primary), then Rating, then Votes
        restaurant_map = {r.id: r for r in self.list_restaurants()}
        tier_map = {r.id: tier for r, _, tier in candidates}
        
        recommendations.sort(
            key=lambda r: (
                tier_map.get(r.restaurant_id, 99),        # Tier first (Ascending)
                -(restaurant_map[r.restaurant_id].rating or 0.0), # Rating second (Descending)
                -(restaurant_map[r.restaurant_id].votes or 0)     # Votes third (Descending)
            )
        )
        
        self._logger.info("Generated %d recommendations", len(recommendations))
        return recommendations

