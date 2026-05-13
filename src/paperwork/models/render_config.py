"""Render configuration model — the render: block in a job YAML."""

from typing import Any
from pydantic import BaseModel, model_validator


class RenderConfig(BaseModel):
    template: str
    output: str
    layout_overrides: dict[str, Any] = {}
    auto_fit: bool = False
    target_pages: int = 1
    fit_report: bool = False

    @model_validator(mode="before")
    @classmethod
    def _coerce_overrides(cls, values: Any) -> Any:
        """Ensure all layout_overrides values are strings for CSS injection."""
        overrides = values.get("layout_overrides", {})
        if isinstance(overrides, dict):
            values["layout_overrides"] = {k: str(v) for k, v in overrides.items()}
        return values
