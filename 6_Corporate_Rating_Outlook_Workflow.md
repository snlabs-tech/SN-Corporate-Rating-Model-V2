# Rating–Outlook Workflow

This document explains how the model determines the **rating outlook** (Positive / Stable / Negative), given the different layers of logic: the score band, the optional distress hardstops, and the optional sovereign cap.

The key idea is: *the outlook is driven by the same mechanism that effectively constrains the rating* (pure score, distress, or sovereign).

---

## 1. Building Blocks

### 1.1 Combined Score and Base Rating Band

From the quantitative and qualitative blocks, the model computes:

* `combined_score` (0–100)
* `base_rating` via `SCORE_TO_RATING` (e.g. 55.5 → BBB)

Each rating grade has a numeric **band** `[band_min, band_max]` in score space (e.g. BBB = 55–59).

`derive_outlook_band_only(combined_score, rating)`:

1. Looks up the band for `rating`.
2. Floors the combined score: `cs = floor(combined_score)`.
3. Maps position to outlook:

   * `cs == band_max` → **Positive**
   * `cs == band_min` → **Negative**
   * Otherwise → **Stable**

So within a given rating grade, the bottom of the band is Negative, the top is Positive, and the middle is Stable.

> In the current implementation the base outlook is always derived from the **base_rating** and `combined_score` (before hardstops and cap).

---

### 1.2 Distress Hardstops and Trends

Distress hardstops use three quantitative indicators:

* `interest_coverage`
* `dscr`
* `altman_z`

`compute_distress_notches(fin_t0, altman_z)`:

* For each distress metric, checks if it falls below its threshold bands in `DISTRESS_BANDS`.
* Sums the associated negative notches (floored at `MAX_DISTRESS_NOTCHES`).
* Returns `(distress_notches, hardstop_details)`.

`derive_outlook_with_distress_trend(base_outlook, distress_notches, fin_t0, fin_t1)`:

* If `distress_notches >= 0`:

  * Returns `base_outlook` unchanged.
* If `distress_notches < 0` (distress active):

  * Compares t1 → t0 for `interest_coverage`, `dscr`, `altman_z`:

    * For each metric with values in both periods:

      * If `t0 > t1` → flag as **improving**
      * If `t0 < t1` → flag as **deteriorating**
  * Rules:

    * Improving and not deteriorating → **Stable**
    * Deteriorating and not improving → **Negative**
    * Mixed / flat → **Stable**

Important: the trend overlay only runs when **hardstops have actually bitten** (`distress_notches < 0`) and the sovereign cap is not binding. It cannot create a Positive outlook; it only moves between Stable and Negative.

---

### 1.3 Sovereign Cap and Binding Definition

If enabled, the sovereign cap ensures the issuer is not rated above the sovereign on the internal scale:

* `apply_sovereign_cap(hardstop_rating, sovereign_rating)` returns the worse of the two ratings according to `RATING_SCALE`.

After applying hardstops (if any), the model computes:

```python
capped_rating = hardstop_rating
if enable_sovereign_cap and sovereign_rating is not None:
    capped_rating = apply_sovereign_cap(hardstop_rating, sovereign_rating)

final_rating = capped_rating
```

The cap is considered binding if:

```python
sovereign_cap_binding = (
    enable_sovereign_cap
    and sovereign_rating is not None
    and final_rating == sovereign_rating
)
```

Binding means the final rating sits at the sovereign level under an active cap (either because the issuer was above and got cut down, or because it is exactly at the sovereign ceiling).

---

## 2. Outlook Decision Ladder

The model uses the following ladder to determine the final outlook.

### 2.1 Base Outlook from the Base Rating Band

First, the model derives a band-based base outlook:

```python
base_outlook = derive_outlook_band_only(combined_score, base_rating)
```

This uses the base (unconstrained) rating and places the combined score within that band to get Positive / Stable / Negative.

---

### 2.2 Sovereign-Binding Branch

If the sovereign cap is binding and a valid `sovereign_outlook` is provided:

```python
if (
    sovereign_cap_binding
    and sovereign_outlook in {"Positive", "Stable", "Negative"}
):
    if (
        hardstop_rating == capped_rating == sovereign_rating
        and base_outlook == sovereign_outlook
    ):
        outlook = base_outlook
    else:
        if base_outlook == "Positive" and sovereign_outlook in {"Stable", "Negative"}:
            outlook = sovereign_outlook
        elif base_outlook == "Negative" or sovereign_outlook == "Negative":
            outlook = "Negative"
        else:
            outlook = "Stable"
```

**Interpretation**

**Exact alignment case:**
If the post-distress rating, capped rating, and sovereign rating are all the same and the base outlook already matches the sovereign outlook, the model keeps the band-based base outlook.

**Otherwise:**

* If the model is more optimistic than the sovereign (`base_outlook = Positive`, sovereign_outlook = Stable or Negative), the sovereign view dominates and the issuer outlook is aligned down to the sovereign’s stance.
* If either side is Negative (base or sovereign), the final outlook is set to Negative.
* In all other non-negative combinations, the outlook is set to Stable, reflecting a deliberately conservative stance that avoids signalling upside momentum when the issuer is constrained by a binding sovereign cap.

In this branch, the sovereign becomes the anchor for the outlook whenever it is actually constraining the rating.

---

### 2.3 Non-Binding / No-Cap Branch (Distress Trend Overlay)

If the cap is not binding (or not enabled), the model falls back to distress-trend logic:

```python
else:
    outlook = derive_outlook_with_distress_trend(
        base_outlook,
        distress_notches,
        quant_inputs.fin_t0,
        quant_inputs.fin_t1,
    )
```

* If `distress_notches >= 0` (no distress downgrade), `derive_outlook_with_distress_trend` simply returns `base_outlook`.
* If `distress_notches < 0`, it may push the outlook to Negative (clearly deteriorating distress) or to Stable (improving / mixed), but never to Positive.

In other words, when the sovereign is not constraining the rating, distress dynamics are allowed to modify the band-based outlook.

---

### 2.4 AAA Guardrail

Finally, the model applies a simple guard on the maximum rating:

```python
if final_rating == "AAA" and outlook == "Positive":
    outlook = "Stable"
```

As a policy choice, the model does not use a Positive outlook at AAA, because the rating is already at the top of the scale and cannot be upgraded. Any intermediate AAA/Positive combination is reset to AAA/Stable.

---

## 3. Scenario Summary

### Scenario A – Hardstops OFF, Sovereign Cap OFF

* `enable_hardstops = False`
* `enable_sovereign_cap = False`

**Effects:**

* `distress_notches = 0`, `hardstop_rating = base_rating`.
* `sovereign_cap_binding = False`.
* Outlook = band-based only via `derive_outlook_band_only`.

Use this when you want a pure score-driven rating and outlook.

---

### Scenario B – Hardstops ON, No Distress, Cap OFF / Non-Binding

* `enable_hardstops = True`
* `distress_notches >= 0`
* Either `enable_sovereign_cap = False` or cap not binding

**Effects:**

* Hardstop layer does not change the rating.
* Distress trend overlay returns `base_outlook` unchanged.
* Outlook = band-based (same as Scenario A).

Use this when distress metrics are comfortably above thresholds.

---

### Scenario C – Hardstops ON, Distress Deteriorating, Cap Non-Binding

* `enable_hardstops = True`
* `distress_notches < 0`
* Distress ratios between t1 and t0 deteriorate (and do not improve)
* Sovereign cap not binding

**Effects:**

* `derive_outlook_with_distress_trend` sets outlook to Negative, even if the band alone would have suggested Stable or Positive.

**Interpretation:** the issuer is in a distressed zone and getting worse; outlook must be Negative.

---

### Scenario D – Hardstops ON, Distress Improving or Mixed, Cap Non-Binding

* `enable_hardstops = True`
* `distress_notches < 0`
* Distress ratios under their thresholds but either:

  * Clearly improving and not deteriorating, or
  * Mixed/flat

**Effects:**

* Distress trend overlay forces Stable (you remain notched down, but the trend is not clearly worsening).

**Interpretation:** the entity is still under distress constraints, but the trend does not justify a Negative outlook.

---

### Scenario E – Sovereign Cap ON and Binding

* `enable_sovereign_cap = True`, `sovereign_rating` provided
* `final_rating` equals `sovereign_rating` under the cap
* `sovereign_cap_binding = True`

**Effects:**

* If ratings and outlook are already aligned (special case), base outlook can be kept.
* Otherwise:

  * More optimistic than sovereign (e.g. Positive vs Stable/Negative) → aligned down to sovereign stance or Stable.
  * Any Negative from either side → outlook set to Negative.
  * All other non-negative combinations → outlook set to Stable.

**Interpretation:** once the sovereign ceiling binds, the sovereign’s stance effectively dominates the issuer outlook.

---

### Scenario F – Sovereign Cap ON but Not Binding

* `enable_sovereign_cap = True`, but issuer is not constrained (issuer ≤ sovereign)
* `sovereign_cap_binding = False`

**Effects:**

* Final rating = hardstop rating.
* Outlook = result of band + distress logic (Scenarios A–D).

**Interpretation:** sovereign information is available but not constraining; the issuer’s own fundamentals and distress trends drive the outlook.

---

## 4. Design Intent (Intuitive Summary)

### Pure Score Environment (No Distress, No Binding Cap)

Outlook is a function of where the combined score sits within the base rating band.

### Distress Environment (Hardstops Active, Cap Non-Binding)

Outlook cannot be more optimistic than the distress state: it is either Stable (improving or mixed distress trend) or Negative (clearly deteriorating), but never Positive while distress notches are in force.

### Sovereign-Constrained Environment (Cap Binding)

The sovereign’s rating and outlook become the effective ceiling, and the issuer’s outlook is anchored to that stance, with conservative rules to avoid Positive signals under a binding cap.

This structure keeps the outlook consistent with the main driver of the rating in each case: pure score, dis
