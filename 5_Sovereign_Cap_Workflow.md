# Sovereign Cap Workflow

This document explains how the model applies a **sovereign cap** (sovereign ceiling) to ensure an issuer's rating does not exceed the rating of its sovereign when the cap is enabled. It also describes how the sovereign‑capped rating interacts with the base rating (before overlays) and the hardstop rating.

The goal is to align the issuer's rating with country‑level risk and to avoid situations where an issuer is rated materially above its sovereign when the cap is active.

---

## 1. Sovereign Layer in the Rating Stack

The rating is built in three main layers:

1. **Base rating (unconstrained)**
   Derived from the combined quantitative and qualitative score using `SCORE_TO_RATING`, before any hardstops or caps.

2. **Distress hardstops (optional)**
   Apply notch‑down adjustments based on:

   * `interest_coverage`
   * `dscr`
   * `altman_z`

3. **Sovereign cap (optional)**
   Ensures the issuer is not rated better than the specified sovereign rating when the cap is enabled.

The **hardstop rating** is the outcome after applying the distress layer to the base rating.
The **capped rating** is the outcome after applying the sovereign cap to the hardstop rating.
The **final rating** currently equals the capped rating.

Overall flow:

> base rating → hardstop rating → sovereign‑capped final rating

When the cap is disabled, the final rating is simply the hardstop rating.

---

## 2. Inputs and Configuration

The sovereign cap logic relies on:

* **`RATING_SCALE`**
  Ordered list of rating symbols from best to worst (for example `["AAA", "AA+", ..., "C"]`).

* **`apply_sovereign_cap(issuer_grade, sovereign_grade)`**
  Helper that enforces the ceiling logic on the ordinal scale.

* **Sovereign context passed into `compute_final_rating`:**

  * `sovereign_rating: Optional[str]`
  * `sovereign_outlook: Optional[str]`
  * `enable_sovereign_cap: bool`

If `enable_sovereign_cap` is `False` or `sovereign_rating` is `None`, the sovereign cap layer is skipped.

---

## 3. Core Sovereign Cap Logic

The core function behaves as a simple ceiling on the rating scale:

```python
def apply_sovereign_cap(
    issuer_grade: str,
    sovereign_grade: Optional[str],
) -> str:
    if sovereign_grade is None:
        return issuer_grade
    if issuer_grade not in RATING_SCALE or sovereign_grade not in RATING_SCALE:
        return issuer_grade
    i = RATING_SCALE.index(issuer_grade)
    s = RATING_SCALE.index(sovereign_grade)
    return RATING_SCALE[max(i, s)]  # worse (higher index) of issuer vs sovereign
```

### Key properties

* If the issuer is better than the sovereign, it is downgraded to the sovereign level.
* If the issuer is equal or worse, the rating is unchanged.
* If the sovereign is missing or either grade is not on `RATING_SCALE`, the function leaves the issuer rating unchanged as a defensive fallback.

---

## 4. Application in `compute_final_rating`

Within `compute_final_rating`, the sovereign cap sits directly after the hardstop rating.

### 4.1 Activation

```python
capped_rating = hardstop_rating
if enable_sovereign_cap and sovereign_rating is not None:
    capped_rating = apply_sovereign_cap(hardstop_rating, sovereign_rating)

final_rating = capped_rating  # no further overlays at present
```

The flag `enable_sovereign_cap` and the presence of `sovereign_rating` together determine whether the cap is applied.

### 4.2 Binding definition

The model tracks whether the cap is actually constraining the issuer:

```python
sovereign_cap_binding = (
    enable_sovereign_cap
    and sovereign_rating is not None
    and final_rating == sovereign_rating
)
```

* `sovereign_cap_binding = True` means the final rating sits at the sovereign level under an active cap.
* `False` means either the cap is off, the sovereign is missing, or the issuer ends up below the sovereign even with the cap active.

A corresponding flag is stored in `flags["sovereign_cap_binding"]` for transparency.

---

## 5. Scenario Overview

### Scenario A – Cap Not Binding (Issuer Below Sovereign)

* `hardstop_rating = BB+`
* `sovereign_rating = BBB-`
* `enable_sovereign_cap = True`

**Result**

* Issuer is already worse than the sovereign.
* `capped_rating = BB+` and `final_rating = BB+`.
* `sovereign_cap_binding = False`.

The sovereign cap has no effect when the issuer is below the sovereign.

---

### Scenario B – Cap Binding (Issuer Above Sovereign)

* `hardstop_rating = BBB`
* `sovereign_rating = BB+`
* `enable_sovereign_cap = True`

**Result**

* Issuer is better than the sovereign on `RATING_SCALE`.
* `capped_rating = BB+` and `final_rating = BB+`.
* `sovereign_cap_binding = True`.

Here the sovereign ceiling actively constrains the issuer's rating.

---

### Scenario C – Cap “Aligned” (Issuer Equals Sovereign)

* `hardstop_rating = BB`
* `sovereign_rating = BB`
* `enable_sovereign_cap = True`

**Result**

* `capped_rating = BB` and `final_rating = BB`.
* `sovereign_cap_binding = True` (the issuer sits at the sovereign level, even though there is no visible notch movement).

---

### Scenario D – Cap Disabled

* `hardstop_rating = BBB`
* `sovereign_rating = BB+`
* `enable_sovereign_cap = False`

**Result**

* Sovereign data may still be stored for context.
* `capped_rating = BBB` and `final_rating = BBB`.
* `sovereign_cap_binding = False` by construction.

This is useful for sensitivity analysis or applications where a sovereign ceiling is not desired.

---

## 6. Interaction with Outlook

When the sovereign cap is binding and a valid `sovereign_outlook` is provided (`"Positive"`, `"Stable"`, or `"Negative"`), the model adjusts the issuer outlook in `compute_final_rating`:

* It first computes a band‑based base outlook from the combined score and base rating.

If the cap is binding and a sovereign outlook is available:

* If `hardstop_rating == capped_rating == sovereign_rating` and the base outlook already matches the sovereign outlook, the model keeps that band‑based outlook.

Otherwise:

* If the base outlook is `"Positive"` but the sovereign outlook is only `"Stable"` or `"Negative"`, the issuer outlook is aligned down to the sovereign view.
* If either the base outlook or the sovereign outlook is `"Negative"`, the final outlook is set to `"Negative"`.

In all other non‑negative combinations, the outlook is set to `"Stable"`, reflecting a deliberately conservative stance that avoids signalling upside momentum when the issuer is constrained by a binding sovereign cap.

If the cap is not binding (or not enabled), the outlook is driven instead by band position and distress trends, as described in the main methodology.

---

## 7. Design Intent

The sovereign cap layer is designed to:

* Enforce country‑risk consistency by preventing issuers from being rated materially above their sovereign when the cap is active.
* Remain transparent, using a simple ordinal comparison on `RATING_SCALE` rather than opaque adjustments.
* Be non‑compensatory: strong issuer metrics cannot overcome a weak sovereign when the cap is enabled.
* Stay configurable via `enable_sovereign_cap`, so users can run the model with or without the ceiling.

Integrate cleanly with:

* The hardstop layer (distress‑driven notches), and
* The outlook logic (sovereign‑anchored outlook when the cap is binding, issuer‑driven otherwise).

Together with the distress overlay and outlook components, the sovereign cap layer helps the model behave like a disciplined internal rating framework that reflects both issuer‑specific risk and broader country‑level constraints.
