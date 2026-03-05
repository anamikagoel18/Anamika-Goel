import pytest
from src.llm.llm_client import LlmClient
from src.domain.models import UserPreference, Restaurant

def test_real_llm_recommendation_smoke_test():
    """
    Integration test using the real Groq API.
    Ensures that our prompts and parser work end-to-end.
    """
    llm_client = LlmClient()
    
    # 2 candidates
    candidates = [
        (Restaurant(id="1", name="Jalsa", city="Bangalore", cuisines=["North Indian"]), 5.0),
        (Restaurant(id="2", name="Spice Elephant", city="Bangalore", cuisines=["Chinese"]), 4.0),
    ]
    
    prefs = UserPreference(location="Bangalore", cuisines=["North Indian"])
    
    print("\nCalling real LLM for 2 candidates...")
    recommendations = llm_client.generate_recommendations(prefs, candidates)
    
    assert len(recommendations) > 0
    for rec in recommendations:
        print(f"Rec: {rec.restaurant_id} - {rec.explanation}")
        assert rec.explanation != "Top match based on your location and preferences." # Ensure it's not the fallback
    
if __name__ == "__main__":
    try:
        test_real_llm_recommendation_smoke_test()
        print("\nReal LLM integration test passed!")
    except Exception as e:
        print(f"\nReal LLM integration test failed: {e}")
        raise
