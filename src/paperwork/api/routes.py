"""API routes.

Provides backward-compatible /render-cv endpoint plus new endpoints
for template selection, profile-based rendering, and template listing.
"""

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from ..models.cv import CVData
from ..engine.renderer import RenderEngine, ValidationError
from ..templates.registry import TemplateNotFoundError
from ..profiles.loader import load_profile, ProfileLoadError


def create_router(engine: RenderEngine, profiles_dir: Path) -> APIRouter:
    router = APIRouter()

    @router.get("/")
    def health():
        return {
            "status": "ok",
            "templates": len(engine.registry.list_templates()),
        }

    @router.get("/templates")
    def list_templates():
        return [t.model_dump() for t in engine.registry.list_templates()]

    @router.post("/render")
    def render(
        cv: CVData,
        template: str = Query(default="classic", description="Template slug"),
    ):
        """Render CV data to PDF. Data provided in request body."""
        try:
            pdf = engine.render_pdf(cv, template)
            return Response(content=pdf, media_type="application/pdf")
        except TemplateNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except ValidationError as e:
            raise HTTPException(status_code=422, detail=str(e))

    @router.post("/render-cv")
    def render_cv_legacy(cv: CVData):
        """Legacy endpoint for backward compatibility with existing n8n workflows."""
        try:
            pdf = engine.render_pdf(cv, "classic")
            return Response(content=pdf, media_type="application/pdf")
        except TemplateNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except ValidationError as e:
            raise HTTPException(status_code=422, detail=str(e))

    @router.get("/render/{profile_slug}")
    def render_from_profile(
        profile_slug: str,
        template: str = Query(default="classic"),
    ):
        """Render a stored profile to PDF."""
        profile_path = profiles_dir / f"{profile_slug}.yaml"
        if not profile_path.exists():
            raise HTTPException(
                status_code=404, detail=f"Profile not found: {profile_slug}"
            )
        try:
            cv_data = load_profile(profile_path)
            pdf = engine.render_pdf(cv_data, template)
            return Response(content=pdf, media_type="application/pdf")
        except ProfileLoadError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except TemplateNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except ValidationError as e:
            raise HTTPException(status_code=422, detail=str(e))

    return router
