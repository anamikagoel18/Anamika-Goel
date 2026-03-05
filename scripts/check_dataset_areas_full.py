
from datasets import load_dataset
import pandas as pd

def check_dataset():
    print("Loading full dataset...")
    ds = load_dataset("ManikaSaini/zomato-restaurant-recommendation", split="train")
    df = pd.DataFrame(ds)
    
    print(f"Total rows: {len(df)}")
    
    l_city = df["listed_in(city)"].nunique() if "listed_in(city)" in df.columns else 0
    loc = df["location"].nunique() if "location" in df.columns else 0
    
    print(f"Unique 'listed_in(city)': {l_city}")
    print(f"Unique 'location': {loc}")

if __name__ == "__main__":
    check_dataset()
