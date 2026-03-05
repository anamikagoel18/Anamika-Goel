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
        Builds candidates following a strict 6-tier hierarchy:
        1. Local Strict
        2. Local Price Relaxed
        3. Local Rating Relaxed
        4. City-wide Strict
        5. City-wide Relaxed (Price & Rating)
        6. Neighborhood Favorites (Any Cuisine)
        
        Returns a list of (Restaurant, Score, TierIndex).
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
        orig_rating = preferences.min_rating or 4.0
        relaxed_rating = max(0, orig_rating - 0.5)

        # Tier 1: Strict Match (Neighborhood, Cuisine, Budget, Rating)
        add_tier_candidates(filter_restaurants(restaurants, preferences), 0)
        if len(candidates) >= threshold: return candidates[:preferences.limit]

        # Tier 2: Price Relaxation (Local, Cuisine, Rating, Relaxed Price)
        if relaxed_price:
            p2 = preferences.model_copy(update={"price_max": relaxed_price})
            add_tier_candidates(filter_restaurants(restaurants, p2), 1)
            if len(candidates) >= threshold: return candidates[:preferences.limit]

        # Tier 3: Rating Relaxation (Local, Cuisine, Budget, Relaxed Rating)
        p3 = preferences.model_copy(update={"min_rating": relaxed_rating})
        add_tier_candidates(filter_restaurants(restaurants, p3), 2)
        if len(candidates) >= threshold: return candidates[:preferences.limit]

        # Tier 4: Area Expansion Strict (City-wide, Cuisine, Budget, Rating)
        p4 = preferences.model_copy(update={"area": None})
        add_tier_candidates(filter_restaurants(restaurants, p4), 3)
        if len(candidates) >= threshold: return candidates[:preferences.limit]

        # Tier 5: Area Expansion Relaxed (City-wide, Cuisine, Relaxed Price & Rating)
        p5 = preferences.model_copy(update={"area": None, "price_max": relaxed_price, "min_rating": relaxed_rating})
        add_tier_candidates(filter_restaurants(restaurants, p5), 4)
        if len(candidates) >= threshold: return candidates[:preferences.limit]

        # Tier 6: Neighborhood Favorites (Local, Any Cuisine, Budget, Rating)
        p6 = preferences.model_copy(update={"cuisines": []})
        add_tier_candidates(filter_restaurants(restaurants, p6), 5)

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

