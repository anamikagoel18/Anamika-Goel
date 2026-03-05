from __future__ import annotations

import json
from typing import Any, Dict, List

from src.domain.models import Recommendation


def parse_recommendations_from_text(raw_text: str) -> List[Recommendation]:
    """
    Parse the LLM's text response into a list of Recommendation objects.

    We expect a JSON structure like:
    {
      "recommendations": [
        {"restaurant_id": "1", "explanation": "..." }
      ]
    }
    """
    raw_text = raw_text.strip()
    
    # Very defensive JSON block extraction
    import re
    # Try to find something that looks like a JSON object {...} or list [...]
    json_match = re.search(r"(\{.*\}|\[.*\])", raw_text, re.DOTALL)
    if json_match:
        json_text = json_match.group(0)
    else:
        json_text = raw_text

    try:
        data: Dict[str, Any] = json.loads(json_text)
    except json.JSONDecodeError as exc:
        # One last attempt: strip potential markdown fences manually if regex missed it
        clean_text = json_text.strip().strip("`").strip()
        if clean_text.startswith("json"):
            clean_text = clean_text[4:].strip()
        try:
            data = json.loads(clean_text)
        except json.JSONDecodeError:
            raise ValueError(f"Failed to parse LLM JSON: {exc}") from exc

    if isinstance(data, list):
        recs = data
    elif isinstance(data, dict):
        recs = data.get("recommendations", [])
        if not isinstance(recs, list):
             raise ValueError("Invalid LLM format: 'recommendations' must be a list")
    else:
        raise ValueError("Invalid LLM format: expected JSON object or list")

    recommendations: List[Recommendation] = []
    for item in recs:
        if not isinstance(item, dict):
            continue
        restaurant_id = str(item.get("restaurant_id", "")).strip()
        explanation = str(item.get("explanation", "")).strip()
        if not restaurant_id or not explanation:
            continue
        recommendations.append(
            Recommendation(
                restaurant_id=restaurant_id,
                score=0.0,  # Will be filled/overridden by upstream logic if needed
                explanation=explanation,
            )
        )

    return recommendations

