"""Two-phase auto-fit optimizer.

Phase 1: Reduce page margins (gentlest — always runs first).
Phase 2: Apply template-driven trim rules to content (only if needed).

All mutations produce new dicts — no in-place modification.
"""

from __future__ import annotations

import copy
import math
from typing import Any

from .css_override import margin_override
from .estimator import estimate_all, total_lines
from .models import (
    FitConfig,
    FitReport,
    FitResult,
    LayoutParams,
    TrimRule,
    TrimStrategy,
)


def optimize(cv_dict: dict[str, Any], config: FitConfig) -> FitResult:
    """Run the full auto-fit pipeline: margins first, then content trimming.

    Args:
        cv_dict: CVData serialized via model_dump().
        config: Target pages and layout parameters.

    Returns:
        FitResult with trimmed CV dict, CSS overrides, and diagnostic report.
    """
    params = config.layout
    target_lines = params.available_lines(params.margin_max_mm) * config.target_pages

    original_estimates = estimate_all(cv_dict, params)
    original_total = total_lines(original_estimates)

    actions: list[str] = []
    css_overrides: list[str] = []
    current_margin = params.margin_max_mm
    current_cv = cv_dict

    # Phase 1 — Margin reduction
    current_margin, target_lines, margin_actions, margin_css = _phase_margins(
        current_cv, params, config.target_pages,
    )
    actions.extend(margin_actions)
    css_overrides.extend(margin_css)

    cpl = params.chars_for_margin(current_margin)
    current_estimates = estimate_all(current_cv, params, cpl)
    current_total = total_lines(current_estimates)

    # Phase 2 — Content trimming (only if Phase 1 was not enough)
    if current_total > target_lines and params.trim_rules:
        current_cv, trim_actions = _phase_trim(
            current_cv, params, target_lines, cpl,
        )
        actions.extend(trim_actions)
        current_estimates = estimate_all(current_cv, params, cpl)
        current_total = total_lines(current_estimates)

    report = FitReport(
        target_lines=target_lines,
        original_lines=original_total,
        final_lines=current_total,
        final_margin_mm=current_margin,
        fits=current_total <= target_lines,
        actions=actions,
    )

    return FitResult(
        trimmed_cv=current_cv,
        css_overrides=css_overrides,
        report=report,
    )


def _phase_margins(
    cv_dict: dict[str, Any],
    params: LayoutParams,
    target_pages: int,
) -> tuple[float, float, list[str], list[str]]:
    """Phase 1: Step margins down until content fits or margin_min reached.

    Returns (final_margin, target_lines, actions, css_overrides).
    """
    margin = params.margin_max_mm
    start_margin = margin

    while margin > params.margin_min_mm:
        target_lines = params.available_lines(margin) * target_pages
        cpl = params.chars_for_margin(margin)
        estimates = estimate_all(cv_dict, params, cpl)
        current = total_lines(estimates)

        if current <= target_lines:
            break

        margin = max(margin - params.margin_step_mm, params.margin_min_mm)

    target_lines = params.available_lines(margin) * target_pages
    actions: list[str] = []
    css_overrides: list[str] = []

    if margin < start_margin:
        gained = params.available_lines(margin) - params.available_lines(start_margin)
        actions.append(
            f"Margins: {start_margin:.0f}mm -> {margin:.0f}mm"
            f" (+{gained * target_pages:.1f} lines)"
        )
        css_overrides.append(margin_override(margin))

    return margin, target_lines, actions, css_overrides


def _phase_trim(
    cv_dict: dict[str, Any],
    params: LayoutParams,
    target_lines: float,
    cpl: int,
) -> tuple[dict[str, Any], list[str]]:
    """Phase 2: Apply trim rules in priority order until content fits.

    Returns (trimmed_cv_dict, actions).
    """
    current = copy.deepcopy(cv_dict)
    actions: list[str] = []

    can_trim = True
    while can_trim:
        estimates = estimate_all(current, params, cpl)
        if total_lines(estimates) <= target_lines:
            break

        can_trim = False
        for rule in params.trim_rules:
            value = current.get(rule.field)
            if value is None:
                continue

            trimmed, action = _apply_trim(rule, value, cpl)
            if trimmed is not value and action:
                current = {**current, rule.field: trimmed}
                actions.append(action)
                can_trim = True

                estimates = estimate_all(current, params, cpl)
                if total_lines(estimates) <= target_lines:
                    break

    return current, actions


def _apply_trim(
    rule: TrimRule,
    value: Any,
    cpl: int,
) -> tuple[Any, str]:
    """Apply a single trim step. Returns (new_value, action_description).

    Returns the original value unchanged if no trimming is possible.
    """
    if rule.strategy == TrimStrategy.NONE:
        return value, ""

    if rule.strategy == TrimStrategy.REMOVE_ITEMS_FROM_END:
        return _trim_remove_items(rule, value)

    if rule.strategy == TrimStrategy.REMOVE_BULLETS_THEN_ENTRIES:
        return _trim_bullets_then_entries(rule, value)

    if rule.strategy == TrimStrategy.TRUNCATE_WORDS:
        return _trim_truncate_words(rule, value, cpl)

    return value, ""


def _trim_remove_items(
    rule: TrimRule,
    items: list[Any],
) -> tuple[list[Any], str]:
    """Remove the last item from a list if above min_items."""
    if not isinstance(items, list) or len(items) <= rule.min_items:
        return items, ""

    new_items = items[:-1]
    return new_items, f"{rule.field}: {len(items)} -> {len(new_items)} items"


def _trim_bullets_then_entries(
    rule: TrimRule,
    entries: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], str]:
    """First reduce max bullets per entry, then remove entries.

    Strategy: find the entry with the most bullets and remove one.
    If all entries are at min_bullets, remove the last entry instead.
    """
    if not isinstance(entries, list) or len(entries) == 0:
        return entries, ""

    max_bullets = max(len(e.get("roles", [])) for e in entries)

    if max_bullets > rule.min_bullets:
        new_entries = []
        for entry in entries:
            roles = entry.get("roles", [])
            if len(roles) >= max_bullets and len(roles) > rule.min_bullets:
                new_entry = {**entry, "roles": roles[:-1]}
                new_entries.append(new_entry)
            else:
                new_entries.append(entry)
        return (
            new_entries,
            f"{rule.field}: max bullets {max_bullets} -> {max_bullets - 1}",
        )

    if len(entries) > rule.min_items:
        new_entries = entries[:-1]
        return new_entries, f"{rule.field}: {len(entries)} -> {len(new_entries)} entries"

    return entries, ""


def _trim_truncate_words(
    rule: TrimRule,
    text: Any,
    cpl: int,
) -> tuple[Any, str]:
    """Truncate text to fewer words."""
    if not isinstance(text, str):
        return text, ""

    words = text.split()
    if len(words) <= rule.min_words:
        return text, ""

    target = max(rule.min_words, len(words) - 10)
    if target >= len(words):
        return text, ""

    truncated = " ".join(words[:target]) + "..."
    return truncated, f"{rule.field}: {len(words)} -> {target} words"
