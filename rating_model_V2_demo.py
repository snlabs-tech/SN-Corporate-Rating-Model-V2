# SN-Corporate-Rating-Model-V2

import logging

from sn_rating_v2 import QuantInputs, QualInputs, RatingModel


def main() -> None:
    logging.basicConfig(level=logging.INFO)

    # --- Financial ratios (t0, t1, t2) ---

    fin_t0 = {
        "debt_ebitda": 3.2,
        "net_debt_ebitda": 2.8,
        "debt_equity": 1.5,
        "debt_capital": 0.55,
        "ffo_debt": 0.18,
        "fcf_debt": 0.12,
        "interest_coverage": 0.8,
        "fixed_charge_coverage": 1.4,
        "dscr": 0.95,
        "ebitda_margin": 0.18,
        "ebit_margin": 0.12,
        "roa": 0.055,
        "roe": 0.11,
        "capex_dep": 1.3,
        "current_ratio": 1.3,
        "rollover_coverage": 1.1,
    }

    fin_t1 = {
        "debt_ebitda": 3.6,
        "net_debt_ebitda": 3.1,
        "debt_equity": 1.6,
        "debt_capital": 0.57,
        "ffo_debt": 0.17,
        "fcf_debt": 0.10,
        "interest_coverage": 1.2,
        "fixed_charge_coverage": 1.6,
        "dscr": 1.05,
        "ebitda_margin": 0.165,
        "ebit_margin": 0.11,
        "roa": 0.052,
        "roe": 0.105,
        "capex_dep": 1.2,
        "current_ratio": 1.2,
        "rollover_coverage": 1.05,
    }

    fin_t2 = {
        "debt_ebitda": 3.9,
        "net_debt_ebitda": 3.4,
        "debt_equity": 1.7,
        "debt_capital": 0.60,
        "ffo_debt": 0.16,
        "fcf_debt": 0.09,
        "interest_coverage": 1.5,
        "fixed_charge_coverage": 1.8,
        "dscr": 1.10,
        "ebitda_margin": 0.155,
        "ebit_margin": 0.10,
        "roa": 0.050,
        "roe": 0.10,
        "capex_dep": 1.1,
        "current_ratio": 1.1,
        "rollover_coverage": 1.0,
    }

    # --- Altman Z components (t0, t1, t2) ---

    components_t0 = {
        "working_capital": 120.0,
        "total_assets": 1000.0,
        "retained_earnings": 200.0,
        "ebit": 80.0,
        "market_value_equity": 600.0,
        "total_liabilities": 400.0,
        "sales": 900.0,
    }

    components_t1 = {
        "working_capital": 110.0,
        "total_assets": 950.0,
        "retained_earnings": 180.0,
        "ebit": 75.0,
        "market_value_equity": 580.0,
        "total_liabilities": 370.0,
        "sales": 880.0,
    }

    components_t2 = {
        "working_capital": 100.0,
        "total_assets": 900.0,
        "retained_earnings": 160.0,
        "ebit": 70.0,
        "market_value_equity": 550.0,
        "total_liabilities": 350.0,
        "sales": 860.0,
    }

    # --- Peer data (t0) ---

    peers_t0 = {
        "debt_ebitda": [2.8, 3.0, 3.1],
        "net_debt_ebitda": [2.5, 2.7, 2.9],
        "debt_equity": [1.3, 1.4, 1.5],
        "debt_capital": [0.50, 0.52, 0.54],
        "ffo_debt": [0.20, 0.22, 0.24],
        "fcf_debt": [0.14, 0.16, 0.18],
        "interest_coverage": [2.0, 2.5, 3.0],
        "fixed_charge_coverage": [1.8, 2.0, 2.2],
        "dscr": [1.2, 1.3, 1.4],
        "ebitda_margin": [0.17, 0.18, 0.19],
        "ebit_margin": [0.115, 0.125, 0.13],
        "roa": [0.055, 0.06, 0.065],
        "roe": [0.11, 0.115, 0.12],
        "capex_dep": [1.1, 1.2, 1.3],
        "current_ratio": [1.2, 1.3, 1.4],
        "rollover_coverage": [1.1, 1.2, 1.3],
    }

    quant_inputs = QuantInputs(
        fin_t0=fin_t0,
        fin_t1=fin_t1,
        fin_t2=fin_t2,
        components_t0=components_t0,
        components_t1=components_t1,
        components_t2=components_t2,
        peers_t0=peers_t0,
    )

    # --- Qualitative factors ---

    qual_t0 = {
        "industry_risk": 3,
        "market_position": 5,
        "revenue_diversification": 5,
        "revenue_stability": 4,
        "business_model_resilience": 4,
        "management_quality": 4,
        "governance": 4,
        "financial_policy": 3,
        "sovereign_risk": 3,
        "legal_environment": 4,
        "transparency": 4,
        "liquidity_profile": 3,
        "wc_management_quality": 4,
        "refinancing_risk": 3,
    }
    qual_t1 = qual_t0.copy()

    qual_inputs = QualInputs(
        factors_t0=qual_t0,
        factors_t1=qual_t1,
    )

    # --- Sovereign inputs ---

    sample_sovereign_rating = "A-"
    sample_sovereign_outlook = "Negative"

    # --- Run model ---

    model = RatingModel(cp_name="SampleCorp")
    out = model.compute_final_rating(
        quant_inputs,
        qual_inputs,
        sovereign_rating=sample_sovereign_rating,
        sovereign_outlook=sample_sovereign_outlook,
        enable_hardstops=False,
        enable_sovereign_cap=True,
    )

    summary = {
        "issuer_name": out.issuer_name,
        "quantitative_score": round(out.quantitative_score, 1),
        "qualitative_score": round(out.qualitative_score, 1),
        "combined_score": round(out.combined_score, 1),
        "peer_score": out.peer_score,
        "base_rating": out.base_rating,
        "distress_notches": out.distress_notches,
        "hardstop_rating": out.hardstop_rating,
        "final_rating": out.final_rating,
        "outlook": out.outlook,
        "hardstop_triggered": out.hardstop_triggered,
        "hardstop_details": out.hardstop_details,
        "sovereign_rating": out.sovereign_rating,
        "sovereign_outlook": out.sovereign_outlook,
        "bucket_avgs": out.bucket_avgs,
        "altman_z_t0": out.altman_z_t0,
        "flags": out.flags,
        "rating_explanation": out.rating_explanation,
    }

    for k, v in summary.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
