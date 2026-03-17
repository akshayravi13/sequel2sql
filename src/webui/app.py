from __future__ import annotations

from pathlib import Path
from typing import Any

from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
ASSETS_DIR = PROJECT_ROOT / "assets"


def create_branded_web_app(
    *,
    agent: Any,
    deps: Any,
    models: dict[str, Any],
) -> Starlette:
    """Create a branded chat app that keeps Pydantic routes at root."""
    chat_root_app = agent.to_web(
        deps=deps,
        models=models,
        html_source=str(TEMPLATES_DIR / "home.html"),
    )

    routes = [
        Mount("/assets", app=StaticFiles(directory=str(ASSETS_DIR))),
        Mount("/", app=chat_root_app),
    ]

    return Starlette(routes=routes)
