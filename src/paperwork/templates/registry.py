"""Template registry -- discovers and loads template packs.

Templates are directories containing:
  - template.yaml (manifest)
  - An HTML file (Jinja2 template)
  - A CSS file (stylesheet)
  - Optional assets/ directory
"""

from pathlib import Path

import yaml

from ..models.template_meta import TemplateMeta


class TemplateNotFoundError(Exception):
    pass


class TemplateRegistry:
    def __init__(self, templates_dir: Path):
        self._templates_dir = Path(templates_dir)
        self._templates: dict[str, TemplateMeta] = {}
        self._scan()

    def _scan(self) -> None:
        """Discover all template packs in the templates directory."""
        if not self._templates_dir.exists():
            return
        for entry in sorted(self._templates_dir.iterdir()):
            if entry.name.startswith("_"):
                continue
            manifest_path = entry / "template.yaml"
            if entry.is_dir() and manifest_path.exists():
                with open(manifest_path) as f:
                    raw = yaml.safe_load(f)
                meta = TemplateMeta(**raw)
                self._templates[meta.slug] = meta

    def list_templates(self) -> list[TemplateMeta]:
        return list(self._templates.values())

    def get_template(self, slug: str) -> TemplateMeta:
        if slug not in self._templates:
            available = ", ".join(sorted(self._templates.keys())) or "(none)"
            raise TemplateNotFoundError(
                f"Template '{slug}' not found. Available: {available}"
            )
        return self._templates[slug]

    def get_template_dir(self, slug: str) -> Path:
        self.get_template(slug)  # Validates existence
        return self._templates_dir / slug
