import importlib

from src.data_ingestion.ingest import ingest_from_iterable


class _FakeSplit(list):
    pass


class _FakeDataset(dict):
    pass


def test_load_restaurants_from_hf_uses_ingest_from_iterable(monkeypatch):
    from src.data_ingestion import hf_client as hf_module

    # Prepare fake data similar to the HF dataset schema
    fake_split = _FakeSplit(
        [
            {
                "Restaurant ID": 10,
                "Restaurant Name": "Test Place",
                "City": "Bangalore",
                "Cuisines": "South Indian",
                "Aggregate rating": 4.2,
                "Average Cost for two": 300,
                "Votes": 20,
            }
        ]
    )

    fake_ds = _FakeDataset(train=fake_split)

    def _fake_load_dataset(*args, **kwargs):
        return fake_ds

    monkeypatch.setattr(hf_module, "load_dataset", _fake_load_dataset)

    importlib.reload(hf_module)
    from src.data_ingestion.hf_client import load_restaurants_from_hf

    restaurants = load_restaurants_from_hf()

    assert len(restaurants) == 1
    r = restaurants[0]
    assert r.name == "Test Place"
    assert r.city == "Bangalore"

