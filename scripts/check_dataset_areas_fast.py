
from datasets import load_dataset
import pandas as pd

def check_dataset():
    print("Loading 5000 rows...")
    # Load first 5000 rows to be fast
    ds = load_dataset("ManikaSaini/zomato-restaurant-recommendation", split="train[:5000]")
    df = pd.DataFrame(ds)
    
    print(f"Sample size: {len(df)}")
    
    if "listed_in(city)" in df.columns:
        unique_cities = df["listed_in(city)"].nunique()
        print(f"Unique 'listed_in(city)': {unique_cities}")
        print(sorted(df["listed_in(city)"].astype(str).unique())[:10])
    
    if "location" in df.columns:
        unique_locations = df["location"].nunique()
        print(f"Unique 'location': {unique_locations}")
        print(sorted(df["location"].astype(str).unique())[:10])

if __name__ == "__main__":
    check_dataset()
