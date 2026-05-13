FROM python:3.11-slim

WORKDIR /app

# System dependencies for WeasyPrint
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-xlib-2.0-0 \
    libffi-dev \
    shared-mime-info \
    gir1.2-pango-1.0 \
    python3-gi \
    python3-cffi \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install the package with API dependencies
COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN uv pip install --system --no-cache ".[api]"

# Templates and profiles are mounted at runtime via Docker volumes
# Default paths (overridable via env vars)
ENV RENDERCV_TEMPLATES_DIR=/app/templates
ENV RENDERCV_PROFILES_DIR=/app/profiles

EXPOSE 8000

CMD ["uvicorn", "paperwork.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
