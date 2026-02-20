# SN — Corporate Rating Model (V2)

This repository contains **V2** of the SN corporate credit rating model: a deterministic, rules‑based rating engine that translates standardized financial and qualitative inputs into an internal issuer rating and outlook on an AAA–D‑style scale. The model is designed to differentiate **structural** credit quality rather than to forecast short‑term default events and prioritizes transparency, auditability, and governance over statistical optimization. 

> V1 (`SN_CorporateRatingModel`) is kept as a **deprecated prototype** for educational purposes.  
> V2 (`RatingModel`) is the **recommended** version for any analysis.

---

## 1. Executive Summary

The V2 corporate rating model provides a transparent, rule‑based framework to assign long‑term issuer ratings to corporate obligors using standardized financial ratios, a small set of qualitative factors, and optional structured overlays for distress and sovereign risk. 

Core characteristics:

- Outputs ratings on an internal long‑term scale conceptually aligned with AAA–D, with a clear investment‑grade / speculative‑grade boundary. 
- Separates **quantitative** (financial ratios, Altman Z‑score) and **qualitative** (1–5 expert scores) inputs, then combines them with effective weights.  
- Uses monotone, contiguous **ratio grids** and an Altman‑style distress overlay plus an optional **sovereign cap**.  
- Is explicitly through‑the‑cycle and **deterministic**: given the same inputs, the same rating and outlook are always produced.

The model is intended as an internal **decision‑support** tool and primary quantitative anchor within a broader credit framework, not as a purely predictive PD or capital model.

---

## 2. Internal Rating Scale

The model’s internal rating scale is conceptually aligned with the familiar AAA–D framework used by major agencies.

- **Symbolic mapping**  
  Ratings range from `AAA` (highest credit quality) down through `AA`, `A`, `BBB`, `BB`, `B`, `CCC`/`CC`/`C` to `D`, where `D` denotes default or near‑default situations.

- **Investment‑grade boundary**  
  Ratings of `BBB−` and above are treated as **investment grade**; ratings below `BBB−` are **speculative‑grade**.

- **Ordinal meaning**  
  The scale provides an **ordinal ranking of relative long‑term default risk**, not a direct PD estimate or spread level. Higher ratings imply strictly lower perceived default risk than lower ratings, but no specific PD is embedded in a symbol.

The numerical engine operates on a 0–100 internal score, which is then mapped to rating symbols via `SCORE_TO_RATING`.

---

## 3. Scope and Intended Use

- **Covered population**  
  Non‑financial corporates with reasonably standard financial reporting (e.g. IFRS, US GAAP or similar), including industrials, services, and many infrastructure‑like entities. The model is **not** designed for banks, insurers, project finance SPVs, or highly structured vehicles.

- **Typical use cases**  
  - Internal credit grading and limit setting  
  - Portfolio monitoring and watch‑list identification  
  - Input into pricing / RAROC frameworks  
  - Support for internal and external communication where an internal rating scale is used.

- **Exclusions / adaptations**  
  Sectors with highly idiosyncratic drivers (early‑stage venture, commodity trading houses, complex conglomerates) may require additional sector overlays or bespoke adjustments beyond this generic V2 framework.

---

## 4. Conceptual Framework

V2 is an expert‑designed, rule‑based scorecard that:

- Ingests **QuantInputs** (financial ratios and components) and **QualInputs** (1–5 scores).  
- Scores each quantitative ratio via **RATIO_GRIDS** and aggregates them into ratio‑family subscores (leverage, coverage, cash flow, profitability, liquidity, Altman Z).
- Computes an aggregate **quantitative score**, a **qualitative score**, and a **combined score** using effective weights based on counts or configured weights.  
- Maps the combined score to an **uncapped rating**, then applies overlays:
  - Distress hardstops / notching (downward only)  
  - Optional sovereign cap

The methodology is through‑the‑cycle and deterministic to maximize replicability and auditability.

---

## 5. Ratio Families and Inputs

### 5.1 Quantitative inputs (`QuantInputs`)

`QuantInputs` captures ratio data and components (e.g. for Altman Z) per period:

- `fin_t0`, `fin_t1`, `fin_t2`: dictionaries of financial **ratios**.  
- `components_t0`, `components_t1`, `components_t2`: components for Altman Z (working capital, total assets, retained earnings, EBIT, market value of equity, total liabilities, sales).
- `peers_t0`: peer group ratios for **relative positioning**.

Ratio coverage includes:

- **Leverage**: `debt_ebitda`, `net_debt_ebitda`, `debt_equity`, `debt_capital`, `ffo_debt`, `fcf_debt`  
- **Coverage**: `interest_coverage`, `fixed_charge_coverage`, `dscr`, `rollover_coverage`  
- **Profitability**: `ebitda_margin`, `ebit_margin`, `roa`, `roe`  
- **Liquidity / investment**: `capex_dep`, `current_ratio`  
- **Distress**: `altman_z` (or its components)

Each ratio is scored using a grid:

```python
RATIO_GRIDS[name] = [
    (low, high, score),  # low <= value < high
    ...
]
```
Grids are **monotone and contiguous**: more favorable economics always map to higher scores, and every real (non‑NaN) value falls into exactly one band per ratio. Missing or unscorable ratios are skipped, and the quantitative score is computed from available ratios only.

## 5.2 Altman Z‑score

If `altman_z` is not provided for `t0`, the model computes it from the standard components and weights:

- Working capital / total assets  
- Retained earnings / total assets  
- EBIT / total assets  
- Market value of equity / total liabilities  
- Sales / total assets  

The resulting Z‑score:

- Enters the **Altman** ratio family for scoring.  
- Feeds the **distress overlay**, with thresholds around the classic distress / grey / safe zones.

## 5.3 Qualitative inputs (`QualInputs`)

`QualInputs` captures 1–5 qualitative scores:

- `factors_t0`: primary qualitative assessment at `t0`.  
- `factors_t1`: optional prior‑period qualitative assessment for trend analysis in distress / outlook logic.

**V2 scale convention:**

- `1` = weakest  
- `5` = strongest  

Scores are mapped to 0–100 via `QUAL_SCORE_SCALE`:

- 5 → 100  
- 4 → 75  
- 3 → 50  
- 2 → 25  
- 1 → 0  

Example factor categories (flexible by key):

- Business and industry risk (e.g. `industry_risk`, `revenue_stability`)  
- Market position and diversification (`market_position`, `revenue_diversification`)  
- Management & governance (`management_quality`, `governance`, `financial_policy`)
- Liquidity and refinancing (`liquidity_profile`, `refinancing_risk`, `wc_management_quality`)  
- Country / legal environment (`sovereign_risk`, `legal_environment`)

Missing or invalid factors are skipped; all valid ones are equally weighted in the average qualitative score.

---

## 6. Overlays and Final Rating Logic

### 6.1 Distress overlay (hardstops and notching)

After computing the `uncapped_rating` from the combined score, the model applies a **distress overlay** that can only **downgrade**:

- `compute_distress_notches(fin_t0, altman_z)` evaluates distress indicators using `DISTRESS_BANDS`:
  - `interest_coverage`  
  - `dscr`  
  - `altman_z` (e.g. Z < distress threshold)

It returns:

- `distress_notches` (typically ≤ 0, capped by `MAX_DISTRESS_NOTCHES`)  
- `hardstop_details` (which ratio triggered what)

`move_notches(rating, notches)` then shifts the rating **down** the internal scale to produce the `hardstop_rating`.

The goal is to ensure that very weak coverage or Z‑scores **limit** the issuer’s rating, even if other metrics look stronger.

### 6.2 Sovereign cap overlay

The sovereign cap is an optional overlay applied to the post‑distress rating:

- `apply_sovereign_cap(issuer_grade, sovereign_grade)` ensures that, when enabled, the issuer rating does not exceed the mapped maximum relative to the sovereign rating.  
- If the cap binds and a `sovereign_outlook` is provided, the issuer’s outlook is anchored to the sovereign.

This reflects the empirical and conceptual view that most domestically‑anchored corporates should not be rated materially above their home sovereign absent strong mitigating factors.

### 6.3 Outlook logic

The outlook is derived in two stages:

1. **Band‑only outlook**

   - `derive_outlook_band_only(combined_score, final_rating)`  

   Within the rating band:

   - Scores near the **upper edge** → `Positive`  
   - Near the **lower edge** → `Negative`  
   - Mid‑band → `Stable`

2. **Distress trend adjustment**

   - `derive_outlook_with_distress_trend(base_outlook, distress_notches, fin_t0, fin_t1)`  

   If distress hardstops are active (negative notches applied), the outlook is adjusted based on **trends** in distress ratios (coverage, DSCR, Z‑score) between `t1` and `t0`:

   - Improving distress metrics → at most `Stable`  
   - Deteriorating metrics → `Negative`

**Additional guards:**

- If `final_rating == "AAA"` and the computed outlook is `Positive`, it is forced to `Stable` (no `AAA Positive` combination).  
- If a binding sovereign cap and `sovereign_outlook` are present, that outlook can override the issuer‑derived outlook.

---

## 7. Limitations

Key limitations, consistent with agency‑style methodologies, are:

### Historical financial reliance

The model uses lagged financials; it may under‑react to sudden changes between reporting dates, especially for event‑driven credits.

### Expert‑driven thresholds and weights

Ratio breakpoints and weights are designed by expert judgement and market practice rather than fully optimized on historical default data; calibration to PD is outside the V2 scope.

### Limited explicit qualitative modeling

Governance, strategy, competition, and ESG factors are captured via generic qualitative scores but not via sector‑specific, data‑heavy models.

### Through‑the‑cycle emphasis

The focus on structural and normalized metrics improves stability but can slow response to regime shifts or severe macro shocks.

### Model‑risk and parameter uncertainty

As with any scorecard, specification and parameter risk exist and must be managed via validation, monitoring, and challenger analysis.

---

## 8. Model Boundaries (“What This Model Is Not”)

This V2 model is **not**:

- A regulatory **IRB** model, and it is **not calibrated** to Basel capital requirements.
- A **market‑implied** model based on bond or CDS spreads.  
- A **structural asset‑value model** in the Merton tradition that explicitly models firm asset value and volatility.   
- A standalone **PD/LGD engine** for capital or pricing.

It is an internal, deterministic **rating scorecard** that provides an ordinal ranking of credit quality to be combined with other models and expert judgement.

---

## 9. Governance and Outputs

### 9.1 `RatingOutputs` as authoritative record

`RatingOutputs` is the **authoritative record** of each model run:

- Scores: `quantitative_score`, `qualitative_score`, `combined_score`, `peer_score`  
- Ratings: `uncapped_rating`, `hardstop_rating`, `final_rating`, `distress_notches`  
- Overlays & outlook: `sovereign_rating`, `sovereign_outlook`, `outlook`, `hardstop_triggered`, `flags`  
- Diagnostics: `bucket_avgs`, `altman_z_t0`, `hardstop_details`, `rating_explanation`

This supports full replay, explainability, and integration into audit and workflow systems. 

### 9.2 Governance philosophy

The model is governed under a formal model‑risk framework:

- Transparent, deterministic implementation in Python with documented grids and overlays.  
- Separation of development / maintenance from independent validation.  
- Regular validation, back‑testing, and monitoring of performance metrics and overrides.  
- Boolean flags for data gaps and configuration issues to support exception handling and governance workflows.
  
## 10. Using the Model (Code Sketch)

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

