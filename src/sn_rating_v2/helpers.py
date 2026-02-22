# SN Corporate Rating Model V2 package

import logging
import math
from statistics import mean
from typing import Dict, List, Optional, Tuple

from .config import (
    RATIO_GRIDS,
    QUAL_SCORE_SCALE,
    SCORE_TO_RATING,
    RATING_SCALE,
    RATING_WEIGHTS,
    DISTRESS_BANDS,
    MAX_DISTRESS_NOTCHES,
)


def score_ratio(name: str, value: float) -> Optional[float]:
    grid = RATIO_GRIDS.get(name)
    if not grid or value is None or math.isnan(value):
        return None
    for low, high, score in grid:
        if low <= value < high:
            return float(score)
    return None


def score_qual_factor_numeric(value: int) -> Optional[float]:
    return QUAL_SCORE_SCALE.get(int(value))


def compute_altman_z_from_components(
    working_capital: float,
    total_assets: float,
    retained_earnings: float,
    ebit: float,
    market_value_equity: float,
    total_liabilities: float,
    sales: float,
) -> float:
    if total_assets == 0 or total_liabilities == 0:
        return float("nan")
    A = working_capital / total_assets
    B = retained_earnings / total_assets
    C = ebit / total_assets
    D = market_value_equity / total_liabilities
    E = sales / total_assets
    return 1.2 * A + 1.4 * B + 3.3 * C + 0.6 * D + 1.0 * E


def compute_peer_score(
    fin_current: Dict[str, float],
    peers: Dict[str, List[float]],
) -> Optional[float]:
    under = 0
    total = 0
    for rname, peer_vals in peers.items():
        if rname not in fin_current or not peer_vals:
            continue
        cp = fin_current[rname]
        peer_avg = mean(peer_vals)
        if peer_avg == 0:
            continue
        total += 1
        if cp < peer_avg * 0.9:
            under += 1
    if total == 0:
        return None
    under_share = under / total
    if under_share <= 0.10:
        return 100.0
    elif under_share <= 0.30:
        return 75.0
    elif under_share <= 0.60:
        return 50.0
    elif under_share <= 0.80:
        return 25.0
    else:
        return 0.0


def score_to_rating(score: float) -> str:
    for cutoff, grade in SCORE_TO_RATING:
        if score >= cutoff:
            return grade
    raise ValueError(f"Score {score} did not match any cutoff")


def safe_score_to_rating(score: float) -> str:
    try:
        return score_to_rating(score)
    except ValueError as e:
        logging.error("Score-to-rating mapping failed: %s", e)
        return "N/R"


def move_notches(grade: str, notches: int) -> str:
    if grade not in RATING_SCALE:
        return grade
    idx = RATING_SCALE.index(grade)
    new_idx = max(0, min(idx - notches, len(RATING_SCALE) - 1))
    return RATING_SCALE[new_idx]


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
    return RATING_SCALE[max(i, s)]


def compute_effective_weights(n_quant: int, n_qual: int) -> Tuple[float, float]:
    """
    Determine effective quantitative vs qualitative weights.

    Priority:
    1) If both weights are explicitly configured in RATING_WEIGHTS, use them.
    2) Otherwise, weight automatically in proportion to the number of active
       quantitative and qualitative items.
    3) If there are no active items at all, return (0.0, 0.0).
    """
    wq_cfg = RATING_WEIGHTS["quantitative"]
    wl_cfg = RATING_WEIGHTS["qualitative"]

    if wq_cfg is not None and wl_cfg is not None:
        return float(wq_cfg), float(wl_cfg)

    n_quant = max(n_quant, 0)
    n_qual = max(n_qual, 0)
    total = n_quant + n_qual

    if total == 0:
        return 0.0, 0.0

    wq = n_quant / total
    wl = n_qual / total
    return wq, wl


def get_rating_band(rating: str) -> Tuple[float, float]:
    # returns inclusive score band [min, max] that maps to rating
    for i, (cutoff, grade) in enumerate(SCORE_TO_RATING):
        if grade == rating:
            band_min = cutoff
            if i == 0:
                band_max = 100.0
            else:
                prev_cutoff, _ = SCORE_TO_RATING[i - 1]
                band_max = prev_cutoff - 1.0
            return band_min, band_max
    raise ValueError(f"Unknown rating grade: {rating!r}")


def derive_outlook_band_only(combined_score: float, rating: str) -> str:
    """Band-based outlook on the base rating, using floored score."""
    band_min, band_max = get_rating_band(rating)
    cs = math.floor(combined_score)
    if cs == band_max:
        return "Positive"
    elif cs == band_min:
        return "Negative"
    else:
        return "Stable"


def derive_outlook_with_distress_trend(
    base_outlook: str,
    distress_notches: int,
    fin_t0: Dict[str, float],
    fin_t1: Dict[str, float],
) -> str:
    """Adjust outlook when hardstops are active based on trend in distress ratios."""
    if distress_notches >= 0:
        return base_outlook

    ratios = ["interest_coverage", "dscr", "altman_z"]
    improving = False
    deteriorating = False

    for r in ratios:
        v0 = fin_t0.get(r)
        v1 = fin_t1.get(r)
        if v0 is None or v1 is None:
            continue
        # higher is better
        if v0 > v1:
            improving = True
        elif v0 < v1:
            deteriorating = True

    if improving and not deteriorating:
        return "Stable"
    if deteriorating and not improving:
        return "Negative"
    return "Stable"
