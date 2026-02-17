# Sovereign Cap Workflow

This document explains how the model applies a **sovereign cap** (sovereign ceiling) to ensure an issuer’s rating does not exceed the rating of its sovereign. It also describes how the sovereign‑capped rating interacts with the uncapped rating and the hardstop rating.

The goal is to align the issuer’s rating with country‑level risk, preventing situations where an issuer is rated materially above its sovereign when the cap is enabled.

---

## 1. Sovereign Layer in the Rating Stack

The rating is built in three main layers:

- **Uncapped rating**  
  Derived from the combined quantitative and qualitative score using `SCORE_TO_RATING`.

- **Distress hardstops**  
  Apply notch‑down adjustments based on:
  - `interest_coverage`  
  - `dscr`  
  - `altman_z`  

- **Sovereign cap (this document, optional)**  
  Ensures the issuer is not rated above the sovereign.

The **hardstop rating** is the outcome after applying the distress layer to the uncapped rating.  
The **sovereign‑capped rating** is the outcome after applying the sovereign cap to the hardstop rating.

Overall flow:

> Uncapped rating → Hardstop rating → Sovereign‑capped final rating

When the cap is disabled, the final rating is simply the hardstop rating.

---

## 2. Inputs and Configuration

The sovereign cap logic relies on:

- `RATING_SCALE`  
  Ordered list of rating symbols from best to worst (e.g. `["AAA", "AA+", ..., "C"]`).

- `apply_sovereign_cap(issuer_grade, sovereign_grade)`  
  Helper that enforces the ceiling logic.

- Sovereign context passed into `compute_final_rating`:
  - `sovereign_rating: Optional[str]`  
  - `sovereign_outlook: Optional[str]`
  - `enable_sovereign_cap: bool`

If `enable_sovereign_cap` is `False`, the sovereign cap layer is skipped entirely.

---

## 3. Core Sovereign Cap Logic

The core function behaves as a simple ceiling on the ordinal rating scale:

```python
def apply_sovereign_cap(issuer_grade: str, sovereign_grade: Optional[str]) -> str:
    # If no sovereign is provided, do nothing
    if sovereign_grade is None:
        return issuer_grade

    # If either grade is not in the rating scale, fail safe and return issuer unchanged
    if issuer_grade not in RATING_SCALE or sovereign_grade not in RATING_SCALE:
        return issuer_grade

    issuer_idx = RATING_SCALE.index(issuer_grade)
    sov_idx = RATING_SCALE.index(sovereign_grade)

    # Ratings are ordered best (index 0) to worst (last index)
    # The worse (higher index) of the two becomes the final rating
    capped_idx = max(issuer_idx, sov_idx)
    return RATING_SCALE[capped_idx]
