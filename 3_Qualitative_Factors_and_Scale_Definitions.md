# Qualitative Factors and Scale Definitions

This document describes the qualitative factors used in the V2 corporate rating model and how their 1–5 scores are interpreted.

In V2, qualitative factors use a **1–5 scale where 1 = weakest and 5 = strongest**.  
Scores are mapped to the internal 0–100 scale via:

- 5 → 100  
- 4 → 75  
- 3 → 50  
- 2 → 25  
- 1 → 0  

> Note: This is the **opposite** of the V1 convention, where 1 was strongest and 5 weakest.

All valid qualitative factors are treated equally and averaged into a single qualitative score; there is no factor‑specific weighting in V2.

The factor set is flexible in the sense that the model uses whatever keys are present in `factors_t0` / `factors_t1`. If a factor is missing or has an invalid value, it is ignored, and only the remaining valid factors are averaged.

---

## Business and industry risk

### `industry_risk`

- **Dimension**: Business / industry risk  
- **Meaning**: Captures the structural risk profile of the issuer’s main industry (cyclicality, entry barriers, structural growth/decline, regulatory burden).  
- **Scale examples**:  
  - 1: Very high‑risk, structurally challenged or highly cyclical industry.  
  - 3: Average risk industry with moderate cyclicality.  
  - 5: Very resilient industry with stable demand and strong structural fundamentals.  

### `revenue_stability`

- **Dimension**: Earnings and revenue volatility  
- **Meaning**: Assesses how stable revenues and earnings are over the cycle (volatility, contract coverage, customer stickiness).  
- **Scale examples**:  
  - 1: Highly volatile revenues, strongly cyclical, little visibility.  
  - 3: Moderate volatility, partly contractual or diversified.  
  - 5: Very stable, long‑term contracted or regulated revenues.

### `revenue_diversification`

- **Dimension**: Business diversification  
- **Meaning**: Measures diversification across products, geographies, and customers.  
- **Scale examples**:  
  - 1: Highly concentrated on one product/customer/region.  
  - 3: Some diversification but still meaningful concentration risks.  
  - 5: Well diversified across multiple products, regions, and customers.

---

## Market position and competitiveness

### `market_position`

- **Dimension**: Competitive position  
- **Meaning**: Assesses the issuer’s market share, pricing power, and brand strength relative to peers.  
- **Scale examples**:  
  - 1: Weak player with small share and limited pricing power.  
  - 3: Solid but non‑dominant player with average pricing power.  
  - 5: Leading player with strong market share and pricing power.

---

## Management quality and governance

### `management_quality`

- **Dimension**: Management quality / execution  
- **Meaning**: Evaluates the track record, strategic discipline, and execution capability of management.  
- **Scale examples**:  
  - 1: Weak track record, volatile strategy, frequent negative surprises.  
  - 3: Adequate track record with some execution risks.  
  - 5: Strong, experienced management with consistent execution.

### `governance`

- **Dimension**: Corporate governance  
- **Meaning**: Assesses governance framework, board independence, shareholder alignment, and risk controls.  
- **Scale examples**:  
  - 1: Poor governance, weak controls, significant related‑party or key‑person risks.  
  - 3: Standard governance with some areas for improvement.  
  - 5: Strong, transparent governance with robust checks and balances.

### `financial_policy`

- **Dimension**: Financial policy / risk appetite  
- **Meaning**: Captures management’s attitude towards leverage, shareholder returns, and balance sheet conservatism.  
- **Scale examples**:  
  - 1: Aggressive policy (high leverage targets, frequent leveraged transactions).  
  - 3: Neutral, flexible policy with moderate leverage targets.  
  - 5: Very conservative policy, clear commitment to strong credit metrics.

---

## Liquidity and refinancing profile

### `liquidity_profile`

- **Dimension**: Liquidity management  
- **Meaning**: Assesses available liquidity (cash, RCF headroom) versus near‑term needs and the quality of liquidity planning.  
- **Scale examples**:  
  - 1: Thin liquidity, tight headroom, reliance on opportunistic funding.  
  - 3: Adequate liquidity with some buffer.  
  - 5: Strong, well‑managed liquidity with substantial committed headroom.

### `refinancing_risk`

- **Dimension**: Refinancing and maturity profile  
- **Meaning**: Evaluates concentration of debt maturities, access to capital markets, and refinancing risk.  
- **Scale examples**:  
  - 1: Very high refinancing risk (large near‑term maturities, uncertain market access).  
  - 3: Manageable refinancing profile with some concentration.  
  - 5: Well‑staggered maturities and strong, diversified funding access.

### `wc_management_quality`

- **Dimension**: Working capital management  
- **Meaning**: Assesses how efficiently the issuer manages receivables, payables, and inventories.  
- **Scale examples**:  
  - 1: Poor working capital discipline, frequent cash swings.  
  - 3: Acceptable management with occasional issues.  
  - 5: Strong discipline and predictable working capital behaviour.

---

## Country, sovereign, and legal environment

### `sovereign_risk`

- **Dimension**: Country / sovereign risk  
- **Meaning**: Reflects macroeconomic stability, political risk, and sovereign creditworthiness of the primary operating country.  
- **Scale examples**:  
  - 1: Very high‑risk country with weak institutions and frequent shocks.  
  - 3: Moderate‑risk country with reasonable macro and institutional framework.  
  - 5: Low‑risk, stable country with strong institutions.

### `legal_environment`

- **Dimension**: Legal and institutional environment  
- **Meaning**: Assesses the strength of legal protections, creditor rights, and enforcement mechanisms.  
- **Scale examples**:  
  - 1: Weak legal environment, uncertain enforcement, limited creditor protection.  
  - 3: Adequate but imperfect legal framework.  
  - 5: Strong rule of law and predictable enforcement.

---

## Qualitative inputs over time

The model takes qualitative inputs for at least two periods:

- `factors_t0`: Current qualitative assessment (primary input).  
- `factors_t1`: Previous or prior‑year assessment (used by `derive_outlook_with_distress_trend` when distress hardstops are active).

In V2, the outlook logic:

- Derives a base outlook from the rating band and combined score.  
- Adjusts this outlook using **distress trends** (based primarily on quantitative distress ratios).  
- If a sovereign cap is binding and a sovereign outlook is provided, the issuer outlook is overridden and anchored to the sovereign outlook.


