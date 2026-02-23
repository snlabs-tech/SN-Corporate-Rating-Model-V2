# SN-Corporate-Rating-Model-V2/tests/test_model.py

# tests/test_model.py
from sn_rating.model import RatingModel
from sn_rating.datamodel import QuantInputs, QualInputs
from sn_rating import config


def _setup_simple_config():
    # Rating scale and cutoffs
    config.RATING_SCALE[:] = ["AAA", "AA", "A", "BBB", "BB", "B"]
    config.SCORE_TO_RATING.clear()
    config.SCORE_TO_RATING.extend([
        (80.0, "AAA"),
        (70.0, "AA"),
        (60.0, "A"),
        (50.0, "BBB"),
        (40.0, "BB"),
        (0.0, "B"),
    ])

    # Ratio families and grids
    config.RATIO_FAMILY.clear()
    config.RATIO_FAMILY.update({
        "interest_coverage": "coverage",
        "dscr": "coverage",
        "lt_debt_to_ebitda": "leverage",
    })
    config.RATIO_GRIDS.clear()
    config.RATIO_GRIDS.update({
        "interest_coverage": [
            (0.0, 1.0, 0.0),
            (1.0, 2.0, 40.0),
            (2.0, 5.0, 70.0),
            (5.0, 999.0, 90.0),
        ],
        "dscr": [
            (0.0, 0.8, 0.0),
            (0.8, 1.0, 40.0),
            (1.0, 1.5, 70.0),
            (1.5, 999.0, 90.0),
        ],
        "lt_debt_to_ebitda": [
            (0.0, 1.0, 90.0),
            (1.0, 3.0, 70.0),
            (3.0, 5.0, 40.0),
            (5.0, 999.0, 10.0),
        ],
    })

    # Qualitative scale
    config.QUAL_SCORE_SCALE.clear()
    config.QUAL_SCORE_SCALE.update({
        1: 20.0,
        2: 40.0,
        3: 60.0,
        4: 80.0,
        5: 100.0,
    })

    # Distress bands (simple)
    config.DISTRESS_BANDS.clear()
    config.DISTRESS_BANDS.update({
        "interest_coverage": [
            (1.0, -2),  # if <1.0 → -2 notches
        ],
        "dscr": [
            (1.0, -1),
        ],
        "altman_z": [
            (1.8, -2),
        ],
    })
    config.MAX_DISTRESS_NOTCHES = -4
    config.RATING_WEIGHTS["quantitative"] = None
    config.RATING_WEIGHTS["qualitative"] = None


def test_compute_final_rating_basic_no_caps():
    _setup_simple_config()

    quant = QuantInputs(
        fin_t0={
            "interest_coverage": 3.0,
            "dscr": 1.2,
            "lt_debt_to_ebitda": 2.5,
        },
        fin_t1={
            "interest_coverage": 2.5,
            "dscr": 1.1,
            "lt_debt_to_ebitda": 2.8,
        },
        fin_t2={},
        components_t0={
            "working_capital": 100.0,
            "total_assets": 200.0,
            "retained_earnings": 50.0,
            "ebit": 20.0,
            "market_value_equity": 300.0,
            "total_liabilities": 150.0,
            "sales": 400.0,
        },
        components_t1={},
        components_t2={},
        peers_t0={
            "interest_coverage": [2.0, 2.5, 3.0],
        },
    )

    qual = QualInputs(
        factors_t0={
            "management_quality": 4,
            "industry_position": 3,
        },
        factors_t1={},
    )

    model = RatingModel(cp_name="TestCorp")
    output = model.compute_final_rating(
        quant_inputs=quant,
        qual_inputs=qual,
        enable_hardstops=True,
        enable_sovereign_cap=False,
    )

    # basic assertions: structure and plausible ranges
    assert output.issuer_name == "TestCorp"
    assert 0.0 <= output.quantitative_score <= 100.0
    assert 0.0 <= output.qualitative_score <= 100.0
    assert 0.0 <= output.combined_score <= 100.0
    assert output.base_rating in config.RATING_SCALE
    assert output.final_rating in config.RATING_SCALE
    assert isinstance(output.rating_explanation, str)
    assert "final issuer rating" in output.rating_explanation.lower()


def test_compute_final_rating_with_sovereign_cap_binding():
    _setup_simple_config()

    quant = QuantInputs(
        fin_t0={
            "interest_coverage": 6.0,  # good metrics → high score
            "dscr": 2.0,
            "lt_debt_to_ebitda": 1.0,
        },
        fin_t1={},
        fin_t2={},
        components_t0={
            "working_capital": 200.0,
            "total_assets": 300.0,
            "retained_earnings": 80.0,
            "ebit": 40.0,
            "market_value_equity": 500.0,
            "total_liabilities": 200.0,
            "sales": 600.0,
        },
        components_t1={},
        components_t2={},
        peers_t0={},
    )

    qual = QualInputs(
        factors_t0={"management_quality": 5},
        factors_t1={},
    )

    model = RatingModel(cp_name="CapTest")
    sovereign_rating = "A"
    sovereign_outlook = "Stable"

    out = model.compute_final_rating(
        quant_inputs=quant,
        qual_inputs=qual,
        sovereign_rating=sovereign_rating,
        sovereign_outlook=sovereign_outlook,
        enable_hardstops=False,
        enable_sovereign_cap=True,
    )

    assert out.final_rating <= sovereign_rating or out.final_rating == sovereign_rating
    assert out.sovereign_cap_binding in {True, False}
    if out.sovereign_cap_binding:
        assert out.final_rating == sovereign_rating
