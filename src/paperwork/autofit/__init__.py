"""Auto-fit system for RenderCV.

Public API:
    estimate_lines() — measure how many lines a CV occupies
    optimize()       — fit content to target page count
"""

from .estimator import estimate_all, total_lines
from .models import FitConfig, FitResult, LayoutParams, TrimRule
from .optimizer import optimize

__all__ = [
    "estimate_all",
    "total_lines",
    "optimize",
    "FitConfig",
    "FitResult",
    "LayoutParams",
    "TrimRule",
]
