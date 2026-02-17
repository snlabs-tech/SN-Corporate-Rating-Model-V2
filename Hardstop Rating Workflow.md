[hardstop_rating_workflow.md](https://github.com/user-attachments/files/25363259/hardstop_rating_workflow.md)
# Hardstop Rating Workflow

This document explains how the model applies **distress hardstops** to
notch the rating down when key risk indicators signal elevated distress.
It also describes how the resulting **hardstop rating** interacts with
the uncapped rating and the sovereign cap.

The goal is to prevent a situation where strong averages or good
profitability fully offset near-default coverage or Altman Z metrics.

------------------------------------------------------------------------

## 1. Distress Layer in the Rating Stack

The rating is built in three main layers:

1.  **Uncapped rating**\
    Derived from the combined quantitative and qualitative score using
    `SCORE_TO_RATING`.

2.  **Distress hardstops (this document)**\
    Apply notch-down adjustments based on:

    -   Interest coverage\
    -   DSCR\
    -   Altman Z-score

3.  **Sovereign cap (optional)**\
    Ensures the issuer is not rated above the sovereign.

The **hardstop rating** is the outcome after applying the distress layer
to the uncapped rating.

------------------------------------------------------------------------

## 2. Distress Metrics and Bands

Three metrics are used for hardstops:

-   `interest_coverage` --- Interest coverage ratio\
-   `dscr` --- Debt service coverage ratio\
-   `altman_z` --- Altman Z-score

Each metric has a set of **bands** with associated **negative notches**
(values are illustrative):

``` python
DISTRESS_BANDS = {
    "interest_coverage": [
        (0.5, -4),
        (0.8, -3),
        (1.0, -2),
    ],
    "dscr": [
        (0.8, -3),
        (0.9, -2),
        (1.0, -1),
    ],
    "altman_z": [
        (1.2, -4),
        (1.5, -3),
        (1.81, -2),
    ],
}

MAX_DISTRESS_NOTCHES = -4
```

### Interpretation (example for interest coverage)

-   Interest coverage \< 0.5 → −4 notches\
-   0.5 ≤ coverage \< 0.8 → −3 notches\
-   0.8 ≤ coverage \< 1.0 → −2 notches\
-   Coverage ≥ 1.0 → No hardstop from this metric

The same logic applies to `dscr` and `altman_z`.

------------------------------------------------------------------------

## 3. How Distress Notches Are Calculated

The core function:

``` python
def compute_distress_notches(fin: Dict[str, float], altman_z: float) -> Tuple[int, Dict[str, float]]:
    total_notches = 0
    details: Dict[str, float] = {}

    # interest_coverage
    ...

    # dscr
    ...

    # altman_z
    ...

    if total_notches < MAX_DISTRESS_NOTCHES:
        total_notches = MAX_DISTRESS_NOTCHES

    return total_notches, details
```

### Step-by-Step Logic

**Interest coverage** - Retrieve `fin.get("interest_coverage")` - Find
the first `(threshold, notches)` where the value is below the
threshold - Add negative notches to `total_notches` - Store value in
`details["interest_coverage"]`

**DSCR** - Same pattern using `DISTRESS_BANDS["dscr"]` - Add additional
negative notches if DSCR is low - Store value in `details["dscr"]`

**Altman Z** - Compare `altman_z` to its bands - Add negative notches
and record in `details["altman_z"]`

**Cap the total** If total notches \< `MAX_DISTRESS_NOTCHES`, clamp to
`MAX_DISTRESS_NOTCHES`.

------------------------------------------------------------------------

### Output

-   `distress_notches`
    -   `0` → No hardstop\
    -   Negative (e.g. −2, −3) → Downgrade notches
-   `details`
    -   Dictionary indicating which metrics triggered the hardstop

------------------------------------------------------------------------

## 4. How the Hardstop Rating Is Applied

Inside `compute_final_rating`:

If hardstops are enabled:

``` python
distress_notches, hardstop_details = self.compute_distress_notches(fin_t0, altman_z)
```

If disabled:

``` python
distress_notches = 0
hardstop_details = {}
```

Apply notches:

``` python
hardstop_rating = move_notches(uncapped_rating, distress_notches)
hardstop_triggered = distress_notches < 0
```

The hardstop rating is then passed to the sovereign cap logic.

------------------------------------------------------------------------

## 5. Scenario Overview

### Scenario A -- No Distress

-   `distress_notches = 0`
-   `hardstop_rating = uncapped_rating`
-   `hardstop_triggered = False`

Distress layer inactive.

------------------------------------------------------------------------

### Scenario B -- Mild Distress

Example: - Interest coverage slightly below 1.0 - DSCR slightly below
1.0 - Altman Z above threshold

Illustrative result: - −2 notches (coverage) - −1 notch (DSCR) - 0
(Altman)

Uncapped = BBB\
Hardstop = BB

Distress forces downgrade.

------------------------------------------------------------------------

### Scenario C -- Severe Distress

Example: - Interest coverage \< 0.5 - Altman Z \< 1.2 - DSCR \< 0.8

Raw total could be −11\
Capped at −4

Uncapped = BBB\
Hardstop = B

Downgrade limited by cap.

------------------------------------------------------------------------

### Scenario D -- Improving Trend

Absolute levels still determine rating level.

Improving metrics may affect outlook but not remove hardstop until
thresholds are crossed.

------------------------------------------------------------------------

### Scenario E -- Hardstops Disabled

-   `distress_notches = 0`
-   `hardstop_rating = uncapped_rating`
-   Distress layer fully inactive.

------------------------------------------------------------------------

## 6. Interaction with Sovereign Cap

Final flow:

Uncapped rating → Hardstop rating → Sovereign-capped final rating

If sovereign rating is lower, it overrides the hardstop rating.

------------------------------------------------------------------------

## 7. Design Intent

The hardstop layer:

-   Is non-compensatory\
-   Prevents strong averages from masking distress\
-   Uses transparent notching\
-   Is bounded by `MAX_DISTRESS_NOTCHES`\
-   Can be toggled with `enable_hardstops`

Together with outlook logic, this behaves like a disciplined internal
rating framework rather than a purely mechanical score.
