# SN Corporate Rating Model V2 package
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class QuantInputs:
    fin_t0: Dict[str, float]  # current period
    fin_t1: Dict[str, float]  # previous period
    fin_t2: Dict[str, float]  # two periods ago
    components_t0: Dict[str, float]
    components_t1: Dict[str, float]
    components_t2: Dict[str, float]
    peers_t0: Dict[str, List[float]]


@dataclass
class QualInputs:
    factors_t0: Dict[str, int]  # 1–5 values
    factors_t1: Dict[str, int]


@dataclass
class RatingOutputs:
    issuer_name: str
    quantitative_score: float
    qualitative_score: float
    combined_score: float
    peer_score: Optional[float]
    base_rating: str  # model rating before hardstops / cap
    distress_notches: int
    hardstop_rating: str  # rating after distress notches
    capped_rating: str  # rating after sovereign cap
    final_rating: str  # delivered rating (currently = capped)
    hardstop_triggered: bool
    hardstop_details: Dict[str, float]
    sovereign_rating: Optional[str]
    sovereign_outlook: Optional[str]
    sovereign_cap_binding: bool  # True if final_rating == sovereign_rating
    outlook: str
    bucket_avgs: Dict[str, float]
    altman_z_t0: float
    flags: Dict[str, bool]
    rating_explanation: str
