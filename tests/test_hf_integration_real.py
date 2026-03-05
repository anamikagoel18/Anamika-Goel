import pytest
from src.data_ingestion.hf_client import load_restaurants_from_hf
from src.domain.models import Restaurant

def test_real_hf_ingestion_smoke_test():
    """
    Smoke test to ensure we can actually pull data from Hugging Face
    and map it to our Restaurant model without crashing.
    """
    # Fetch a very small sample to keep the test fast
    limit = 5
    restaurants = load_restaurants_from_hf(limit=limit)
    
    assert isinstance(restaurants, list)
    # We expect at least some data if the dataset is available
    assert len(restaurants) > 0
    assert len(restaurants) <= limit
    
    for r in restaurants:
        assert isinstance(r, Restaurant)
        assert r.id is not None
        assert r.name is not None
        assert r.city is not None
        # Print a sample for visual verification in logs
        print(f"Imported: {r.name} in {r.city} (Rating: {r.rating})")

if __name__ == "__main__":
    # Allow running directly for quick feedback
    try:
        test_real_hf_ingestion_smoke_test()
        print("\nSmoke test passed!")
    except Exception as e:
        print(f"\nSmoke test failed: {e}")
        raise
