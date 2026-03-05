from datasets import load_dataset

def inspect_dataset():
    print("Loading dataset...")
    ds = load_dataset("ManikaSaini/zomato-restaurant-recommendation")
    print("\nDataset object:")
    print(ds)
    
    split_name = "train" if "train" in ds else next(iter(ds.values()))
    split = ds[split_name]
    
    print(f"\nInspecting split: {split_name}")
    print(f"Features: {split.features}")
    print("\nSample row:")
    print(split[0])

if __name__ == "__main__":
    inspect_dataset()
