"""Data models for the auto-fit system.

Defines layout parameters, trim rules, and result types used
by the estimator and optimizer modules.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TrimStrategy(str, Enum):
    """How a section should be trimmed to save space."""

    REMOVE_ITEMS_FROM_END = "remove_items_from_end"
    REMOVE_BULLETS_THEN_ENTRIES = "remove_bullets_then_entries"
    TRUNCATE_WORDS = "truncate_words"
    NONE = "none"


@dataclass(frozen=True)
class TrimRule:
    """A single trim instruction read from template.yaml."""

    field: str
    strategy: TrimStrategy
    min_items: int = 0
    min_words: int = 0
    min_bullets: int = 0

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> TrimRule:
        return cls(
            field=raw["field"],
            strategy=TrimStrategy(raw["strategy"]),
            min_items=raw.get("min_items", 0),
            min_words=raw.get("min_words", 0),
            min_bullets=raw.get("min_bullets", 0),
        )


@dataclass(frozen=True)
class LayoutParams:
    """Page geometry and typography constants for a template."""

    page_width_mm: float = 210
    page_height_mm: float = 297
    margin_min_mm: float = 12
    margin_max_mm: float = 25
    margin_step_mm: float = 1
    font_size_px: float = 10
    line_height: float = 1.35
    chars_per_line: int = 95
    header_fixed_lines: float = 5
    section_heading_lines: float = 2
    entry_header_lines: float = 2
    section_gap_lines: float = 0.75
    safety_margin: float = 0.95

    trim_rules: tuple[TrimRule, ...] = ()

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> LayoutParams:
        rules_raw = raw.pop("trim_rules", [])
        rules = tuple(TrimRule.from_dict(r) for r in rules_raw)
        return cls(**raw, trim_rules=rules)

    def available_lines(self, margin_mm: float) -> float:
        """Total printable lines given a margin value."""
        printable_height_mm = self.page_height_mm - 2 * margin_mm
        line_height_mm = self.font_size_px * self.line_height * 25.4 / 72
        return (printable_height_mm / line_height_mm) * self.safety_margin

    def chars_for_margin(self, margin_mm: float) -> int:
        """Recalculate chars_per_line for a given margin."""
        default_printable = self.page_width_mm - 2 * self.margin_max_mm
        new_printable = self.page_width_mm - 2 * margin_mm
        ratio = new_printable / default_printable if default_printable > 0 else 1
        return max(1, math.floor(self.chars_per_line * ratio))


@dataclass(frozen=True)
class FitConfig:
    """Runtime configuration for an auto-fit run."""

    target_pages: int = 1
    layout: LayoutParams = field(default_factory=LayoutParams)


@dataclass
class LineEstimate:
    """Estimated line count for a single section."""

    field: str
    lines: float
    item_count: int = 0
    detail: str = ""


@dataclass
class FitReport:
    """Human-readable log of what the optimizer did."""

    target_lines: float
    original_lines: float
    final_lines: float
    final_margin_mm: float
    fits: bool
    actions: list[str] = field(default_factory=list)

    def format(self) -> str:
        status = "FITS" if self.fits else "OVERFLOW"
        lines = [
            "Auto-fit Report",
            f"  Target: {self.target_lines:.0f} lines"
            f" | Original: {self.original_lines:.1f}"
            f" | Final: {self.final_lines:.1f}",
            f"  Margin: {self.final_margin_mm:.0f}mm",
            f"  Status: {status}",
        ]
        if self.actions:
            lines.append("  Actions:")
            for action in self.actions:
                lines.append(f"    - {action}")
        return "\n".join(lines)


@dataclass
class FitResult:
    """Output of the optimizer: trimmed data + CSS + diagnostics."""

    trimmed_cv: dict[str, Any]
    css_overrides: list[str]
    report: FitReport
