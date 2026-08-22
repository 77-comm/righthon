"""Perp_Machine — FastAPI. Board first. Agent next."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from board import build_board

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
        "board": True,
    }


@app.get("/api/board")
def api_board() -> dict:
    return build_board()


@app.post("/api/chat")
def api_chat(payload: dict) -> JSONResponse:
    message = payload.get("message") if isinstance(payload, dict) else None
    if not isinstance(message, str) or not message.strip():
        return JSONResponse({"error": "message 필드가 필요합니다"}, status_code=400)
    board = build_board()
    cards = board.get("cards") or []
    hit = next((c for c in cards if c["name"] in message or c["id"] in message.upper()), None)
    if hit is None:
        hit = next((c for c in cards if c["id"] == "KR"), cards[0] if cards else None)
    if not hit:
        return JSONResponse({"reply": "계기판이 비어 있습니다. 잠시 후 다시 열어 주세요."})
    s = hit["sides"]
    rr = hit["metrics"]["real_rate"]
    reply = (
        f"{hit['name']} 실질금리 {rr['value'] if rr['value'] is not None else 'n/a'}"
        f"% ({rr['year'] or '?'} · WB {rr['code']}).\n\n"
        f"채권자: {s['creditor']}\n채무자: {s['debtor']}\n\n"
        "에이전트(MAF)는 다음 슬라이스. 지금은 같은 숫자로 양면만 닫는다. 매매 아님."
    )
    return JSONResponse({"reply": reply, "agent": "rule"})


@app.get("/")
def index() -> FileResponse:
    return FileResponse(PUBLIC / "index.html")


if PUBLIC.is_dir():
    app.mount("/static", StaticFiles(directory=PUBLIC), name="static")
