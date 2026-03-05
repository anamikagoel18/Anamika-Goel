from __future__ import annotations

from typing import List, Tuple

from src.domain.models import Restaurant, UserPreference


def build_recommendation_messages(
    preferences: UserPreference,
    candidates: List[Tuple[Restaurant, float]],
    relaxation_level: str = "none",
) -> list[dict]:
    """
    Build chat messages for the Groq LLM.
    """
    system_content = (
        "You are a helpful restaurant recommendation assistant. "
        "You must ONLY choose from the candidate restaurants provided by the system. "
        "Do not invent new restaurant names or locations. "
        "Return recommendations in the exact JSON schema specified."
    )

    # Contextual instruction based on how much we had to relax the search
    relaxation_note = ""
    if relaxation_level == "price":
        relaxation_note = "Note: We slightly relaxed your price range to find these great options."
    elif relaxation_level == "area":
        relaxation_note = "Note: I couldn't find any restaurants serving these specific cuisines in your neighborhood, so I looked in nearby areas of Bangalore to find you the best matches."
    elif relaxation_level == "area_price":
        relaxation_note = "Note: I couldn't find matches for this cuisine within your exact budget or neighborhood, so I looked in nearby areas with slightly relaxed pricing."
    elif relaxation_level == "neighborhood_favorites":
        relaxation_note = "Note: I couldn't find an exact match for your cuisines here, so I've hand-picked the top-rated local favorites in your area that match your other preferences."
    elif relaxation_level == "neighborhood_favorites_price":
        relaxation_note = "Note: I've found the best-rated local favorites near you, with a slight adjustment to the budget to ensure quality options."
    elif relaxation_level == "global_favorites":
        relaxation_note = "Note: I've looked across all of Bangalore to find the highest-rated restaurants that fit your budget and general preferences."
    elif relaxation_level == "rating_relaxed":
        relaxation_note = "Note: I've expanded the search to find the best available matches across Bangalore, relaxing some criteria to ensure you have good options to choose from."

    # Compact candidate info
    candidate_summaries = []
    for restaurant, score in candidates:
        candidate_summaries.append(
            {
                "id": restaurant.id,
                "name": restaurant.name,
                "city": restaurant.city,
                "area": restaurant.area,
                "rating": restaurant.rating,
                "average_cost_for_two": restaurant.average_cost_for_two,
                "price_band": restaurant.price_band,
                "cuisines": restaurant.cuisines,
                "score": score,
            }
        )

    user_content = {
        "preferences": preferences.model_dump(),
        "candidates": candidate_summaries,
        "relaxation_context": relaxation_note,
        "instructions": (
            "From the candidates provided, choose up to 'limit' restaurants that best match the "
            "preferences. You MUST generate a UNIQUE, specific explanation for EACH restaurant. "
            "Internal Rule: Each explanation must mention the restaurant's NAME and describe "
            "features (cuisines, rating, or location) specific to that restaurant. "
            "DO NOT use the same explanation for multiple restaurants. "
            "DO NOT refer to the names of other candidates in one restaurant's explanation. "
            "If a restaurant's average_cost_for_two is <= user's price_max, you MUST explicitly "
            "include the phrase 'within your budget'. Do NOT mention numerical prices."
            "Respond ONLY with JSON in this exact schema:\n\n"
            "{\n"
            '  "recommendations": [\n'
            "    {\n"
            '      "restaurant_id": "string",\n'
            '      "explanation": "string"\n'
            "    }\n"
            "  ]\n"
            "}\n"
        ),
    }

    import json
    return [
        {"role": "system", "content": system_content},
        {
            "role": "user",
            "content": (
                "Here are the user preferences and candidate restaurants in JSON format:\n"
                f"{json.dumps(user_content, indent=2)}\n\n"
                "IMPORTANT: Respond ONLY with the JSON structure requested. Do not include any conversational text."
            )
        },
    ]

