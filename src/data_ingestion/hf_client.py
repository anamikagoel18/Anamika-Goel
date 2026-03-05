from __future__ import annotations

from typing import List, Optional

from src.data_ingestion.ingest import ingest_from_iterable
from src.domain.models import Restaurant

# Import guard so tests that monkeypatch `load_dataset` before reloading this
# module don't lose their patch on reload.
try:  # pragma: no cover - trivial guard
    load_dataset  # type: ignore[name-defined]
except NameError:  # pragma: no cover
    from datasets import load_dataset  # type: ignore[assignment]


def load_restaurants_from_hf(limit: Optional[int] = None, force_refresh: bool = False) -> List[Restaurant]:
    """
    Load restaurant data. Prioritizes local `data/restaurants.json` if it exists,
    otherwise fetches from Hugging Face.
    """
    import json
    import os
    local_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "restaurants.json"))
    
    if os.path.exists(local_path) and not force_refresh:
        print(f"INFO: Loading restaurants from local cache: {local_path}")
        with open(local_path, "r", encoding="utf-8") as f:
            raw_items = json.load(f)
            if limit is not None:
                raw_items = raw_items[:limit]
            # Convert dicts back to Restaurant models
            return [Restaurant(**item) for item in raw_items]

    print("INFO: Fetching fresh data from Hugging Face (applying latest mapping)...")
    ds = load_dataset("ManikaSaini/zomato-restaurant-recommendation")
    # Many datasets expose the default split as "train"
    split = ds["train"] if "train" in ds else next(iter(ds.values()))

    if limit is not None:
        split = split.select(range(min(limit, len(split))))

    raw_items = [dict(row) for row in split]
    restaurants: List[Restaurant] = ingest_from_iterable(raw_items)
    
    # Save to cache
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    with open(local_path, "w", encoding="utf-8") as f:
        # Restaurant is a Pydantic model, use model_dump()
        json.dump([r.model_dump() for r in restaurants], f, indent=2)
    print(f"INFO: Saved {len(restaurants)} records to cache at {local_path}")
    
    return restaurants

