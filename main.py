"""Perp_Machine — FastAPI. First slice: static + /healthz. Agent comes next."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / "public"

app = FastAPI(title="Perp_Machine", docs_url=None, redoc_url=None)


@app.get("/healthz")
def healthz() -> dict:
    configured = bool(
        os.environ.get("AZURE_OPENAI_API_KEY") or os.environ.get("AZURE_OPENAI_KEY")
    )
    return {
        "ok": True,
        "runtime": "python",
        "agent": "pending",
        "configured": configured,
    }


@app.get("/")
def index() -> FileResponse:
    return FileResponse(PUBLIC / "index.html")


if PUBLIC.is_dir():
    app.mount("/static", StaticFiles(directory=PUBLIC), name="static")
