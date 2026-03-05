from datasets import load_dataset
from collections import Counter

def check_dataset_cities():
    print("Loading dataset...")
    ds = load_dataset("ManikaSaini/zomato-restaurant-recommendation")
    split = ds["train"] if "train" in ds else next(iter(ds.values()))
    
    print(f"Total rows in dataset: {len(split)}")
    
    # Check first 10000 rows
    limit = 10000
    rows = split.select(range(min(limit, len(split))))
    
    city_counter = Counter()
    listed_in_city_counter = Counter()
    
    print(f"Scanning first {limit} rows...")
    for row in rows:
        city = row.get("City") or row.get("city")
        listed_in = row.get("listed_in(city)")
        
        if city: city_counter[city] += 1
        if listed_in: listed_in_city_counter[listed_in] += 1
        
    print("\n'City' field counts (first 10k):")
    for city, count in city_counter.most_common(10):
        print(f" - {city}: {count}")
        
    print("\n'listed_in(city)' field counts (first 10k):")
    for city, count in listed_in_city_counter.most_common(10):
        print(f" - {city}: {count}")

if __name__ == "__main__":
    check_dataset_cities()
