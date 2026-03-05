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
    elif relaxation_level == "rating":
        relaxation_note = "Note: We slightly relaxed the minimum rating to find matches in this neighborhood."
    elif relaxation_level == "area":
        relaxation_note = "Note: I couldn't find any restaurants serving these specific cuisines in your neighborhood, so I looked in nearby areas of Bangalore to find you the best matches."
    elif relaxation_level == "area_relaxed":
        relaxation_note = "Note: I couldn't find matches for these cuisines within your exact budget or neighborhood, so I've found the best options available elsewhere in Bangalore."
    elif relaxation_level == "neighborhood":
        relaxation_note = "Note: I couldn't find an exact match for your cuisines here, so I've hand-picked the top-rated local favorites in your area that match your other preferences."

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
            "From the candidates, choose up to 'limit' restaurants that best match the "
            "preferences. For each chosen restaurant, explain briefly why it is a good fit. "
            "If a restaurant's average_cost_for_two is less than or equal to the user's "
            "price_max (if provided), you MUST explicitly include the phrase 'within your budget' "
            "in the explanation. In these cases, do NOT mention numerical price ranges (e.g., '1200-1500')."
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

