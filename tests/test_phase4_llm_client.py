from src.domain.models import UserPreference, Restaurant
from src.llm.llm_client import LlmClient


class _FakeGroqMessage:
    def __init__(self, content: str) -> None:
        self.content = content


class _FakeGroqChoice:
    def __init__(self, content: str) -> None:
        self.message = _FakeGroqMessage(content)


class _FakeGroqCompletion:
    def __init__(self, content: str) -> None:
        self.choices = [_FakeGroqChoice(content)]


class _FakeGroqClient:
    """
    Minimal fake Groq client for testing without real API calls.
    """

    def __init__(self, response_json: str) -> None:
        self._response_json = response_json
        self.chat = self.Chat(self)

    class Chat:
        def __init__(self, outer: "_FakeGroqClient") -> None:
            self._outer = outer
            self.completions = self.Completions(outer)

        class Completions:
            def __init__(self, outer: "_FakeGroqClient") -> None:
                self._outer = outer

            def create(self, *args, **kwargs):
                # Ignore args/kwargs for this simple fake; always return the same content.
                return _FakeGroqCompletion(self._outer._response_json)


def test_llm_client_parses_recommendations_and_merges_scores():
    # Prepare a fake JSON response that Groq might return
    fake_json = """
    {
      "recommendations": [
        {"restaurant_id": "1", "explanation": "Great budget option in Delhi."}
      ]
    }
    """

    fake_client = _FakeGroqClient(fake_json)
    llm_client = LlmClient(client=fake_client)

    # Single candidate restaurant with a known score
    restaurant = Restaurant(
        id="1",
        name="Budget Bites",
        cuisines=["North Indian", "Chinese"],
        city="Delhi",
        rating=4.0,
        average_cost_for_two=250,
    )
    candidates = [(restaurant, 6.0)]

    prefs = UserPreference(location="Delhi", cuisines=["North Indian"])

    recommendations = llm_client.generate_recommendations(prefs, candidates)

    assert len(recommendations) == 1
    rec = recommendations[0]
    assert rec.restaurant_id == "1"
    assert rec.score == 6.0  # should be merged from candidate score
    assert "budget" in rec.explanation.lower()

