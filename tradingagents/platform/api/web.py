"""Opt-in, loopback-only built UI serving. No repository or SPA catch-all mount."""

from pathlib import Path

from fastapi import FastAPI
from starlette.exceptions import HTTPException
from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles

CSP = (
    "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; "
    "font-src 'self'; connect-src 'self'; base-uri 'none'; object-src 'none'; "
    "frame-ancestors 'none'; form-action 'self'"
)


class BuildAssets(StaticFiles):
    async def get_response(self, path, scope):
        # No source maps, dotfiles, source TSX, manifests, or arbitrary data files.
        if (any(part.startswith(".") for part in Path(path).parts)
                or Path(path).suffix.lower() not in {
                    ".js", ".css", ".woff", ".woff2", ".svg", ".png", ".jpg", ".webp", ".ico",
                }):
            raise HTTPException(status_code=404)
        return await super().get_response(path, scope)


def mount_built_web(app: FastAPI, directory: Path) -> None:
    root = directory.resolve(strict=True)
    index = root / "index.html"
    assets = root / "assets"
    if (not index.is_file() or index.is_symlink() or not assets.is_dir()
            or assets.is_symlink()):
        raise ValueError("web root must contain built index.html and an assets directory")

    @app.api_route("/", methods=["GET", "HEAD"], include_in_schema=False)
    @app.api_route("/index.html", methods=["GET", "HEAD"], include_in_schema=False)
    async def web_index():
        return FileResponse(index, media_type="text/html")

    # StaticFiles resolves paths and confines files to this assets directory.
    app.mount("/assets", BuildAssets(directory=assets, follow_symlink=False), name="web-assets")
