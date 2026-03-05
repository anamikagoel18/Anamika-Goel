from __future__ import annotations

from typing import List, Tuple, Optional

from groq import Groq

from src.config.settings import settings
from src.domain.models import Recommendation, Restaurant, UserPreference
from src.llm.prompts import build_recommendation_messages
from src.llm.response_parser import parse_recommendations_from_text


class LlmClient:
    """
    Simple Groq LLM client for generating restaurant recommendations.

    For production use, this uses the real Groq SDK and the API key from settings.
    In tests, you can inject a fake `client` object to avoid real network calls.
    """

    def __init__(
        self,
        client: Optional[Groq] = None,
        model: str = "llama-3.1-8b-instant",
    ) -> None:
        self._client = client or Groq(api_key=settings.groq_api_key)
        self._model = model

    def generate_recommendations(
        self,
        preferences: UserPreference,
        candidates: List[Tuple[Restaurant, float]],
        relaxation_level: str = "none",
    ) -> List[Recommendation]:
        """
        Call the Groq LLM to generate natural-language explanations for the
        already-filtered/scored candidate restaurants.
        """
        if not candidates:
            return []

        messages = build_recommendation_messages(preferences, candidates, relaxation_level=relaxation_level)

        try:
            completion = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=0.2,
            )
            content = completion.choices[0].message.content
            recs_from_llm = parse_recommendations_from_text(content)
        except Exception as e:
            # Important: if the LLM fails (rate limit, network, decommissioned etc.),
            # we do NOT want the whole application to crash.
            print(f"WARNING: LLM recommendation generation failed: {e}")
            recs_from_llm = []

        # Merging and deterministic note prepending
        relaxation_note = ""
        if relaxation_level == "price":
            relaxation_note = "Note: We slightly relaxed your price range to find these great options."
        elif relaxation_level == "rating":
            relaxation_note = "Note: We slightly relaxed the minimum rating to find matches in this neighborhood."
        elif relaxation_level == "area":
            relaxation_note = "Note: I couldn't find any restaurants serving these specific cuisines in your neighborhood, so I looked in nearby areas of Bangalore to find you the best matches."
        elif relaxation_level == "area_price":
            relaxation_note = "Note: I couldn't find matches for this cuisine within your exact budget or neighborhood, so I looked in nearby areas with slightly relaxed pricing."
        elif relaxation_level == "area_relaxed":
            relaxation_note = "Note: I couldn't find matches for this cuisine within your exact criteria or neighborhood, so I've found the best options available elsewhere in Bangalore."
        elif relaxation_level == "neighborhood":
            relaxation_note = "Note: I couldn't find an exact match for your cuisines here, so I've hand-picked the top-rated local favorites in your area that match your other preferences."

        candidate_lookup = {r.id: (r, score) for r, score in candidates}
        merged: List[Recommendation] = []
        for rec in recs_from_llm:
            res_data = candidate_lookup.get(rec.restaurant_id)
            if not res_data:
                continue
            
            restaurant, score = res_data
            final_explanation = rec.explanation
            
            # Deterministically handle budget phrasing
            if preferences.price_max and restaurant.average_cost_for_two:
                if restaurant.average_cost_for_two <= preferences.price_max:
                    budget_phrase = "This restaurant is within your budget."
                    if budget_phrase.lower() not in final_explanation.lower():
                        final_explanation = f"{budget_phrase} {final_explanation}"

            # Deterministically prepend the relaxation note if it's not already there
            if relaxation_note and relaxation_note not in final_explanation:
                final_explanation = f"{relaxation_note} {final_explanation}"
                
            merged.append(
                Recommendation(
                    restaurant_id=rec.restaurant_id,
                    score=score,
                    explanation=final_explanation,
                )
            )

        # Fallback: if the LLM didn't return any valid recommendations, just
        # surface the top N candidates with a generic explanation so the user
        # always sees something.
        if not merged:
            base_fallback = "Top match based on your location and preferences."
            if relaxation_level == "price":
                base_fallback = "Slightly relaxed your price range to find these great options."
            elif relaxation_level == "rating":
                base_fallback = "Slightly relaxed the minimum rating to find matches in this area."
            elif relaxation_level == "neighborhood":
                base_fallback = "Found the best local alternatives since your exact cuisine wasn't available."
            
            # Ensure transparency note is present even in non-LLM fallback
            final_fallback = base_fallback
            if relaxation_note and relaxation_note not in final_fallback:
                final_fallback = f"{relaxation_note} {base_fallback}"

            merged = [
                Recommendation(
                    restaurant_id=r.id,
                    score=score,
                    explanation=final_fallback,
                )
                for r, score in candidates
            ]

        return merged

