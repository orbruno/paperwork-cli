"""FastAPI application factory.

Wraps the RenderEngine for HTTP access. Used by Docker/n8n.
"""

import os
from pathlib import Path

from fastapi import FastAPI

from .routes import create_router
from ..engine.renderer import RenderEngine


def create_app() -> FastAPI:
    templates_dir = Path(
        os.environ.get("RENDERCV_TEMPLATES_DIR", "/app/templates")
    )
    profiles_dir = Path(
        os.environ.get("RENDERCV_PROFILES_DIR", "/app/profiles")
    )

    engine = RenderEngine(templates_dir)
    app = FastAPI(title="RenderCV", version="0.2.0")
    app.include_router(create_router(engine, profiles_dir))
    return app


app = create_app()
