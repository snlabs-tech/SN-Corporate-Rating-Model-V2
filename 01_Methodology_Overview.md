# 00_Methodology_Overview
## 1. Scope, Inputs, and Outputs

The rating engine combines quantitative financial ratios, Altman Z‑score, peer benchmarking, and structured qualitative factors into an internal issuer rating and outlook. It is intended for non‑financial corporates with standard financial statements and at least three years of history.

### 1.1 Time Structure and Data Windows

The model uses three consecutive annual (or latest‑twelve‑month) periods:

- t0: most recent financial period (current assessment year).
- t1: previous period.
- t2: two periods ago.

Quantitative inputs are passed via `QuantInputs`:

- `fin_t0`, `fin_t1`, `fin_t2`: dictionaries of pre‑computed ratios keyed by ratio name.
- `components_t0`, `components_t1`, `components_t2`: Altman Z‑score components (working capital, total assets, retained earnings, EBIT, market value of equity, total liabilities, sales).
- `peers_t0`: peer group ratios for the current period for benchmarking.

Qualitative inputs are passed via `QualInputs`:

- `factors_t0`, `factors_t1`: dictionaries of 1–5 scores for each qualitative factor.

Model outputs are collected in `RatingOutputs`, which includes:

- Scores: quantitative, qualitative, combined, peer score, Altman Z at t0, bucket averages.
- Ratings: base rating, post‑distress rating, capped rating, final rating, outlook.
- Overlays: distress notches and details, sovereign rating and outlook, cap binding flag.
- Flags: activation of hardstops and sovereign cap.
- Narrative: a rating explanation string for governance and audit.

Both the distress overlay and the sovereign cap are optional modules, activated via flags in the rating engine. When disabled, the model returns a purely unconstrained, score‑based rating.

---

## 2. Quantitative Framework

### 2.1 Ratio Families

Each financial ratio is assigned to a risk dimension via `RATIO_FAMILY`:

- Leverage: `debt_ebitda`, `net_debt_ebitda`, `debt_equity`, `debt_capital`.
- Leverage (reverse, where higher is better): `ffo_debt`, `fcf_debt`.
- Coverage: `interest_coverage`, `fixed_charge_coverage`, `dscr`.
- Profitability: `ebitda_margin`, `ebit_margin`, `roa`, `roe`.
- Other: `capex_dep`, `current_ratio`, `rollover_coverage`.
- Altman: `altman_z`.

This grouping allows the model to produce both an overall quantitative score and family‑level averages that show which risk dimensions dominate the outcome.

### 2.2 Ratio Grids and Scoring

Each ratio has a monotonic grading grid defined in `RATIO_GRIDS`. Grids are specified as contiguous intervals with an associated score:

- Each entry is of the form `(low, high, score)`.
- Scores lie in {0, 25, 50, 75, 100}.
- Higher economic risk (for example, higher leverage or lower coverage) is systematically mapped to lower scores.

Example: the `debt_ebitda` grid is:

- < 2.0: score 100.
- 2.0–3.0: score 75.
- 3.0–4.0: score 50.
- 4.0–6.0: score 25.
- ≥ 6.0: score 0.

The helper function `score_ratio(name, value)`:

- Looks up the appropriate grid for the ratio.
- Returns the score for the interval containing the observed value.
- Returns `None` if no grid exists or the value is missing/NaN (these ratios are ignored).

### 2.3 Altman Z‑Score

If `altman_z` is not present in `fin_t0`, the engine computes it from components using the classic formulation:

Z = 1.2A + 1.4B + 3.3C + 0.6D + 1.0E

where:

- A = working capital / total assets
- B = retained earnings / total assets
- C = EBIT / total assets
- D = market value of equity / total liabilities
- E = sales / total assets

The computed Z‑score is:

- Stored back in `fin_t0["altman_z"]`.
- Scored via the `altman_z` grid as part of the quantitative block.
- Reused in the distress overlay (Section 5).

### 2.4 Peer Positioning

The model incorporates an explicit peer benchmarking component for t0 via `compute_peer_score`:

- For each ratio with both issuer and peer values, the issuer’s value is compared to the peer average.
- A ratio is classified as “underperforming” if the issuer’s value is more than 10% worse than the peer average (taking the ratio direction as defined).
- The share of underperforming ratios (under_share) is mapped to a 0–100 peer score:

  - under_share ≤ 10% → peer score 100
  - 10% < under_share ≤ 30% → 75
  - 30% < under_share ≤ 60% → 50
  - 60% < under_share ≤ 80% → 25
  - under_share > 80% → 0

When available, the peer score is treated as one additional quantitative metric (bucketed under “other”) and enters the aggregate quantitative score.

### 2.5 Aggregation of Quantitative Score

In `compute_quantitative`:

1. The model copies `fin_t0` to avoid mutating upstream data and ensures `altman_z` is present.
2. For each recognized ratio:
   - It computes a grid‑based score.
   - It records that score in the appropriate ratio family bucket.
3. It computes the peer score, if possible, and appends it to the quantitative scores.
4. The **quantitative score** is the simple arithmetic average of all available numeric scores. If no scores are available, it defaults to 0.0.
5. For diagnostics, the model computes `bucket_avgs` as the average score per ratio family.

The function returns:

- `quantitative_score`
- `peer_score`
- `bucket_avgs`
- `altman_z` at t0
- `n_quant_items` (number of quantitative items that actually entered the average)

---

## 3. Qualitative Framework

### 3.1 Qualitative Factors

Qualitative inputs capture dimensions that are not fully reflected in static financial ratios, for example:

- Industry risk
- Market position and competitive strength
- Revenue diversification and stability
- Business model resilience
- Management quality and governance
- Financial policy and risk appetite
- Sovereign and legal environment
- Liquidity profile and refinancing risk

The engine itself is agnostic to the specific factor list. Any key in `factors_t0` with a 1–5 value is processed.

### 3.2 Qualitative Scoring

`compute_qualitative` maps each numeric input to a 0–100 score using `QUAL_SCORE_SCALE`:

- 5 → 100
- 4 → 75
- 3 → 50
- 2 → 25
- 1 → 0

Unknown or out‑of‑range values are logged and skipped. The **qualitative score** is the arithmetic average of all valid factor scores at t0. The function also returns `n_qual_items` (number of factors that entered the average).

---

## 4. Combining Quantitative and Qualitative Scores

### 4.1 Weighting Scheme

The combined score is a weighted average of quantitative and qualitative blocks:

- If `RATING_WEIGHTS["quantitative"]` and `RATING_WEIGHTS["qualitative"]` are both set, those fixed weights are used directly.
- Otherwise, weights are derived endogenously from the number of usable items:
  - w_q = n_quant / (n_quant + n_qual)
  - w_l = n_qual / (n_quant + n_qual)
- If there are no usable quantitative or qualitative items (n_quant + n_qual = 0), the function returns (0.0, 0.0) and the combined score is effectively non‑informative.

The combined score is:

combined_score = w_q × quantitative_score + w_l × qualitative_score

### 4.2 Score‑to‑Rating Mapping

The combined score is mapped to an internal AAA–C scale via the `SCORE_TO_RATING` ladder, with thresholds in 5‑point increments across the 0–100 range. For example:

- ≥ 95 → AAA
- ≥ 90 → AA+
- …
- ≥ 5 → CCC−
- ≥ 2 → CC
- ≥ 0 → C

`safe_score_to_rating` returns the first rating whose cutoff is satisfied. If the score does not match any cutoff (which should not occur under normal configuration), it logs an error and returns “N/R”.

This value is the **base rating**, which reflects the unconstrained model outcome before any overlays.

---

## 5. Distress Overlay (Hardstops)

### 5.1 Optional Activation

The distress overlay is optional and controlled by the `enable_hardstops` flag in `compute_final_rating`:

- If `enable_hardstops` is `False`, the model sets `distress_notches = 0`, `hardstop_rating = base_rating`, and `hardstop_triggered = False`.
- If `enable_hardstops` is `True`, the model applies the distress logic described below.

### 5.2 Distress Indicators and Thresholds

When enabled, the distress overlay introduces mandatory downgrades (“hardstops”) when key downside risk indicators are weak. The indicators are:

- Interest coverage (`interest_coverage`)
- Debt service coverage ratio (`dscr`)
- Altman Z‑score (`altman_z`)

For each indicator, `DISTRESS_BANDS` defines descending thresholds and associated negative notches. For example:

- Interest coverage:
  - < 0.5 → −4 notches
  - < 0.8 → −3
  - < 1.0 → −2
- DSCR:
  - < 0.8 → −3
  - < 0.9 → −2
  - < 1.0 → −1
- Altman Z:
  - < 1.2 → −4
  - < 1.5 → −3
  - < 1.81 → −2

The model stops at the first threshold breached for each ratio and records the associated notches and the observed value in `hardstop_details`. Missing ratios do not contribute.

### 5.3 Aggregation, Floor, and Hardstop Rating

`compute_distress_notches` sums the notches across indicators to obtain `total_notches` and applies a floor:

- `MAX_DISTRESS_NOTCHES = -4` limits the cumulative downgrade to four notches, regardless of how many indicators are weak.

The **hardstop rating** is then:

- hardstop_rating = move_notches(base_rating, distress_notches)

Negative values of `distress_notches` indicate downgrades relative to the base rating. A Boolean `hardstop_triggered` flags whether any downgrade was applied.

---

## 6. Sovereign Cap Overlay

### 6.1 Optional Activation

The sovereign cap overlay is also optional and controlled by the `enable_sovereign_cap` flag:

- If `enable_sovereign_cap` is `False` or `sovereign_rating` is `None`, no cap is applied and `capped_rating = hardstop_rating`.
- If `enable_sovereign_cap` is `True` and a valid `sovereign_rating` is supplied, the cap logic is applied.

### 6.2 Cap Logic and Binding

The cap operates on the common `RATING_SCALE` list (AAA down to C). `apply_sovereign_cap`:

- Finds the indices of the issuer’s hardstop rating and the sovereign rating on the scale.
- Returns the rating with the worse index (weaker credit quality).

The resulting rating is the **capped rating**. The flag `sovereign_cap_binding` is `True` if:

- The cap is enabled,
- A sovereign rating is provided, and
- The final rating equals the sovereign rating (i.e., the cap is actually constraining the issuer).

Currently, the **final rating** is set equal to the capped rating; there are no additional overlays beyond distress and the sovereign cap.

---

## 7. Outlook Determination

### 7.1 Band‑Based Base Outlook

The model first derives a base outlook from the combined score’s position within the score band of the base rating:

- Each rating grade has an associated numeric band [band_min, band_max] implied by `SCORE_TO_RATING`.
- The combined score is floored to an integer and compared with that band:
  - If equal to band_max → base outlook “Positive”
  - If equal to band_min → base outlook “Negative”
  - Otherwise → base outlook “Stable”

### 7.2 Sovereign‑Linked Outlook (Cap Binding Case)

If the sovereign cap is binding and `sovereign_outlook` is one of “Positive”, “Stable”, or “Negative”:

- If `hardstop_rating`, `capped_rating`, and `sovereign_rating` are all the same and the base outlook already matches the sovereign outlook, the model keeps the band‑based base outlook.
- Otherwise:
  - If the base outlook is “Positive” but the sovereign outlook is only “Stable” or “Negative”, the outlook is aligned down to the sovereign view.
  - If either the base outlook or the sovereign outlook is “Negative”, the final outlook is set to “Negative”.
  - In all other non‑negative combinations, the outlook is set to “Stable”, reflecting a deliberately conservative stance that avoids signalling upside momentum when the issuer is constrained by a binding sovereign cap.

This prevents an issuer capped at the sovereign level from having a meaningfully more optimistic outlook than the sovereign.

### 7.3 Distress‑Trend Adjustment (Non‑binding Case)

If the sovereign cap is not binding (either the cap is disabled or not constraining):

- The model may adjust the outlook based on the trend in distress ratios between t1 and t0, but only if `distress_notches < 0` (i.e., hardstops actually bit).
- Ratios assessed: `interest_coverage`, `dscr`, `altman_z`.
- For each ratio with both t0 and t1 values:
  - If t0 > t1, the ratio is classified as “improving”.
  - If t0 < t1, it is classified as “deteriorating”.

The rule is:

- If at least one ratio is improving and none are deteriorating → outlook “Stable”.
- If at least one ratio is deteriorating and none are improving → outlook “Negative”.
- Otherwise → keep the base outlook.


Finally, the model enforces a guard: no issuer rated AAA can carry a “Positive” outlook. If such a combination arises, the outlook is reset to “Stable”.

---

## 8. Outputs, Flags, and Narrative

### 8.1 Core Outputs

`compute_final_rating` returns a `RatingOutputs` object containing:

- Issuer identification:
  - `issuer_name`
- Scores:
  - `quantitative_score`
  - `qualitative_score`
  - `combined_score`
  - `peer_score`
  - `bucket_avgs`
  - `altman_z_t0`
- Ratings:
  - `base_rating`
  - `hardstop_rating`
  - `capped_rating`
  - `final_rating`
- Distress overlay:
  - `distress_notches`
  - `hardstop_triggered`
  - `hardstop_details`
- Sovereign overlay:
  - `sovereign_rating`
  - `sovereign_outlook`
  - `sovereign_cap_binding`
- Outlook:
  - `outlook`
- Flags:
  - `flags["enable_hardstops"]`
  - `flags["enable_sovereign_cap"]`
  - `flags["hardstop_triggered"]`
  - `flags["sovereign_cap_binding"]`
- Narrative:
  - `rating_explanation`

### 8.2 Rating Explanation

The `rating_explanation` field provides a human‑readable summary:

- It states the combined score and resulting base rating.
- It describes whether distress hardstops were active, whether they triggered, and how many notches of downgrade were applied.
- It explains if a sovereign cap was active, whether it was binding, and how it affected the rating.
- It concludes with the final rating and outlook.

This narrative is intended to be stored with each rating run so users can quickly understand how the model arrived at the result.
