"""Template-profile validation.

Validates that profile data satisfies a template's required_fields
contract. Supports dot-notation paths for nested field access
(e.g., "contact_info.email").
"""

from dataclasses import dataclass, field

from ..models.cv import CVData
from ..models.template_meta import TemplateMeta


@dataclass
class ValidationResult:
    """Result of validating profile data against a template."""

    is_valid: bool = True
    missing_required: list[str] = field(default_factory=list)
    missing_optional: list[str] = field(default_factory=list)
    present_required: list[str] = field(default_factory=list)
    present_optional: list[str] = field(default_factory=list)

    def format_errors(self) -> str:
        if not self.missing_required:
            return ""
        lines = ["Required fields missing from profile:"]
        for f in self.missing_required:
            lines.append(f"  - {f}")
        return "\n".join(lines)

    def format_report(self) -> str:
        lines = []
        if self.present_required:
            lines.append("Required (present):")
            for f in self.present_required:
                lines.append(f"  + {f}")
        if self.missing_required:
            lines.append("Required (MISSING):")
            for f in self.missing_required:
                lines.append(f"  ! {f}")
        if self.present_optional:
            lines.append("Optional (present):")
            for f in self.present_optional:
                lines.append(f"  + {f}")
        if self.missing_optional:
            lines.append("Optional (absent):")
            for f in self.missing_optional:
                lines.append(f"  - {f}")
        return "\n".join(lines)


def _resolve_field(data: dict, dotted_path: str) -> tuple[bool, object]:
    """Resolve a dot-notation path against a dict.

    Returns (found, value). A field is considered "present" if:
    - It exists and is not None
    - If it's a list, it has at least one element
    - If it's a string, it's not empty
    """
    parts = dotted_path.split(".")
    current = data
    for part in parts:
        if not isinstance(current, dict) or part not in current:
            return False, None
        current = current[part]

    if current is None:
        return False, None
    if isinstance(current, (list, str)) and len(current) == 0:
        return False, None
    return True, current


def validate_profile_for_template(
    cv_data: CVData,
    meta: TemplateMeta,
) -> ValidationResult:
    """Validate profile data against a template's field requirements."""
    data = cv_data.model_dump()
    result = ValidationResult()

    for field_path in meta.required_fields:
        found, _ = _resolve_field(data, field_path)
        if found:
            result.present_required.append(field_path)
        else:
            result.missing_required.append(field_path)
            result.is_valid = False

    for field_path in meta.optional_fields:
        found, _ = _resolve_field(data, field_path)
        if found:
            result.present_optional.append(field_path)
        else:
            result.missing_optional.append(field_path)

    return result
