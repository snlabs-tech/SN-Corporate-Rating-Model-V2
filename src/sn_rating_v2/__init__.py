# SN Corporate Rating Model V2 package
"""
SN Corporate Rating Model V2 – package entrypoint.
"""

from .datamodel import QuantInputs, QualInputs, RatingOutputs
from .model import RatingModel

__all__ = [
    "QuantInputs",
    "QualInputs",
    "RatingOutputs",
    "RatingModel",
]
