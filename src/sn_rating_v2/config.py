# SN Corporate Rating Model V2 package
import math
from typing import Dict, List, Tuple

# Map ratios to conceptual families
RATIO_FAMILY = {
    "debt_ebitda": "leverage",
    "net_debt_ebitda": "leverage",
    "debt_equity": "leverage",
    "debt_capital": "leverage",
    "ffo_debt": "leverage_rev",
    "fcf_debt": "leverage_rev",
    "interest_coverage": "coverage",
    "fixed_charge_coverage": "coverage",
    "dscr": "coverage",
    "ebitda_margin": "profit",
    "ebit_margin": "profit",
    "roa": "profit",
    "roe": "profit",
    "capex_dep": "other",
    "current_ratio": "other",
    "rollover_coverage": "other",
    "altman_z": "altman",
}

# Numerical score → rating grade cutoffs
SCORE_TO_RATING: List[Tuple[float, str]] = [
    (95, "AAA"),
    (90, "AA+"),
    (85, "AA"),
    (80, "AA-"),
    (75, "A+"),
    (70, "A"),
    (65, "A-"),
    (60, "BBB+"),
    (55, "BBB"),
    (50, "BBB-"),
    (45, "BB+"),
    (40, "BB"),
    (35, "BB-"),
    (30, "B+"),
    (25, "B"),
    (20, "B-"),
    (15, "CCC+"),
    (10, "CCC"),
    (5, "CCC-"),
    (2, "CC"),
    (0, "C"),
]

# Linear index scale for notch moves
RATING_SCALE = [
    "AAA", "AA+", "AA", "AA-",
    "A+", "A", "A-",
    "BBB+", "BBB", "BBB-",
    "BB+", "BB", "BB-",
    "B+", "B", "B-",
    "CCC+", "CCC", "CCC-",
    "CC", "C",
]

# Optional explicit weights; if None, auto-weight by count
RATING_WEIGHTS = {
    "quantitative": None,  # if None, auto-weight by count
    "qualitative": None,
}

DISTRESS_TRIGGERS = {
    "interest_coverage": 1.0,
    "dscr": 1.0,
    "altman_z": 1.81,
}

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

MAX_DISTRESS_NOTCHES = -4  # floor for cumulative distress notches

# Ratio grids: (low, high, score)
RATIO_GRIDS: Dict[str, List[Tuple[float, float, float]]] = {
    "debt_ebitda": [
        (float("-inf"), 2.0, 100),
        (2.0, 3.0, 75),
        (3.0, 4.0, 50),
        (4.0, 6.0, 25),
        (6.0, float("inf"), 0),
    ],
    "net_debt_ebitda": [
        (float("-inf"), 1.5, 100),
        (1.5, 3.0, 75),
        (3.0, 4.5, 50),
        (4.5, 6.0, 25),
        (6.0, float("inf"), 0),
    ],
    "ffo_debt": [
        (0.40, float("inf"), 100),
        (0.25, 0.40, 75),
        (0.12, 0.25, 50),
        (0.0, 0.12, 25),
        (float("-inf"), 0.0, 0),
    ],
    "fcf_debt": [
        (0.20, float("inf"), 100),
        (0.10, 0.20, 75),
        (0.0, 0.10, 50),
        (-0.10, 0.0, 25),
        (float("-inf"), -0.10, 0),
    ],
    "debt_equity": [
        (float("-inf"), 0.5, 100),
        (0.5, 1.0, 75),
        (1.0, 2.0, 50),
        (2.0, 4.0, 25),
        (4.0, float("inf"), 0),
    ],
    "debt_capital": [
        (float("-inf"), 0.20, 100),
        (0.20, 0.35, 75),
        (0.35, 0.50, 50),
        (0.50, 0.70, 25),
        (0.70, float("inf"), 0),
    ],
    "interest_coverage": [
        (8.0, float("inf"), 100),
        (5.0, 8.0, 75),
        (3.0, 5.0, 50),
        (1.5, 3.0, 25),
        (float("-inf"), 1.5, 0),
    ],
    "fixed_charge_coverage": [
        (6.0, float("inf"), 100),
        (4.0, 6.0, 75),
        (2.5, 4.0, 50),
        (1.5, 2.5, 25),
        (float("-inf"), 1.5, 0),
    ],
    "dscr": [
        (2.0, float("inf"), 100),
        (1.5, 2.0, 75),
        (1.2, 1.5, 50),
        (1.0, 1.2, 25),
        (float("-inf"), 1.0, 0),
    ],
    "ebitda_margin": [
        (0.25, float("inf"), 100),
        (0.15, 0.25, 75),
        (0.10, 0.15, 50),
        (0.05, 0.10, 25),
        (float("-inf"), 0.05, 0),
    ],
    "ebit_margin": [
        (0.15, float("inf"), 100),
        (0.10, 0.15, 75),
        (0.05, 0.10, 50),
        (0.0, 0.05, 25),
        (float("-inf"), 0.0, 0),
    ],
    "roa": [
        (0.12, float("inf"), 100),
        (0.08, 0.12, 75),
        (0.04, 0.08, 50),
        (0.0, 0.04, 25),
        (float("-inf"), 0.0, 0),
    ],
    "roe": [
        (0.20, float("inf"), 100),
        (0.12, 0.20, 75),
        (0.05, 0.12, 50),
        (0.0, 0.05, 25),
        (float("-inf"), 0.0, 0),
    ],
    "capex_dep": [
        (1.2, 1.8, 100),
        (0.9, 1.2, 75),
        (1.8, 2.5, 75),
        (0.7, 0.9, 50),
        (2.5, 3.5, 50),
        (0.5, 0.7, 25),
        (3.5, float("inf"), 25),
        (float("-inf"), 0.5, 0),
    ],
    "current_ratio": [
        (2.0, float("inf"), 100),
        (1.5, 2.0, 75),
        (1.0, 1.5, 50),
        (0.7, 1.0, 25),
        (float("-inf"), 0.7, 0),
    ],
    "rollover_coverage": [
        (2.0, float("inf"), 100),
        (1.2, 2.0, 75),
        (0.8, 1.2, 50),
        (0.5, 0.8, 25),
        (float("-inf"), 0.5, 0),
    ],
    "altman_z": [
        (3.0, float("inf"), 100),
        (2.7, 3.0, 75),
        (1.8, 2.7, 50),
        (1.5, 1.8, 25),
        (float("-inf"), 1.5, 0),
    ],
}

# Qualitative 1–5 scale → score
QUAL_SCORE_SCALE: Dict[int, float] = {
    5: 100.0,
    4: 75.0,
    3: 50.0,
    2: 25.0,
    1: 0.0,
}
