"""Custom Jinja2 filters for CV templates."""

from urllib.parse import urlparse

from jinja2 import Environment


def base_url_filter(url: str) -> str:
    """Extract clean display URL without query params or UTM tracking."""
    parsed = urlparse(url)
    if parsed.scheme:
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")
    return (
        f"{parsed.netloc}{parsed.path}" if parsed.netloc else parsed.path.split("?")[0]
    ).rstrip("/")


def register_filters(env: Environment) -> None:
    """Register all custom filters on a Jinja2 environment."""
    env.filters["base_url"] = base_url_filter
