from coinarb.models import Observation


def test_observation_has_reconciliation_fields():
    obs = Observation(
        "kitco",
        "US-AGE-1OZ-RANDOM-BU",
        "ask",
        4200.0,
        "https://example.test",
        "AGE",
        quantity_min=1,
        inventory_status="available",
    )
    assert obs.dealer_id == "kitco"
    assert obs.side == "ask"
    assert obs.price == 4200.0
    assert obs.source_url == "https://example.test"
