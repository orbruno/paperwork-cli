"""Profile data loader.

Loads CV data from YAML or JSON files and validates against CVData schema.
"""

import json
from pathlib import Path

import yaml

from ..models.cv import CVData
from ..models.render_config import RenderConfig


class ProfileLoadError(Exception):
    pass


class JobLoadError(Exception):
    pass


def load_profile(path: Path) -> CVData:
    """Load and validate a profile from a YAML or JSON file.

    Args:
        path: Path to .yaml, .yml, or .json file.

    Returns:
        Validated CVData instance.

    Raises:
        ProfileLoadError: If file cannot be loaded or fails validation.
    """
    path = Path(path)
    if not path.exists():
        raise ProfileLoadError(f"Profile not found: {path}")

    try:
        with open(path) as f:
            if path.suffix in (".yaml", ".yml"):
                raw = yaml.safe_load(f)
            elif path.suffix == ".json":
                raw = json.load(f)
            else:
                raise ProfileLoadError(
                    f"Unsupported format: {path.suffix}. Use .yaml or .json"
                )
    except (yaml.YAMLError, json.JSONDecodeError) as e:
        raise ProfileLoadError(f"Failed to parse {path}: {e}") from e

    if not isinstance(raw, dict):
        raise ProfileLoadError(f"Expected a mapping at top level, got {type(raw).__name__}")

    try:
        return CVData(**raw)
    except Exception as e:
        raise ProfileLoadError(f"Profile validation failed: {e}") from e


def load_job(path: Path) -> tuple[CVData, RenderConfig]:
    """Load a job YAML — a file with a render: block + CVData fields at root.

    The render: key is extracted first; the remaining fields are validated
    as CVData. Missing render: block raises JobLoadError.

    Args:
        path: Path to .yaml or .yml job file.

    Returns:
        Tuple of (CVData, RenderConfig).

    Raises:
        JobLoadError: If file cannot be loaded, has no render: block, or fails validation.
    """
    path = Path(path)
    if not path.exists():
        raise JobLoadError(f"Job file not found: {path}")

    try:
        with open(path) as f:
            raw = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise JobLoadError(f"Failed to parse {path}: {e}") from e

    if not isinstance(raw, dict):
        raise JobLoadError(f"Expected a mapping at top level, got {type(raw).__name__}")

    if "render" not in raw:
        raise JobLoadError(
            "Job YAML must contain a 'render:' block with at least 'template' and 'output'."
        )

    render_raw = raw.pop("render")

    try:
        render_config = RenderConfig.model_validate(render_raw)
    except Exception as e:
        raise JobLoadError(f"render: block validation failed: {e}") from e

    # Fields not in CVData's schema are template-specific extras.
    # Lift them into extra: so users can write them flat at root level.
    known_fields = set(CVData.model_fields.keys())
    unknown = {k: v for k, v in raw.items() if k not in known_fields}
    if unknown:
        explicit_extra = raw.get("extra") or {}
        raw["extra"] = {**unknown, **explicit_extra}
        for k in unknown:
            del raw[k]

    try:
        cv_data = CVData(**raw)
    except Exception as e:
        raise JobLoadError(f"CV content validation failed: {e}") from e

    return cv_data, render_config
