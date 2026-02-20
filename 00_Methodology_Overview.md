# 00_Methodology_Overview

## Executive Summary

The model is designed to differentiate structural credit quality rather than to forecast short‑term default events. The deterministic structure prioritizes transparency, auditability, and governance over statistical optimization, consistent with its intended role as an internal decision‑support tool rather than a purely predictive model.

## Internal Rating Scale

The internal scale is aligned conceptually with the familiar AAA–D framework used by major agencies, with an explicit boundary between investment‑grade (BBB− and above) and speculative‑grade ratings. Ratings are intended as an ordinal ranking of relative long‑term default risk, not as direct probability‑of‑default estimates; mappings to PD bands, if required, are maintained separately from this methodology.

## Scope and Intended Use

The model is intended for non‑financial corporates with standard financial reporting and is used for internal credit grading, limit setting, portfolio monitoring, and decision support. It is not designed for banks, insurers, project finance SPVs, or highly specialized structures, which require sector‑specific methodologies or additional overlays.

## Conceptual Framework

The methodology follows an expert‑driven, rules‑based scorecard structure: standardized financial inputs are mapped to ratio‑level subscores, aggregated into a base rating, and then adjusted via structured overlays (distress, sovereign cap, and notching). The framework is explicitly through‑the‑cycle and deterministic, ensuring that identical inputs always produce the same rating and supporting robust replication for audit and validation.

## Ratio Families

Financial metrics are organized into coherent ratio families—leverage, coverage, cash flow, profitability, liquidity, investment intensity, and composite distress (Altman Z‑score)—each with monotone, contiguous grading grids. These families mirror market and agency practice and ensure that higher economic risk is consistently mapped to lower subscores across dimensions.

## Overlays

Overlays adjust the base rating for factors not fully captured in static financial ratios, with a focus on downside protection. The distress overlay imposes mandatory downgrades when acute distress signals are present, while the sovereign cap overlay constrains corporate ratings relative to the home sovereign except in defined exceptional cases. All overlays are implemented as transparent, rule‑based notching steps to minimize ad‑hoc judgement and support consistent treatment across issuers.

## Limitations

Key limitations include reliance on historical financial statements, expert‑driven (rather than statistically optimized) thresholds and weights, and limited explicit treatment of qualitative factors such as governance quality and competitive positioning. The through‑the‑cycle design improves stability but can slow reaction to sharp regime shifts or event‑driven deterioration, and the model’s parameters and structure are subject to typical model‑risk and specification uncertainties.

## Model Boundaries

This is not a regulatory IRB model, is not calibrated to Basel capital requirements, and is not a market‑implied spread model or a structural asset‑value model in the Merton tradition. It should not be used as a standalone PD or LGD engine; instead, it provides an internally consistent ranking of credit quality that can be combined with separate capital, pricing, and portfolio models.

## Governance

The model is governed under a formal model‑risk framework that emphasizes transparency, independent validation, change control, and ongoing performance monitoring. RatingOutputs serves as the authoritative record of each run, while documented override policies, data‑quality flags, and periodic back‑testing ensure that model use remains controlled, explainable, and aligned with the institution’s risk appetite and regulatory expectations.
