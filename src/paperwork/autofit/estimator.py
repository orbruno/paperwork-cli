"""Generic line estimation for CV sections.

Measures any CVData field by inspecting its runtime type and applying
the appropriate formula. No hard-coded section names — uses data shape
and LayoutParams constants.
"""

from __future__ import annotations

import math
from typing import Any

from .models import LayoutParams, LineEstimate


def estimate_section(
    field_name: str,
    value: Any,
    params: LayoutParams,
    chars_per_line: int | None = None,
) -> LineEstimate:
    """Estimate lines for a single CVData field.

    Args:
        field_name: The CVData field name (e.g. "work_experience").
        value: The field value from cv_data dict.
        params: Layout parameters from the template.
        chars_per_line: Override chars_per_line (used during margin adjustment).

    Returns:
        LineEstimate with the calculated line count.
    """
    cpl = chars_per_line or params.chars_per_line

    if value is None or (isinstance(value, (list, str)) and len(value) == 0):
        return LineEstimate(field=field_name, lines=0, detail="empty")

    if isinstance(value, str):
        return _estimate_text(field_name, value, params, cpl)

    if isinstance(value, list) and len(value) > 0:
        first = value[0]

        if isinstance(first, dict) and "roles" in first:
            return _estimate_experience(field_name, value, params, cpl)

        if isinstance(first, dict) and "language" in first:
            return _estimate_inline_list(field_name, value, params)

        if isinstance(first, dict) and "skills" in first:
            return _estimate_competency_groups(field_name, value, params, cpl)

        if isinstance(first, dict):
            return _estimate_entry_list(field_name, value, params)

    return LineEstimate(field=field_name, lines=0, detail="unrecognized type")


def estimate_all(
    cv_dict: dict[str, Any],
    params: LayoutParams,
    chars_per_line: int | None = None,
) -> list[LineEstimate]:
    """Estimate lines for all sections in a CV data dict.

    Returns a list of LineEstimate objects plus a synthetic "header" entry.
    """
    estimates: list[LineEstimate] = [
        LineEstimate(
            field="header",
            lines=params.header_fixed_lines,
            detail="fixed",
        ),
    ]

    section_fields = [
        "profile",
        "competencies_and_skills",
        "work_experience",
        "education",
        "certifications",
        "languages",
    ]

    section_count = 0
    for field_name in section_fields:
        value = cv_dict.get(field_name)
        est = estimate_section(field_name, value, params, chars_per_line)
        if est.lines > 0:
            estimates.append(est)
            section_count += 1

    if section_count > 1:
        gap_lines = (section_count - 1) * params.section_gap_lines
        estimates.append(
            LineEstimate(field="section_gaps", lines=gap_lines, detail="inter-section")
        )

    return estimates


def total_lines(estimates: list[LineEstimate]) -> float:
    """Sum all line estimates."""
    return sum(e.lines for e in estimates)


def _estimate_text(
    field_name: str,
    text: str,
    params: LayoutParams,
    cpl: int,
) -> LineEstimate:
    """Text block: heading + wrapped lines."""
    text_lines = math.ceil(len(text) / cpl)
    total = params.section_heading_lines + text_lines
    return LineEstimate(
        field=field_name,
        lines=total,
        detail=f"{len(text)} chars -> {text_lines} text lines",
    )


def _estimate_experience(
    field_name: str,
    entries: list[dict[str, Any]],
    params: LayoutParams,
    cpl: int,
) -> LineEstimate:
    """Work experience: heading + per-entry header + bullet wrapping."""
    lines = params.section_heading_lines
    for entry in entries:
        lines += params.entry_header_lines
        for bullet in entry.get("roles", []):
            lines += math.ceil(len(bullet) / cpl)
    return LineEstimate(
        field=field_name,
        lines=lines,
        item_count=len(entries),
        detail=f"{len(entries)} entries",
    )


def _estimate_competency_groups(
    field_name: str,
    groups: list[dict[str, Any]],
    params: LayoutParams,
    cpl: int,
) -> LineEstimate:
    """Competency groups: heading + one line per group (label: skills joined)."""
    lines = params.section_heading_lines
    for group in groups:
        label = group.get("competency", "")
        skills = group.get("skills", [])
        text = f"{label}: {', '.join(skills)}"
        lines += math.ceil(len(text) / cpl)
    return LineEstimate(
        field=field_name,
        lines=lines,
        item_count=len(groups),
        detail=f"{len(groups)} groups",
    )


def _estimate_entry_list(
    field_name: str,
    entries: list[dict[str, Any]],
    params: LayoutParams,
) -> LineEstimate:
    """Simple entry list (education, certs): heading + entry_header per item."""
    lines = params.section_heading_lines + len(entries) * params.entry_header_lines
    return LineEstimate(
        field=field_name,
        lines=lines,
        item_count=len(entries),
        detail=f"{len(entries)} entries",
    )


def _estimate_inline_list(
    field_name: str,
    items: list[dict[str, Any]],
    params: LayoutParams,
) -> LineEstimate:
    """Inline list (languages): heading + 1 line for all items."""
    lines = params.section_heading_lines + 1
    return LineEstimate(
        field=field_name,
        lines=lines,
        item_count=len(items),
        detail=f"{len(items)} items inline",
    )
