import pytest
from src.llm.response_parser import parse_recommendations_from_text
from src.domain.models import Recommendation

def test_parse_robustness_with_extra_text():
    raw = """
    Here is your JSON:
    {
      "recommendations": [
        {"restaurant_id": "1", "explanation": "Fits well."}
      ]
    }
    Hope this helps!
    """
    recs = parse_recommendations_from_text(raw)
    assert len(recs) == 1
    assert recs[0].restaurant_id == "1"

def test_parse_robustness_with_markdown_fences():
    raw = """
    ```json
    {
      "recommendations": [
        {"restaurant_id": "2", "explanation": "Fenced."}
      ]
    }
    ```
    """
    recs = parse_recommendations_from_text(raw)
    assert len(recs) == 1
    assert recs[0].restaurant_id == "2"

def test_parse_robustness_with_bare_list():
    raw = """
    [
      {"restaurant_id": "3", "explanation": "Bare list."}
    ]
    """
    recs = parse_recommendations_from_text(raw)
    assert len(recs) == 1
    assert recs[0].restaurant_id == "3"

def test_parse_fails_on_complete_garbage():
    raw = "This is not JSON at all."
    with pytest.raises(ValueError, match="Failed to parse LLM JSON"):
        parse_recommendations_from_text(raw)

if __name__ == "__main__":
    # Quick manual run
    try:
        test_parse_robustness_with_extra_text()
        test_parse_robustness_with_markdown_fences()
        test_parse_robustness_with_bare_list()
        print("Parser robustness tests passed!")
    except Exception as e:
        print(f"Parser robustness tests failed: {e}")
