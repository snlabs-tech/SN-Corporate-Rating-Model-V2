# Quantitative Factors and Ratio Definitions

This document describes the quantitative ratios used in the V2 corporate rating model, how they are defined, and why they are included in the analysis.

All ratios are ultimately mapped to a 0–100 internal score using `RATIO_GRIDS[name] = [(low, high, score), ...]`. For each ratio, the grid is defined so that more favourable values (for that specific ratio) receive higher scores – whether that means a higher or a lower numeric value.

---

## Leverage ratios

### `debt_ebitda` — Debt / EBITDA

- **Category**: Leverage  
- **Definition**: Total debt divided by EBITDA (earnings before interest, taxes, depreciation, and amortization).  
- **Why it matters**: Indicates how many years of current EBITDA would be needed to repay total debt. Higher values signal higher leverage and weaker debt capacity.  
- **Model scoring** (example grid used in V2):  
  - `< 2.0` → 100  
  - `2.0–3.0` → 75  
  - `3.0–4.0` → 50  
  - `4.0–6.0` → 25  
  - `> 6.0` → 0  

---

### `net_debt_ebitda` — Net Debt / EBITDA

- **Category**: Leverage  
- **Definition**: Net debt (debt minus cash and cash‑equivalents) divided by EBITDA.  
- **Why it matters**: Adjusts gross leverage for available cash; a more refined leverage indicator than `debt_ebitda` in cash‑rich or cash‑poor situations.  
- **Model scoring**:  
  - `< 1.5` → 100  
  - `1.5–3.0` → 75  
  - `3.0–4.5` → 50  
  - `4.5–6.0` → 25  
  - `> 6.0` → 0  

---

### `ffo_debt` — FFO / Debt

- **Category**: Leverage (cash‑flow based)  
- **Definition**: Funds from operations (FFO) divided by total debt.  
- **Why it matters**: Measures recurrent cash‑flow capacity to service and repay debt; higher values indicate stronger deleveraging capacity.  
- **Model scoring**:  
  - `≥ 0.40` → 100  
  - `0.25–0.40` → 75  
  - `0.12–0.25` → 50  
  - `0.00–0.12` → 25  
  - `< 0.00` → 0  

---

### `fcf_debt` — FCF / Debt

- **Category**: Leverage (cash‑flow based)  
- **Definition**: Free cash flow (after capex and working capital) divided by total debt.  
- **Why it matters**: Captures the issuer’s ability to reduce debt from fully discretionary cash flow after investments; persistent negative values are a warning signal.  
- **Model scoring**:  
  - `≥ 0.20` → 100  
  - `0.10–0.20` → 75  
  - `0.00–0.10` → 50  
  - `‑0.10–0.00` → 25  
  - `< ‑0.10` → 0  

---

### `debt_equity` — Debt / Equity

- **Category**: Leverage (capital structure)  
- **Definition**: Total debt divided by total equity.  
- **Why it matters**: Measures the balance between debt and equity funding; higher values mean thinner equity buffers and higher financial risk.  
- **Model scoring**:  
  - `< 0.5` → 100  
  - `0.5–1.0` → 75  
  - `1.0–2.0` → 50  
  - `2.0–4.0` → 25  
  - `> 4.0` → 0  

---

### `debt_capital` — Debt / (Debt + Equity)

- **Category**: Leverage (capital structure)  
- **Definition**: Total debt divided by total capital (debt plus equity).  
- **Why it matters**: Alternative leverage measure; higher ratios indicate more debt‑heavy capital structures and less loss‑absorbing equity.  
- **Model scoring**:  
  - `< 0.20` → 100  
  - `0.20–0.35` → 75  
  - `0.35–0.50` → 50  
  - `0.50–0.70` → 25  
  - `> 0.70` → 0  

---

## Coverage ratios

### `interest_coverage` — EBITDA / Interest (or similar)

- **Category**: Coverage  
- **Definition**: Earnings (EBITDA or EBIT, depending on definition) divided by interest expense.  
- **Why it matters**: Indicates the headroom to service interest from recurring earnings; low values are a classic distress signal and feed into hardstop logic.  
- **Model scoring**:  
  - `≥ 8.0` → 100  
  - `5.0–8.0` → 75  
  - `3.0–5.0` → 50  
  - `1.5–3.0` → 25  
  - `< 1.5` → 0  

---

### `fixed_charge_coverage` — Fixed‑Charge Coverage

- **Category**: Coverage  
- **Definition**: Earnings relative to all fixed charges (interest plus lease payments, etc.).  
- **Why it matters**: Broadens coverage beyond pure interest to include other fixed financial commitments.  
- **Model scoring**:  
  - `≥ 6.0` → 100  
  - `4.0–6.0` → 75  
  - `2.5–4.0` → 50  
  - `1.5–2.5` → 25  
  - `< 1.5` → 0  

---

### `dscr` — Debt Service Coverage Ratio

- **Category**: Coverage  
- **Definition**: Cash flow available for debt service divided by total debt service (interest + principal repayments).  
- **Why it matters**: Direct measure of short‑term debt service capacity; low DSCR triggers distress notching.  
- **Model scoring**:  
  - `≥ 2.0` → 100  
  - `1.5–2.0` → 75  
  - `1.2–1.5` → 50  
  - `1.0–1.2` → 25  
  - `< 1.0` → 0  

---

## Profitability and return ratios

### `ebitda_margin` — EBITDA Margin

- **Category**: Profitability  
- **Definition**: EBITDA divided by revenue.  
- **Why it matters**: Captures operating profitability and buffer against shocks; higher margins typically support better ratings.  
- **Model scoring**:  
  - `≥ 25%` → 100  
  - `15–25%` → 75  
  - `10–15%` → 50  
  - `5–10%` → 25  
  - `< 5%` → 0  

---

### `ebit_margin` — EBIT Margin

- **Category**: Profitability  
- **Definition**: EBIT divided by revenue.  
- **Why it matters**: Profitability after depreciation and amortisation; often more conservative than EBITDA margin.  
- **Model scoring**:  
  - `≥ 15%` → 100  
  - `10–15%` → 75  
  - `5–10%` → 50  
  - `0–5%` → 25  
  - `< 0%` → 0  

---

### `roa` — Return on Assets

- **Category**: Profitability / efficiency  
- **Definition**: Net income divided by total assets.  
- **Why it matters**: Indicates efficiency in generating profits from the asset base; persistently low ROA may signal weak business models or over‑investment.  
- **Model scoring**:  
  - `≥ 12%` → 100  
  - `8–12%` → 75  
  - `4–8%` → 50  
  - `0–4%` → 25  
  - `< 0%` → 0  

---

### `roe` — Return on Equity

- **Category**: Profitability / equity return  
- **Definition**: Net income divided by equity.  
- **Why it matters**: Measures returns for shareholders; very low or negative ROE may indicate structural issues; extremely high ROE can also signal leverage.  
- **Model scoring**:  
  - `≥ 20%` → 100  
  - `12–20%` → 75  
  - `5–12%` → 50  
  - `0–5%` → 25  
  - `< 0%` → 0  

---

## Investment and liquidity ratios

### `capex_dep` — Capex / Depreciation

- **Category**: Investment intensity  
- **Definition**: Capital expenditure divided by depreciation expense.  
- **Why it matters**: Indicates whether the issuer is under‑investing (capex below depreciation) or aggressively expanding (very high capex); both extremes can carry risk.  
- **Model scoring** (U‑shaped preference around “sustainable” levels):  
  - `1.2–1.8` → 100  
  - `0.9–1.2` or `1.8–2.5` → 75  
  - `0.7–0.9` or `2.5–3.5` → 50  
  - `0.5–0.7` or `> 3.5` → 25  
  - `< 0.5` → 0  

---

### `current_ratio` — Current Assets / Current Liabilities

- **Category**: Liquidity  
- **Definition**: Current assets divided by current liabilities.  
- **Why it matters**: Measures short‑term liquidity; very low values signal refinancing pressure, very high values may signal inefficient capital allocation.  
- **Model scoring**:  
  - `≥ 2.0` → 100  
  - `1.5–2.0` → 75  
  - `1.0–1.5` → 50  
  - `0.7–1.0` → 25  
  - `< 0.7` → 0  

---

### `rollover_coverage` — Rollover Coverage

- **Category**: Liquidity / refinancing  
- **Definition**: Cash plus committed undrawn lines relative to short‑term debt maturities (or similar proxy).  
- **Why it matters**: Captures near‑term refinancing risk; low values signal vulnerability to market closures or failed refinancing.  
- **Model scoring**:  
  - `≥ 2.0` → 100  
  - `1.2–2.0` → 75  
  - `0.8–1.2` → 50  
  - `0.5–0.8` → 25  
  - `< 0.5` → 0  

---

## Distress indicator

### `altman_z` — Altman Z‑score

- **Category**: Distress / solvency  
- **Definition**: Linear combination of working capital, retained earnings, EBIT, market value of equity, and sales, each scaled by assets or liabilities, per the classic Altman Z model.  
- **Why it matters**: Summarises default risk based on a set of accounting ratios; low Z‑scores are strongly associated with financial distress.  
- **Model use**:  
  - Scored via `RATIO_GRIDS["altman_z"]` into the Altman bucket.  
  - Also used in `DISTRESS_BANDS["altman_z"]` to drive hardstop notching when the Z‑score falls into distress territory.

---

## Missing data and flexibility

The quantitative block is tolerant to missing data:

- If a ratio is not provided or cannot be mapped in `RATIO_GRIDS`, it is skipped.  
- The aggregate quantitative score is computed from the remaining valid ratios.  
- The number of valid quantitative items is tracked and used in `compute_effective_weights` to derive the relative weight of the quantitative block.

