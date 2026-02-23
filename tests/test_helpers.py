# SN-Corporate-Rating-Model-V2/tests/test_helpers.py
import math

from sn_rating.helpers import (
    score_ratio,
    score_qual_factor_numeric,
    compute_altman_z_from_components,
    compute_peer_score,
    score_to_rating,
    safe_score_to_rating,
    move_notches,
    apply_sovereign_cap,
    compute_effective_weights,
    get_rating_band,
    derive_outlook_band_only,
    derive_outlook_with_distress_trend,
)
from sn_rating import config


def test_score_ratio_basic():
    # arrange a simple grid
    config.RATIO_GRIDS["test_ratio"] = [
        (0.0, 1.0, 10.0),
        (1.0, 2.0, 20.0),
    ]
    assert score_ratio("test_ratio", 0.5) == 10.0
    assert score_ratio("test_ratio", 1.5) == 20.0
    assert score_ratio("test_ratio", 2.5) is None
    assert score_ratio("unknown_ratio", 0.5) is None


def test_score_qual_factor_numeric():
    config.QUAL_SCORE_SCALE.clear()
    config.QUAL_SCORE_SCALE.update({1: 20.0, 3: 60.0, 5: 100.0})
    assert score_qual_factor_numeric(1) == 20.0
    assert score_qual_factor_numeric(3) == 60.0
    assert score_qual_factor_numeric(5) == 100.0
    assert score_qual_factor_numeric(2) is None


def test_compute_altman_z_from_components():
    z = compute_altman_z_from_components(
        working_capital=100.0,
        total_assets=200.0,
        retained_earnings=50.0,
        ebit=20.0,
        market_value_equity=300.0,
        total_liabilities=150.0,
        sales=400.0,
    )
    assert not math.isnan(z)
    # basic sanity: positive and in a plausible range
    assert z > 0


def test_compute_peer_score_tiers():
    fin_current = {"ratio1": 100.0, "ratio2": 100.0}
    peers = {
        "ratio1": [100.0, 100.0],  # equal
        "ratio2": [200.0, 200.0],  # issuer underperforms
    }
    score = compute_peer_score(fin_current, peers)
    assert score in {0.0, 25.0, 50.0, 75.0, 100.0}


def test_score_to_rating_and_safe_score_to_rating():
    config.SCORE_TO_RATING.clear()
    config.SCORE_TO_RATING.extend([
        (80.0, "A"),
        (60.0, "BBB"),
        (0.0, "B"),
    ])
    assert score_to_rating(85.0) == "A"
    assert score_to_rating(60.0) == "BBB"
    assert score_to_rating(10.0) == "B"
    assert safe_score_to_rating(-10.0) == "N/R"


def test_move_notches_and_apply_sovereign_cap():
    config.RATING_SCALE[:] = ["AAA", "AA", "A", "BBB", "BB"]
    assert move_notches("A", -1) == "BBB"   # one notch down
    assert move_notches("A", 0) == "A"
    assert move_notches("A", 10) == "AAA"   # clamped at best
    assert apply_sovereign_cap("A", "BBB") == "BBB"
    assert apply_sovereign_cap("A", None) == "A"


def test_compute_effective_weights_auto_and_manual():
    config.RATING_WEIGHTS["quantitative"] = None
    config.RATING_WEIGHTS["qualitative"] = None
    wq, wl = compute_effective_weights(3, 1)
    assert wq == 3 / 4
    assert wl == 1 / 4

    config.RATING_WEIGHTS["quantitative"] = 0.7
    config.RATING_WEIGHTS["qualitative"] = 0.3
    wq2, wl2 = compute_effective_weights(3, 1)
    assert (wq2, wl2) == (0.7, 0.3)


def test_get_rating_band_and_outlook_band_only():
    config.SCORE_TO_RATING.clear()
    config.SCORE_TO_RATING.extend([
        (80.0, "A"),
        (60.0, "BBB"),
        (0.0, "B"),
    ])
    band_min, band_max = get_rating_band("BBB")
    assert band_min == 60.0
    assert band_max == 79.0
    assert derive_outlook_band_only(79.9, "BBB") == "Positive"
    assert derive_outlook_band_only(60.0, "BBB") == "Negative"
    assert derive_outlook_band_only(70.0, "BBB") == "Stable"


def test_derive_outlook_with_distress_trend():
    base_outlook = "Stable"
    distress_notches = -2
    fin_t0 = {"interest_coverage": 3.0, "dscr": 2.0, "altman_z": 2.5}
    fin_t1 = {"interest_coverage": 2.0, "dscr": 1.5, "altman_z": 2.0}
    # improving between t1 -> t0
    outlook = derive_outlook_with_distress_trend(
        base_outlook, distress_notches, fin_t0, fin_t1
    )
    assert outlook in {"Stable", "Negative"}  # depending on logic; here we just sanity check

    # if no distress, should return base_outlook
    outlook2 = derive_outlook_with_distress_trend(
        base_outlook, 0, fin_t0, fin_t1
    )
    assert outlook2 == base_outlook
