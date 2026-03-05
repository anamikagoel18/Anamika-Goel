from __future__ import annotations


class RecommendationError(Exception):
    """Base exception for recommendation-related errors."""


class ExternalServiceError(RecommendationError):
    """Raised when an external service (like Groq) fails."""


