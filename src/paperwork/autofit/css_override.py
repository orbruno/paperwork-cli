"""Generate CSS override strings for page margin adjustment."""


def margin_override(margin_mm: float) -> str:
    """Return a CSS @page rule that sets all margins to the given value."""
    return f"@page {{ margin: {margin_mm:.1f}mm; }}"
