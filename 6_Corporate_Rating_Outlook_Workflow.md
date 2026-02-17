# Rating–Outlook Workflow

This document explains how the model determines the **rating outlook** (Positive / Stable / Negative), given the different layers of logic: the score band, distress hardstops, and the sovereign cap.

The key idea is: *the outlook is driven by the same mechanism that effectively constrains the rating* (pure score, distress, or sovereign).

---

## 1. Building blocks

### 1.1 Uncapped rating and score band

From the quantitative and qualitative blocks, the model computes:

- `combined_score` (0–100).
- `uncapped_rating` via `SCORE_TO_RATING` (e.g. 55.5 → BBB).

Each rating grade has a numeric **band** \([band_min, band_max]\) in score space (e.g. BBB = 55–59).

`derive_outlook_band_only(combined_score, uncapped_rating)`:

1. Looks up the band for `uncapped_rating`.
2. Floors the score and clips it to the band:  
   - `cs = floor(combined_score)`  
   - `cs = max(band_min, min(cs, band_max))`
3. Maps position to outlook:  
   - `cs == band_max` → **Positive**.  
   - `cs == band_min` → **Negative**.  
   - Otherwise → **Stable**.

So within a given rating grade, the bottom of the band is Negative, the top is Positive, and the middle is Stable.

---

### 1.2 Distress hardstops and trends

Distress hardstops use:

- Interest coverage.
- DSCR.
- Altman Z‑score.

`compute_distress_notches`:

- For each distress metric, checks if it falls below its threshold bands (`DISTRESS_BANDS`).
- Sums the associated negative notches (capped at `MAX_DISTRESS_NOTCHES`).
- Returns `(distress_notches, hardstop_details)`.

`derive_outlook_with_distress_trend(base_outlook, distress_notches, fin_t0, fin_t1)`:

- If `distress_notches >= 0`:
  - Returns `base_outlook` unchanged.
- If `distress_notches < 0` (distress active):
  - Compares t1 → t0 for `interest_coverage`, `dscr`, `altman_z`.
  - Sets flags:
    - `improving = True` if any ratio increased.
    - `deteriorating = True` if any ratio decreased.
  - Rules:
    - Improving and **not** deteriorating → **Stable**.
    - Deteriorating and **not** improving → **Negative**.
    - Mixed / flat → **Stable**.

Important: under distress, the outlook is at most **Stable**; you do not get a **Positive** outlook while you are still being notched down for distress.

---

### 1.3 Sovereign cap

If enabled, the sovereign cap ensures the issuer is not rated above the sovereign on the same internal scale.

- `apply_sovereign_cap(hardstop_rating, sovereign_rating)`:
  - Returns the worse of (hardstop_rating, sovereign_rating) along `RATING_SCALE`.

When the cap is **binding** (i.e. it actually lowers the post‑distress rating):

- If `sovereign_outlook` is one of {Positive, Stable, Negative}, the issuer’s outlook is **set equal** to the sovereign outlook.
- In this case, the internal band/distress-based outlook is effectively overridden.

---

## 2. Decision ladder

The model uses the following ladder to determine the **final outlook**:

1. **Compute base outlook from the uncapped rating band**  
   - `base_outlook = derive_outlook_band_only(combined_score, uncapped_rating)`
   - This gives Positive / Stable / Negative purely from where the score sits inside the uncapped rating band.

2. **Apply distress overlay (if hardstops are enabled and active)**  
   - If `enable_hardstops = False` OR `distress_notches >= 0`:
     - `outlook_after_distress = base_outlook`.
   - If `enable_hardstops = True` AND `distress_notches < 0`:
     - `outlook_after_distress = derive_outlook_with_distress_trend(base_outlook, distress_notches, fin_t0, fin_t1)`.
     - This can move the outlook to **Negative** (deteriorating) or **Stable** (improving/mixed) but never to Positive.

3. **Apply sovereign cap overlay (if enabled and binding)**  
   - If `enable_sovereign_cap = True` and `apply_sovereign_cap` lowers the rating relative to `hardstop_rating`:
     - `final_outlook = sovereign_outlook` (if valid), else Stable.
   - Otherwise:
     - `final_outlook = outlook_after_distress`.

4. **AAA safeguard**  
   - If `final_rating == "AAA"` and `final_outlook == "Positive"`:
     - Set `final_outlook = "Stable"`.

---

## 3. Scenario summary

### Scenario A – Hardstops OFF, Sovereign cap OFF

- `enable_hardstops = False`, `enable_sovereign_cap = False`.
- Distress notches ignored (`distress_notches` forced to 0).
- Final rating = uncapped rating.
- Outlook = **band-based** only:
  - Bottom of band → Negative.
  - Top of band → Positive.
  - Middle → Stable.

Use this when you want a **pure score-driven** outlook.

---

### Scenario B – Hardstops ON, no distress

- `enable_hardstops = True`, but all distress metrics above their comfort thresholds.
- `distress_notches >= 0` → distress overlay does nothing.
- Outlook = **band-based** (as in Scenario A).

Use this when there is **no distress**, so distress logic is inert.

---

### Scenario C – Hardstops ON, distress deteriorating

- `enable_hardstops = True`, `distress_notches < 0`.
- From t1 → t0, distress metrics (coverage / DSCR / Altman Z) **worsen**.
- Outlook:
  - Distress trend overlay forces **Negative**, even if the band alone would have suggested Stable or Positive.

Interpretation: the entity is in a distressed zone and getting worse, so outlook must be Negative.

---

### Scenario D – Hardstops ON, distress improving

- `enable_hardstops = True`, `distress_notches < 0`.
- Distress metrics under their thresholds but **improving** vs t1.
- Outlook:
  - Distress trend overlay forces **Stable** (you stay notched down, but the trend is improving).

Interpretation: still in distress, but on a better trajectory; no Positive outlook until hardstops no longer apply.

---

### Scenario E – Hardstops ON, mixed/flat distress trend

- `enable_hardstops = True`, `distress_notches < 0`.
- Distress metrics show a mix of small improvements and deteriorations or are largely flat.
- Outlook:
  - Distress trend overlay forces **Stable**.

Interpretation: distress exists, but trend is not clearly worsening; Negative outlook is reserved for clearly deteriorating distress.

---

### Scenario F – Sovereign cap ON and binding

- `enable_sovereign_cap = True`.
- After hardstops, `hardstop_rating` is **above** `sovereign_rating`, so `apply_sovereign_cap` lowers it.
- Final rating = sovereign‑capped rating.
- Final outlook = **sovereign_outlook** (if Positive/Stable/Negative, else Stable).

Interpretation: external constraint from the sovereign dominates both rating and outlook.

---

### Scenario G – Sovereign cap ON but not binding

- `enable_sovereign_cap = True`, but `hardstop_rating` ≤ `sovereign_rating`.
- Final rating = hardstop rating.
- Outlook = result of band + distress logic (Scenarios A–E).

Interpretation: internal logic fully determines the issuer’s outlook; the sovereign cap is not active in practice.

---

## 4. Design intent (intuitive summary)

- **If only the combined score matters** (no distress, no binding sovereign cap), the outlook is simply a function of where the score sits within the **uncapped rating band**.
- **If distress is actively notching the rating down**, the outlook cannot be Positive; it becomes either Stable (if distress is improving or mixed) or Negative (if distress is clearly deteriorating).
- **If the sovereign cap binds**, the sovereign’s own rating and outlook become the anchor, and the issuer’s outlook aligns to that.

This structure keeps the outlook consistent with the main driver of the rating in each case: pure score, distress constraints, or sovereign ceiling.
