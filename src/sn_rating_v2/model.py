# SN Corporate Rating Model V2 package

import logging
from typing import Dict, List, Optional, Tuple

from .config import (
    RATIO_FAMILY,
    DISTRESS_BANDS,
    MAX_DISTRESS_NOTCHES,
)
from .datamodel import QuantInputs, QualInputs, RatingOutputs
from .helpers import (
    compute_altman_z_from_components,
    compute_peer_score,
    score_ratio,
    score_qual_factor_numeric,
    compute_effective_weights,
    move_notches,
    apply_sovereign_cap,
    derive_outlook_band_only,
    derive_outlook_with_distress_trend,
    safe_score_to_rating,
)


class RatingModel:
    def __init__(self, cp_name: str):
        self.cp_name = cp_name

    def _ensure_altman_z(self, fin: Dict[str, float], comps: Dict[str, float]) -> float:
        # compute Altman Z if not already present
        if "altman_z" in fin and fin["altman_z"] is not None:
            return fin["altman_z"]
        z = compute_altman_z_from_components(
            comps["working_capital"],
            comps["total_assets"],
            comps["retained_earnings"],
            comps["ebit"],
            comps["market_value_equity"],
            comps["total_liabilities"],
            comps["sales"],
        )
        fin["altman_z"] = z
        logging.info("%s-AltmanZ: computed z=%.3f from components", self.cp_name, z)
        return z

    def compute_quantitative(
        self,
        q: QuantInputs,
    ) -> Tuple[float, Optional[float], Dict[str, float], float, int]:
        fin = dict(q.fin_t0)  # copy to avoid mutating caller
        altman_z = self._ensure_altman_z(fin, q.components_t0)

        scores: List[float] = []
        bucket_scores: Dict[str, List[float]] = {
            "leverage": [],
            "leverage_rev": [],
            "coverage": [],
            "profit": [],
            "other": [],
            "altman": [],
        }

        n_quant_items = 0

        for rname, val in fin.items():
            if rname not in RATIO_FAMILY:
                continue
            s = score_ratio(rname, val)
            if s is None:
                logging.info("%s-Quant: no grid/score for ratio %s", self.cp_name, rname)
                continue
            scores.append(s)
            n_quant_items += 1
            family = RATIO_FAMILY[rname]
            bucket_scores.setdefault(family, []).append(s)
            logging.info(
                "%s-Quant: %s value=%.3f score=%.1f family=%s",
                self.cp_name,
                rname,
                val,
                s,
                family,
            )

        peer_score = compute_peer_score(fin, q.peers_t0)
        if peer_score is not None:
            scores.append(peer_score)
            n_quant_items += 1
            bucket_scores["other"].append(peer_score)
            logging.info("%s-PeerPositioning: score=%.1f", self.cp_name, peer_score)

        quantitative_score = sum(scores) / len(scores) if scores else 0.0
        logging.info("%s-Quant: aggregate score=%.1f", self.cp_name, quantitative_score)

        bucket_avgs = {
            b: round(sum(vals) / len(vals), 1) if vals else 0.0
            for b, vals in bucket_scores.items()
        }

        return quantitative_score, peer_score, bucket_avgs, altman_z, n_quant_items

    def compute_qualitative(self, ql: QualInputs) -> Tuple[float, int]:
        scores: List[float] = []
        n_qual_items = 0
        for name, val in ql.factors_t0.items():
            s = score_qual_factor_numeric(val)
            if s is None:
                logging.info(
                    "%s-Qual: unknown or out-of-range factor %s=%s",
                    self.cp_name,
                    name,
                    val,
                )
                continue
            scores.append(s)
            n_qual_items += 1
            logging.info(
                "%s-Qual: %s=%s score=%.1f",
                self.cp_name,
                name,
                val,
                s,
            )
        qualitative_score = sum(scores) / len(scores) if scores else 0.0
        logging.info(
            "%s-Qual: aggregate score=%.1f",
            self.cp_name,
            qualitative_score,
        )
        return qualitative_score, n_qual_items

    def compute_distress_notches(
        self,
        fin: Dict[str, float],
        altman_z: float,
    ) -> Tuple[int, Dict[str, float]]:
        total_notches = 0
        details: Dict[str, float] = {}

        ic = fin.get("interest_coverage")
        if ic is not None:
            for threshold, notches in DISTRESS_BANDS["interest_coverage"]:
                if ic < threshold:
                    total_notches += notches
                    details["interest_coverage"] = ic
                    break

        dscr = fin.get("dscr")
        if dscr is not None:
            for threshold, notches in DISTRESS_BANDS["dscr"]:
                if dscr < threshold:
                    total_notches += notches
                    details["dscr"] = dscr
                    break

        for threshold, notches in DISTRESS_BANDS["altman_z"]:
            if altman_z < threshold:
                total_notches += notches
                details["altman_z"] = altman_z
                break

        if total_notches < MAX_DISTRESS_NOTCHES:
            total_notches = MAX_DISTRESS_NOTCHES

        return total_notches, details

    def compute_final_rating(
        self,
        quant_inputs: QuantInputs,
        qual_inputs: QualInputs,
        sovereign_rating: Optional[str] = None,
        sovereign_outlook: Optional[str] = None,
        enable_hardstops: bool = False,
        enable_sovereign_cap: bool = False,
    ) -> RatingOutputs:
        # 1) Quantitative and qualitative scores
        quant_score, peer_score, bucket_avgs, altman_z, n_quant = self.compute_quantitative(
            quant_inputs
        )
        qual_score, n_qual = self.compute_qualitative(qual_inputs)

        # 2) Effective weights
        wq, wl = compute_effective_weights(n_quant, n_qual)
        logging.info(
            "%s-Weights: n_quant=%d n_qual=%d -> wq=%.3f wl=%.3f",
            self.cp_name,
            n_quant,
            n_qual,
            wq,
            wl,
        )

        combined_score = wq * quant_score + wl * qual_score  # weighted average

        # 3) Base rating (model-only rating, no hardstops/cap)
        base_rating = safe_score_to_rating(combined_score)

        # 4) Hardstops / distress notches
        if enable_hardstops:
            distress_notches, hardstop_details = self.compute_distress_notches(
                quant_inputs.fin_t0,
                altman_z,
            )
        else:
            distress_notches = 0
            hardstop_details = {}

        hardstop_rating = move_notches(base_rating, distress_notches)
        hardstop_triggered = distress_notches < 0

        # 5) Sovereign cap application
        capped_rating = hardstop_rating
        if enable_sovereign_cap and sovereign_rating is not None:
            capped_rating = apply_sovereign_cap(hardstop_rating, sovereign_rating)

        final_rating = capped_rating  # currently no further adjustments

        # 6) Sovereign cap binding definition
        sovereign_cap_binding = (
            enable_sovereign_cap
            and sovereign_rating is not None
            and final_rating == sovereign_rating
        )

        # 7) Outlook logic
        # 1) Band-based base outlook from score position within rating band
        base_outlook = derive_outlook_band_only(combined_score, base_rating)

        # 2) Sovereign-binding branch
        if (
            sovereign_cap_binding
            and sovereign_outlook in {"Positive", "Stable", "Negative"}
        ):
            # Special aligned case: issuer rating == sovereign rating and same outlook
            # → keep model's band-based base_outlook
            if (
                hardstop_rating == capped_rating == sovereign_rating
                and base_outlook == sovereign_outlook
            ):
                outlook = base_outlook
            else:
                # Sovereign-aligned outlook when issuer is capped at or below sovereign
                if base_outlook == "Positive" and sovereign_outlook in {
                    "Stable",
                    "Negative",
                }:
                    # If model is more optimistic than the sovereign, sovereign dominates
                    outlook = sovereign_outlook
                elif base_outlook == "Negative" or sovereign_outlook == "Negative":
                    # if either side is Negative, keep it conservative
                    outlook = "Negative"
                else:
                    # Both sides non-Negative and not more optimistic than sovereign → Stable
                    outlook = "Stable"
        # 3) Non-binding / no-cap branch: distress-trend overlay
        else:
            # No binding: add distress trend logic on top of base_outlook
            # and only adjust if a distress hardstop actually bit (distress_notches < 0)
            outlook = derive_outlook_with_distress_trend(
                base_outlook,
                distress_notches,
                quant_inputs.fin_t0,
                quant_inputs.fin_t1,
            )

        # 4) Final guard: no Positive outlook at AAA
        if final_rating == "AAA" and outlook == "Positive":
            outlook = "Stable"

        # 8) Flags always present
        flags = {
            "enable_hardstops": enable_hardstops,
            "enable_sovereign_cap": enable_sovereign_cap and (sovereign_rating is not None),
            "hardstop_triggered": hardstop_triggered,
            "sovereign_cap_binding": sovereign_cap_binding,
        }

        # 9) Rating explanation (driven by flags and binding)
        parts: List[str] = []

        # Core model
        parts.append(
            f"Based on the quantitative and qualitative factors, the combined score is "
            f"{combined_score:.1f}, corresponding to a base rating of {base_rating}."
        )

        # Distress / hardstops
        if hardstop_triggered:
            parts.append(
                f" Distress factors {list(hardstop_details.keys())} triggered a total "
                f"of {abs(distress_notches)} notch(es) of downgrade, resulting in a "
                f"post-distress (hardstop) rating of {hardstop_rating}."
            )
        else:
            parts.append(
                f" No distress-related hardstops were applied, so the hardstop rating "
                f"remains equal to the base rating at {hardstop_rating}."
            )

        # Sovereign cap
        if enable_sovereign_cap and sovereign_rating is not None:
            if sovereign_cap_binding:
                if hardstop_rating != capped_rating:
                    # sovereign actively worsens the rating relative to hardstop
                    parts.append(
                        f" The sovereign cap is binding: given the sovereign rating of "
                        f"{sovereign_rating}, the rating is constrained from {hardstop_rating} "
                        f"to a capped rating of {capped_rating}."
                    )
                else:
                    # issuer is at sovereign level; cap is effectively binding at that level
                    parts.append(
                        f" The issuer's rating is aligned with the sovereign rating at "
                        f"{sovereign_rating}, so the sovereign cap is effectively binding."
                    )
            else:
                # cap present but not constraining
                parts.append(
                    f" A sovereign rating of {sovereign_rating} is considered, but it does not "
                    f"constrain the issuer rating, so the capped rating remains {capped_rating}."
                )
        else:
            # no cap applied
            parts.append(
                f" No sovereign cap is applied, so the capped rating is the same as the "
                f"post-distress rating at {capped_rating}."
            )

        # Final sentence
        parts.append(
            f" The final issuer rating is {final_rating} with an outlook of {outlook}."
        )

        rating_explanation = "".join(parts)

        logging.info(
            "%s-Final: base=%s hardstop=%s capped=%s final=%s outlook=%s distress_notches=%d",
            self.cp_name,
            base_rating,
            hardstop_rating,
            capped_rating,
            final_rating,
            outlook,
            distress_notches,
        )

        return RatingOutputs(
            issuer_name=self.cp_name,
            quantitative_score=quant_score,
            qualitative_score=qual_score,
            combined_score=combined_score,
            peer_score=peer_score,
            base_rating=base_rating,
            distress_notches=distress_notches,
            hardstop_rating=hardstop_rating,
            capped_rating=capped_rating,
            final_rating=final_rating,
            hardstop_triggered=hardstop_triggered,
            hardstop_details=hardstop_details,
            sovereign_rating=sovereign_rating,
            sovereign_outlook=sovereign_outlook,
            sovereign_cap_binding=sovereign_cap_binding,
            outlook=outlook,
            bucket_avgs=bucket_avgs,
            altman_z_t0=altman_z,
            flags=flags,
            rating_explanation=rating_explanation,
        )
