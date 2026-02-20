# SN — Corporate Rating Model (V2)

This repository contains **V2** of the SN corporate credit rating model: a deterministic, rules‑based rating engine that translates standardized financial and qualitative inputs into an internal issuer rating and outlook on an AAA–C‑style scale. The model is designed to differentiate **structural** credit quality rather than to forecast short‑term default events and prioritizes transparency and auditability over statistical optimization.

> V1 (`SN_CorporateRatingModel`) is kept as a **deprecated prototype** for educational purposes.  
> V2 (`RatingModel`) is the **recommended** version for any analysis.

For the full methodology (conceptual framework, ratio families, overlays, limitations, and boundaries), see `methodology.md`.

---

## 1. Executive Summary

The V2 corporate rating model provides a transparent, rule‑based framework to assign long‑term issuer ratings to corporate obligors using standardized financial ratios, a small set of qualitative factors, and optional structured overlays for distress and sovereign risk.  

Core characteristics:

- Outputs ratings on an internal long‑term scale conceptually aligned with AAA–C, with a clear investment‑grade / speculative‑grade boundary.  
- Separates **quantitative** (financial ratios, Altman Z‑score) and **qualitative** (1–5 expert scores) inputs, then combines them with effective weights.  
- Uses monotone, contiguous **ratio grids** as the core engine, with optional **Altman‑style distress** and **sovereign‑cap** overlays that can be switched on for more conservative treatment of distress and country risk.  
- Is **point‑in‑time and deterministic**: for any given set of inputs, it will always produce the same rating and outlook, with no randomness or hidden state in the calculation.  

The model is intended as an internal **decision‑support** tool and primary quantitative anchor within a broader credit framework, not as a purely predictive PD or capital model.

---

## 2. Internal Rating Scale

The model’s internal rating scale is conceptually aligned with the familiar AAA–C framework used by many agencies, but does **not** include an explicit `D` (default) category.

- **Symbolic mapping**  
  Ratings range from `AAA` (highest credit quality) down through `AA`, `A`, `BBB`, `BB`, `B`, to `CCC`/`CC`/`C`, where `C` denotes the lowest credit quality bucket used by this model (near‑default or default‑like situations in practice).

- **Investment‑grade boundary**  
  Ratings of `BBB−` and above are treated as **investment grade**; ratings below `BBB−` are **speculative‑grade**.

- **Ordinal meaning**  
  The scale provides an **ordinal ranking of relative long‑term default risk**, not a direct PD estimate or spread level. Higher ratings imply strictly lower perceived default risk than lower ratings, but no specific PD is embedded in a symbol.

Internally, the engine operates on a 0–100 score, which is mapped to rating symbols via `SCORE_TO_RATING`.

---

## 3. Scope and Intended Use

- **Covered population**  
  Non‑financial corporates with reasonably standard financial reporting (e.g. IFRS, US GAAP or similar), including industrials, services, and many infrastructure‑like entities. The model is **not** designed for banks, insurers, project finance SPVs, or highly structured vehicles.

- **Typical use cases**  
  - Internal credit grading and limit setting  
  - Portfolio monitoring and watch‑list identification  
  - Input into pricing / RAROC frameworks  
  - Support for internal and external communication where an internal rating scale is used

- **Exclusions / adaptations**  
  Sectors with highly idiosyncratic drivers (early‑stage venture, commodity trading houses, complex conglomerates) may require additional sector overlays or bespoke adjustments beyond this generic V2 framework.

---

## 4. Conceptual Framework (High‑Level)

V2 is an expert‑designed, rule‑based scorecard that:

- Ingests **QuantInputs** (financial ratios and components) and **QualInputs** (1–5 qualitative scores).  
- Scores each quantitative ratio via **RATIO_GRIDS** and aggregates them into ratio‑family subscores (e.g. leverage, coverage, cash flow, profitability, liquidity, Altman Z).  
- Computes an aggregate **quantitative score**, a **qualitative score**, and a **combined score** using effective weights based on counts or configured weights.  
- Maps the combined score to a **base rating**, then (optionally) applies:
  - Distress hardstops / notching (downward only), when hardstops are enabled  
  - A sovereign cap overlay, when sovereign capping is enabled

Detailed descriptions of ratio families, Altman Z, qualitative factors, and overlays are documented in `methodology.md`.

---

## 5. Outputs

The main entry point is `RatingModel.compute_final_rating(...)`, which returns a `RatingOutputs` object:

- Scores: `quantitative_score`, `qualitative_score`, `combined_score`, `peer_score`  
- Ratings: `base_rating`, `hardstop_rating`, `final_rating`, `distress_notches`  
- Overlays & outlook: `sovereign_rating`, `sovereign_outlook`, `outlook`, `hardstop_triggered`, `flags`  
- Diagnostics: `bucket_avgs`, `altman_z_t0`, `hardstop_details`, `rating_explanation`

`RatingOutputs` is the **authoritative record** of each run and can be stored or logged for replay, audit, or reporting.

---

## 6. Using the Model (Code Sketch)

```python
from rating_model import RatingModel, QuantInputs, QualInputs  # adapt path as needed

quant_inputs = QuantInputs(
    fin_t0=..., fin_t1=..., fin_t2=...,
    components_t0=..., components_t1=..., components_t2=...,
    peers_t0=...,
)

qual_inputs = QualInputs(
    factors_t0=...,  # 1–5 (1 weakest, 5 strongest)
    factors_t1=...,
)

model = RatingModel(cp_name="SampleCorp")

result = model.compute_final_rating(
    quant_inputs,
    qual_inputs,
    sovereign_rating="BBB",        # or None
    sovereign_outlook="Stable",    # or None
    enable_hardstops=True,
    enable_sovereign_cap=True,
)

print(result.final_rating, result.outlook)
print(result.rating_explanation)
