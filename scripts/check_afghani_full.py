
from datasets import load_dataset
import pandas as pd

def check_full_dataset():
    print("Loading full dataset to check for Afghani...")
    ds = load_dataset("ManikaSaini/zomato-restaurant-recommendation", split="train")
    df = pd.DataFrame(ds)
    
    print(f"Total rows in HF: {len(df)}")
    
    # Check for Afghani
    afghani = df[df['cuisines'].str.contains('Afghani', case=False, na=False)]
    print(f"Total Afghani in full HF: {len(afghani)}")
    
    if len(afghani) > 0:
        print("Sample areas for Afghani:")
        # Check 'location' and 'listed_in(city)'
        print(afghani[['name', 'location', 'listed_in(city)']].head(10))

if __name__ == "__main__":
    check_full_dataset()
