"""Perp_Machine — FastAPI. Board first. Agent next."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent

# MAF+Copilot SDK는 Oryx pip가 아니라 zip에 동봉된다 (sdk==1.0.2 핀이 PyPI에서 소멸).
_PKG = ROOT / "packages"
if _PKG.is_dir() and str(_PKG) not in sys.path:
    sys.path.insert(0, str(_PKG))

from agent_run import cli_ready, maf_importable, maf_status, run_agent, warmup_linux_cli
from board import build_board

PUBLIC = ROOT / "public"

app = FastAPI(title="Perp_Machine", docs_url=None, redoc_url=None)


@app.on_event("startup")
def _warmup() -> None:
    import threading

    threading.Thread(target=warmup_linux_cli, name="copilot-cli-warmup", daemon=True).start()


@app.get("/healthz")
def healthz() -> dict:
    configured = bool(
        os.environ.get("AZURE_OPENAI_API_KEY") or os.environ.get("AZURE_OPENAI_KEY")
    )
    maf = maf_importable()
    cli = cli_ready()
    return {
        "ok": True,
        "runtime": "python",
        "agent": "GitHubCopilotAgent" if (maf and cli) else ("starting" if configured else "pending"),
        "configured": configured,
        "board": True,
    }


@app.get("/api/board")
def api_board() -> dict:
    return build_board()


def _rule_reply(message: str, board: dict) -> str:
    cards = board.get("cards") or []
    hit = next((c for c in cards if c["name"] in message or c["id"] in message.upper()), None)
    if hit is None:
        hit = next((c for c in cards if c["id"] == "KR"), cards[0] if cards else None)
    if not hit:
        return "계기판이 비어 있습니다."
    s = hit["sides"]
    rr = hit["metrics"]["real_rate"]
    return (
        f"{hit['name']} 실질금리 {rr['value'] if rr['value'] is not None else 'n/a'}"
        f"% ({rr['year'] or '?'} · WB {rr['code']}).\n\n"
        f"채권자: {s['creditor']}\n채무자: {s['debtor']}\n\n"
        "모델 호출이 실패해 규칙 초안으로 닫았다. 매매 아님."
    )


@app.post("/api/chat")
async def api_chat(request: Request) -> JSONResponse:
    body = await request.body()
    if len(body) > 1_000_000:
        return JSONResponse({"error": "본문이 1MB를 넘습니다"}, status_code=413)
    try:
        payload = json.loads(body)
    except Exception:
        return JSONResponse({"error": "JSON 본문이 필요합니다"}, status_code=400)
    message = payload.get("message") if isinstance(payload, dict) else None
    if not isinstance(message, str) or not message.strip():
        return JSONResponse({"error": "message 필드가 필요합니다"}, status_code=400)
    board = build_board()
    try:
        reply, model = await run_agent(message.strip(), board)
        return JSONResponse({"reply": reply, "agent": model, "model": model})
    except TimeoutError:
        return JSONResponse({"error": "업스트림 응답 지연"}, status_code=504)
    except Exception as exc:
        print(f"[chat] agent fail -> rule: {type(exc).__name__}", flush=True)
        return JSONResponse({"reply": _rule_reply(message, board), "agent": "rule"})


@app.get("/")
def index() -> FileResponse:
    return FileResponse(PUBLIC / "index.html")


if PUBLIC.is_dir():
    app.mount("/static", StaticFiles(directory=PUBLIC), name="static")
