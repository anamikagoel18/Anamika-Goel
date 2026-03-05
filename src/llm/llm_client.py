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

    def generate_recommendations_v2(
        self,
        preferences: UserPreference,
        candidates: List[Tuple[Restaurant, float, int]],
    ) -> List[Recommendation]:
        """
        New version that handles per-candidate tier levels and relaxation notes.
        """
        if not candidates:
            return []

        # Convert to (Restaurant, float) for the existing prompt builder
        candidates_for_prompt = [(r, s) for r, s, t in candidates]
        messages = build_recommendation_messages(preferences, candidates_for_prompt)

        try:
            completion = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=0.2,
            )
            content = completion.choices[0].message.content
            recs_from_llm = parse_recommendations_from_text(content)
        except Exception as e:
            print(f"WARNING: LLM recommendation generation failed: {e}")
            recs_from_llm = []

        # Tier-based notes
        tier_notes = {
            0: "", # Strict Match
            1: "Note: We slightly relaxed your price range to find this option in your neighborhood.",
            2: "Note: We slightly relaxed your minimum rating to find this option in your neighborhood.",
            10: "Note: searching across all of Bangalore to find your exact cuisine and rating.",
            11: "Note: expanding search city-wide with relaxed budget to find matches for your exact cuisine.",
            20: "Note: I've looked across all of Bangalore to find the highest-rated restaurants that fit your general preferences."
        }

        candidate_lookup = {r.id: (r, score, tier) for r, score, tier in candidates}
        merged: List[Recommendation] = []
        used_explanations = set()

        for rec in recs_from_llm:
            res_data = candidate_lookup.get(rec.restaurant_id)
            if not res_data:
                continue
            
            restaurant, score, tier = res_data
            # Determine if we use the specific dynamic template for city-wide expansion
            if tier in [10, 11, 20]:
                target_cuisine = preferences.cuisines[0] if preferences.cuisines else (restaurant.cuisines[0] if restaurant.cuisines else "various")
                
                # Dynamic Template from User
                final_explanation = (
                    f"We couldn't find any restaurants with your selected cuisine and rating in your exact neighborhood, "
                    f"so we searched across Bangalore to find the best match. We recommend {restaurant.name} because it "
                    f"serves {target_cuisine} cuisine you prefer, has a strong rating of {restaurant.rating}, "
                    f"and fits within your budget."
                )
            else:
                final_explanation = rec.explanation
                
                # Deterministically handle budget phrasing for local tiers
                if preferences.price_max and restaurant.average_cost_for_two:
                    if restaurant.average_cost_for_two <= preferences.price_max:
                        budget_phrase = "This restaurant is within your budget."
                        if budget_phrase.lower() not in final_explanation.lower():
                            final_explanation = f"{budget_phrase} {final_explanation}"

                # Safety check: Name mention for local tiers
                if restaurant.name.lower() not in final_explanation.lower():
                    final_explanation = f"{restaurant.name} is a great choice because {final_explanation}"

                # Uniqueness handling
                if final_explanation in used_explanations:
                    final_explanation = f"Recommended: {restaurant.name} provides a quality dining experience. {final_explanation}"
                used_explanations.add(final_explanation)

                # Prepend Tier Note (Local tiers only now, as city-wide replaced the whole thing)
                note = tier_notes.get(tier, "")
                if note and note not in final_explanation:
                    final_explanation = f"{note} {final_explanation}"
                
            merged.append(
                Recommendation(
                    restaurant_id=rec.restaurant_id,
                    score=score,
                    explanation=final_explanation,
                )
            )

        # Fallback for LLM failure
        if not merged:
            for r, score, tier in candidates:
                if tier in [10, 11, 20]:
                    target_cuisine = preferences.cuisines[0] if preferences.cuisines else (r.cuisines[0] if r.cuisines else "various")
                    final_fallback = (
                        f"We couldn't find any restaurants with your selected cuisine and rating in your exact neighborhood, "
                        f"so we searched across Bangalore to find the best match. We recommend {r.name} because it "
                        f"serves {target_cuisine} cuisine you prefer, has a strong rating of {r.rating}, "
                        f"and fits within your budget."
                    )
                else:
                    note = tier_notes.get(tier, "")
                    base_fallback = f"{r.name} is a top choice based on your preferences."
                    final_fallback = f"{note} {base_fallback}" if note else base_fallback
                
                merged.append(
                    Recommendation(
                        restaurant_id=r.id,
                        score=score,
                        explanation=final_fallback,
                    )
                )

        return merged

