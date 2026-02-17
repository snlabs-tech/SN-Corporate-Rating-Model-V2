# SN — Corporate Rating Model (V2)

This repository contains **V2** of the SN corporate credit rating model: a rule‑based, multi‑period rating engine that combines quantitative financial metrics, qualitative assessments, peer benchmarking, distress hardstops, and an optional sovereign cap into a final issuer rating and outlook.

> V1 (`SN_CorporateRatingModel`) is kept as a **deprecated prototype** for educational purposes.  
> V2 (`RatingModel`) is the **recommended** version for any analysis.

---

## 1. Core concepts

V2 is a deterministic, transparent rating engine that:

- Uses a 0–100 internal score mapped to a granular rating scale from `AAA` down to `C`.
- Separates **quantitative** (financial) and **qualitative** (expert judgement) inputs, then combines them with effective weights.
- Incorporates **multi‑period data** (three years), **Altman Z‑score**, **peer benchmarking**, and **distress hardstops**.
- Optionally applies a **sovereign cap** and derives an **outlook** based on band position and distress trends. [web:21][web:22][web:29][web:77]

The main entry point is the `RatingModel.compute_final_rating(...)` method, which returns a rich `RatingOutputs` object including diagnostic fields and a human‑readable explanation string.

---

## 2. Key components

### 2.1 Data structures

- `QuantInputs`  
  Holds quantitative inputs:
  - `fin_t0`, `fin_t1`, `fin_t2`: dictionaries of financial ratios for three time points.
  - `components_t0`, `components_t1`, `components_t2`: Altman Z components (working capital, total assets, etc.).
  - `peers_t0`: peer group ratios for relative positioning.

- `QualInputs`  
  Holds qualitative inputs:
  - `factors_t0`, `factors_t1`: dictionaries of 1–5 qualitative scores (t0 primary, t1 for trend in distress outlook).

- `RatingOutputs`  
  Rich result object with:
  - Scores: `quantitative_score`, `qualitative_score`, `combined_score`, `peer_score`.
  - Ratings: `uncapped_rating`, `hardstop_rating`, `final_rating`, `distress_notches`.
  - Outlook & caps: `sovereign_rating`, `sovereign_outlook`, `outlook`, `hardstop_triggered`, `flags`.
  - Diagnostics: `bucket_avgs` (per ratio family), `altman_z_t0`, `hardstop_details`, `rating_explanation`.

### 2.2 RatingModel

- `RatingModel(cp_name: str)`  
  Main class representing the corporate issuer.

Core methods:

- `compute_quantitative(quant_inputs)`  
  - Ensures `altman_z` is present (either provided directly or computed from components via the classic Altman Z formula). [web:21][web:22]  
  - Scores each ratio using `RATIO_GRIDS` and groups them into families (`leverage`, `coverage`, `profit`, `other`, `altman`).  
  - Computes a **peer positioning score** via `compute_peer_score`, comparing issuer ratios to peer averages. [web:29][web:77]  
  - Outputs aggregate `quantitative_score`, optional `peer_score`, per‑bucket averages, and `altman_z`.

- `compute_qualitative(qual_inputs)`  
  - Maps 1–5 qualitative scores to 0–100 via `QUAL_SCORE_SCALE`.  
  - Returns an average `qualitative_score` and the count of valid qualitative items.

- `compute_distress_notches(fin_t0, altman_z)`  
  - Applies **distress hardstops** based on `interest_coverage`, `dscr`, and `altman_z`, using `DISTRESS_BANDS` and `MAX_DISTRESS_NOTCHES`.  
  - Returns total **notch downgrades** and a dict of triggered ratios.

- `compute_final_rating(...)`  
  End‑to‑end engine:
  1. Compute quantitative and qualitative scores.
  2. Derive effective weights via `compute_effective_weights` (from configured weights or counts of quant vs qual factors).
  3. Compute `combined_score` and `uncapped_rating` via `score_to_rating`.
  4. Apply distress hardstops via `compute_distress_notches` and `move_notches` → `hardstop_rating`.
  5. Optionally apply a **sovereign cap** via `apply_sovereign_cap` → `final_rating`.
  6. Derive base outlook from band position (`derive_outlook_band_only`) and adjust with distress trends (`derive_outlook_with_distress_trend`).
  7. Build a narrative `rating_explanation` summarizing the logic.

---

## 3. Inputs and scales

### 3.1 Quantitative ratios

`fin_t0`, `fin_t1`, `fin_t2` use standard corporate ratios, e.g.:

- Leverage: `debt_ebitda`, `net_debt_ebitda`, `debt_equity`, `debt_capital`, `ffo_debt`, `fcf_debt`
- Coverage: `interest_coverage`, `fixed_charge_coverage`, `dscr`
- Profitability: `ebitda_margin`, `ebit_margin`, `roa`, `roe`
- Liquidity/other: `capex_dep`, `current_ratio`, `rollover_coverage`
- Distress: `altman_z` (or components to compute it)

Each ratio is scored using `RATIO_GRIDS[name] = [(low, high, score), ...]`, with scores in `{0, 25, 50, 75, 100}` and intuitive monotonicity (better ratios → higher scores). [web:21][web:22]

### 3.2 Altman Z‑score

If `altman_z` is missing, the model computes it from components:

- Working capital / total assets  
- Retained earnings / total assets  
- EBIT / total assets  
- Market value of equity / total liabilities  
- Sales / total assets

Then applies the standard Z‑score weights, giving a distress indicator that feeds both the quantitative bucket and the hardstop logic. [web:21][web:22]

### 3.3 Qualitative factors (V2 convention)

In **V2**, the qualitative scale is:

- `1` = weakest  
- `5` = strongest  

and mapped as:

- 5 → 100, 4 → 75, 3 → 50, 2 → 25, 1 → 0 (`QUAL_SCORE_SCALE`).

This is **inverted vs V1**, where 1 was strongest and 5 weakest. V2’s direction is chosen for consistency with common “higher = better” Likert‑style scoring. [web:59]

Typical qualitative dimensions (flexible, user‑defined):

- Business risk and industry profile  
- Market position, diversification, resilience  
- Management quality and governance  
- Financial policy, liquidity management, refinancing risk  
- Country/sovereign risk, legal/institutional environment

---

## 4. Rating scale, hardstops, and outlook

### 4.1 Rating scale

`SCORE_TO_RATING` defines the mapping from 0–100 scores to the rating scale:

- From `AAA` at the top down to `C`, with cut‑offs such as 95+ = AAA, 90–94 = AA+, …, 0–1 = C.

`score_to_rating(score)` applies this mapping, and `get_rating_band(rating)` returns the [min, max] band for use in outlook logic.

### 4.2 Distress hardstops and notching

Distress hardstops are applied **after** the uncapped rating:

- `DISTRESS_BANDS` specify thresholds and notch downgrades for:
  - `interest_coverage`
  - `dscr`
  - `altman_z` (e.g. <1.8 typical distress zone) [web:21][web:22]
- `compute_distress_notches` aggregates these (capped by `MAX_DISTRESS_NOTCHES`) and returns:
  - `distress_notches` (usually ≤ 0),
  - `hardstop_details` keyed by ratio name.
- `move_notches(grade, notches)` shifts the rating down the scale to get a **post‑distress** `hardstop_rating`.

This mimics agency‑style “hardstop” logic where very weak coverage or Z‑scores limit the rating regardless of otherwise decent metrics. [web:27][web:30]

### 4.3 Sovereign cap and outlook

- Sovereign cap:  
  - `apply_sovereign_cap(issuer_grade, sovereign_grade)` ensures the issuer cannot be rated above the sovereign when `enable_sovereign_cap=True`.  
  - If the cap binds and a `sovereign_outlook` is provided, the issuer outlook is anchored to the sovereign.

- Outlook:  
  - `derive_outlook_band_only(combined_score, rating)`  
    - Compresses the score into the rating band and sets:
      - Upper edge → `Positive`
      - Lower edge → `Negative`
      - Otherwise → `Stable`
  - `derive_outlook_with_distress_trend(base_outlook, distress_notches, fin_t0, fin_t1)`  
    - If hardstops active (distress_notches < 0), adjusts the outlook based on whether distress ratios (coverage, DSCR, Z‑score) are improving or deteriorating between t1 and t0.
    - Improving distress metrics → at most `Stable`, deteriorating → `Negative`.

An additional guard prevents `AAA` with `Positive` outlook: if `final_rating == "AAA"` and `outlook == "Positive"`, it is forced to `Stable`.

---

## 5. Using the model

### 5.1 Minimal example

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
