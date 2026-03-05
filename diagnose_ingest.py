from src.data_ingestion.hf_client import load_restaurants_from_hf

def diagnose():
    print("Attempting to load restaurants from HF...")
    try:
        recs = load_restaurants_from_hf(limit=100)
        print(f"Loaded {len(recs)} restaurants.")
        if recs:
            for r in recs[:5]:
                print(f" - {r.name} in {r.city} (ID: {r.id})")
        else:
            print("No restaurants returned!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    diagnose()
