"""personality-template API routes — the Personality gallery (left-pane iframe).

Mounted at /api/p/personality-template/* by the loader via manifest.routes_module.
Serves the read-only catalog (+ avatars) and the static gallery UI. Applying a
personality is done by the UI calling core's own `PUT /api/p/plugin-identity/`
endpoint from the browser — this plugin never writes core identity itself.
Decoupled to `luna_sdk` — no `import luna.*`.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, Response

from .catalog import (
    ALLOWED_VALUES,
    DEFAULT_EMOJI,
    DEFAULT_PERSONALITY,
    load_catalog,
)

_UI_DIR = Path(__file__).parent / "ui"


def register_routes(app, ctx):
    from luna_sdk import get_current_user

    catalog = load_catalog()
    router = APIRouter(prefix="/api/p/personality-template", tags=["personality"])

    @router.get("/catalog")
    async def get_catalog(user=Depends(get_current_user)):
        return {
            "personalities": catalog.cards(),
            "allowed_values": {k: list(v) for k, v in ALLOWED_VALUES.items()},
            "default": {**DEFAULT_PERSONALITY, "emoji": DEFAULT_EMOJI},
        }

    # --- Sidebar pane UI (served as a full-pane iframe by the host) ---

    @router.get("/ui/")
    async def serve_ui_root():
        index = _UI_DIR / "index.html"
        if index.exists():
            return FileResponse(str(index), headers={"Cache-Control": "no-cache"})
        return Response(
            content="<h1>personality-template UI not built</h1>",
            media_type="text/html",
        )

    @router.get("/ui/{path:path}")
    async def serve_ui(path: str):
        if not path or path == "/":
            path = "index.html"
        target = (_UI_DIR / path).resolve()
        if not str(target).startswith(str(_UI_DIR.resolve())):
            raise HTTPException(403, "Forbidden")
        if not target.exists() or target.is_dir():
            index = _UI_DIR / "index.html"
            if index.exists():
                return FileResponse(str(index), headers={"Cache-Control": "no-cache"})
            raise HTTPException(404, "Not found")
        return FileResponse(str(target), headers={"Cache-Control": "no-cache"})

    app.include_router(router)
