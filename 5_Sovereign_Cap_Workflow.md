# Sovereign Cap Workflow

This document explains how the model applies a **sovereign cap**
(sovereign ceiling) to ensure an issuer's rating does not exceed the
rating of its sovereign. It also describes how the sovereign-capped
rating interacts with the uncapped rating and the hardstop rating.

The goal is to align the issuer's rating with country-level risk,
preventing situations where an issuer is rated materially above its
sovereign when the cap is enabled.

------------------------------------------------------------------------

## 1. Sovereign Layer in the Rating Stack

The rating is built in three main layers:

-   **Uncapped rating**\
    Derived from the combined quantitative and qualitative score using
    `SCORE_TO_RATING`.

-   **Distress hardstops**\
    Apply notch-down adjustments based on:

    -   `interest_coverage`
    -   `dscr`
    -   `altman_z`

-   **Sovereign cap** (this document, optional)\
    Ensures the issuer is not rated above the sovereign.

The **hardstop rating** is the outcome after applying the distress layer
to the uncapped rating.\
The **sovereign-capped rating** is the outcome after applying the
sovereign cap to the hardstop rating.

Overall flow:

> Uncapped rating → Hardstop rating → Sovereign-capped final rating

When the cap is disabled, the final rating is simply the hardstop
rating.

------------------------------------------------------------------------

## 2. Inputs and Configuration

The sovereign cap logic relies on:

-   `RATING_SCALE`\
    Ordered list of rating symbols from best to worst (for example
    `["AAA", "AA+", ..., "C"]`).

-   `apply_sovereign_cap(issuer_grade, sovereign_grade)`\
    Helper that enforces the ceiling logic.

-   Sovereign context passed into `compute_final_rating`:

    -   `sovereign_rating: Optional[str]`
    -   `sovereign_outlook: Optional[str]`
    -   `enable_sovereign_cap: bool`

If `enable_sovereign_cap` is `False`, the sovereign cap layer is skipped
entirely.

------------------------------------------------------------------------

## 3. Core Sovereign Cap Logic

The core function behaves as a simple ceiling on the ordinal rating
scale:

``` python
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
```

### Key properties:

-   If the issuer is better than the sovereign, it is downgraded to the
    sovereign level.
-   If the issuer is equal or worse, the rating is unchanged.
-   If the sovereign is missing or an invalid grade is supplied, the
    function leaves the issuer rating unchanged as a defensive fallback.

------------------------------------------------------------------------

## 4. Application in `compute_final_rating`

Inside `compute_final_rating`, the sovereign cap sits after the hardstop
rating:

1.  Compute the uncapped rating from the combined score.
2.  Apply distress hardstops (if enabled) to derive:
    -   `hardstop_rating`
3.  Apply sovereign cap (if enabled) to derive:
    -   `final_rating`

### Pseudocode:

``` python
# After computing uncapped_rating and hardstop_rating

if enable_sovereign_cap:
    final_rating = apply_sovereign_cap(hardstop_rating, sovereign_rating)
else:
    final_rating = hardstop_rating

sovereign_cap_binding = (
    enable_sovereign_cap
    and sovereign_rating is not None
    and final_rating != hardstop_rating
)
```

`sovereign_cap_binding` can be stored in flags or used in explanations
to indicate that the sovereign ceiling was active and actually
constrained the issuer's rating.

------------------------------------------------------------------------

## 5. Scenario Overview

### Scenario A -- Cap Not Binding (Sovereign Above Issuer)

-   `hardstop_rating = BB+`
-   `sovereign_rating = BBB-`
-   Cap enabled

**Result:**

-   Issuer is already worse than the sovereign.
-   `final_rating = BB+` (no change).
-   `sovereign_cap_binding = False`.

The sovereign cap has no effect when the issuer is already below the
sovereign.

------------------------------------------------------------------------

### Scenario B -- Cap Binding (Issuer Above Sovereign)

-   `hardstop_rating = BBB`
-   `sovereign_rating = BB+`
-   Cap enabled

**Result:**

-   Issuer is better than the sovereign on `RATING_SCALE`.
-   `final_rating = BB+` (cut down to sovereign level).
-   `sovereign_cap_binding = True`.

Here the sovereign ceiling actively constrains the issuer's rating.

------------------------------------------------------------------------

### Scenario C -- Cap Trivially Binding (Issuer Equals Sovereign)

-   `hardstop_rating = BB`
-   `sovereign_rating = BB`
-   Cap enabled

**Result:**

-   `final_rating = BB` (no visible change).

Logically, the cap confirms equality but there is no notch movement.

------------------------------------------------------------------------

### Scenario D -- Cap Disabled

-   `hardstop_rating = BBB`
-   `sovereign_rating = BB+`
-   `enable_sovereign_cap = False`

**Result:**

-   Sovereign information may still be stored for context.
-   `final_rating = BBB` (unconstrained by sovereign).
-   `sovereign_cap_binding = False` by construction.

This scenario is useful for sensitivity analysis or portfolios where a
sovereign cap is not desired.

------------------------------------------------------------------------

## 6. Interaction with Outlook

When the sovereign cap binds, the model needs a rule for the issuer's
outlook:

-   If the cap binds and a valid `sovereign_outlook` is provided:
    -   The issuer's outlook is set equal to `sovereign_outlook`,
        reflecting that the sovereign ceiling is the binding constraint.
-   If the cap binds but no sovereign outlook is provided:
    -   The model can default to `"Stable"` for the issuer, or fall back
        to the internal band-based or distress-trend logic within the
        capped rating band (depending on implementation choice).
-   If the cap does not bind:
    -   Outlook is driven by:
        -   Position of the combined score within the rating band (for
            example top, middle, bottom), and
        -   Trend in distress metrics (for example via
            `derive_outlook_with_distress_trend`).

This ensures that when country risk is the binding constraint, the
issuer's outlook is anchored to the sovereign's direction; otherwise, it
reflects the issuer's own fundamentals and distress trends.

------------------------------------------------------------------------

## 7. Design Intent

The sovereign cap layer is designed to:

-   Enforce country-risk consistency by preventing issuers from being
    rated materially above their sovereign when the cap is active.
-   Remain transparent, using a simple ordinal comparison on
    `RATING_SCALE` rather than opaque adjustments.
-   Be non-compensatory: strong issuer metrics cannot overcome a weak
    sovereign when the cap is enabled.
-   Remain configurable, via `enable_sovereign_cap`, so that users can
    run analyses with or without the ceiling.
-   Integrate cleanly with:
    -   The hardstop layer (distress-driven notches), and
    -   The outlook logic (inherit sovereign outlook when the cap is
        binding).

Together with the hardstop and outlook components, the sovereign cap
layer helps the model behave like a disciplined internal rating
framework that reflects both issuer-specific risk and broader
country-level constraints.
