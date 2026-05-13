"""Template manifest schema.

Every template directory must contain a `template.yaml` that conforms
to TemplateMeta. The required_fields and optional_fields lists define
the data contract: what the template NEEDS vs what it CAN render.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, model_validator


class TemplateMeta(BaseModel):
    name: str
    slug: str
    version: str
    description: Optional[str] = None
    author: Optional[str] = None

    # File references (relative to template directory)
    html_file: str = "cv.html"
    css_file: str = "cv.css"

    # Template capabilities
    page_size: str = "Letter"
    supports_photo: bool = True
    target_pages: int = 1        # number of pages this template is designed for (1 or 2)

    # Data contract -- dot notation for nested fields (e.g. "contact_info.email")
    # Rendering FAILS if required fields are missing or empty
    required_fields: list[str] = []
    # Template renders these if present, skips gracefully if absent
    optional_fields: list[str] = []

    # Optional SCSS source (informational, for developers)
    scss_file: Optional[str] = None

    # Detailed field spec for agents / CV composer (path relative to template dir)
    spec_file: Optional[str] = None

    # Auto-fit layout parameters (optional — only needed for --auto-fit)
    layout_params: Optional[dict[str, Any]] = None

    @model_validator(mode="before")
    @classmethod
    def _coerce_layout_params(cls, values: Any) -> Any:
        """Keep layout_params as a raw dict; LayoutParams is built lazily."""
        return values

    def get_layout_params(self) -> "LayoutParams":
        """Parse layout_params dict into a LayoutParams dataclass.

        Raises ValueError if layout_params is not defined.
        """
        from ..autofit.models import LayoutParams

        if self.layout_params is None:
            raise ValueError(
                f"Template '{self.slug}' has no layout_params defined. "
                "Auto-fit requires layout_params in template.yaml."
            )
        return LayoutParams.from_dict(dict(self.layout_params))
