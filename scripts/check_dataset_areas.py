
from datasets import load_dataset
import pandas as pd

def check_dataset():
    print("Loading dataset...")
    ds = load_dataset("ManikaSaini/zomato-restaurant-recommendation", split="train")
    df = pd.DataFrame(ds)
    
    print(f"Total rows: {len(df)}")
    
    if "listed_in(city)" in df.columns:
        unique_cities = df["listed_in(city)"].nunique()
        print(f"Unique 'listed_in(city)': {unique_cities}")
        print(df["listed_in(city)"].unique()[:10])
    
    if "location" in df.columns:
        unique_locations = df["location"].nunique()
        print(f"Unique 'location': {unique_locations}")
        print(df["location"].unique()[:10])

    if "cuisines" in df.columns:
        unique_cuisines = df["cuisines"].nunique()
        print(f"Unique 'cuisines': {unique_cuisines}")

if __name__ == "__main__":
    check_dataset()
