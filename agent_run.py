"""MAF + Copilot SDK. Token/keys come from App Settings only."""

from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCTRINE = "\n\n".join(
    (ROOT / p).read_text(encoding="utf-8")
    for p in ("doctrine/dalio.md", "doctrine/eli5.md", "skills/eli5/SKILL.md")
    if (ROOT / p).is_file()
)
SKILLS_DIR = str(ROOT / "skills")


def _compact_board(board: dict) -> dict:
    cards = []
    for c in board.get("cards") or []:
        m = c.get("metrics") or {}
        cards.append(
            {
                "id": c.get("id"),
                "name": c.get("name"),
                "role": c.get("role"),
                "real_rate": (m.get("real_rate") or {}).get("value"),
                "real_year": (m.get("real_rate") or {}).get("year"),
                "inflation": (m.get("inflation") or {}).get("value"),
                "gdp_growth": (m.get("gdp_growth") or {}).get("value"),
                "gov_debt": (m.get("gov_debt") or {}).get("value"),
                "policy_rate": (m.get("policy_rate") or {}).get("value"),
                "policy_period": (m.get("policy_rate") or {}).get("year"),
                "sides": c.get("sides"),
                "playbook": c.get("playbook"),
            }
        )
    mk = board.get("market") or {}
    return {
        "cards": cards,
        "us_10y": (mk.get("us_10y") or {}).get("price"),
        "us_3m": (mk.get("us_3m") or {}).get("price"),
        "note": board.get("vintage_note"),
    }


def _azure_provider() -> dict | None:
    key = os.environ.get("AZURE_OPENAI_API_KEY") or os.environ.get("AZURE_OPENAI_KEY")
    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
    if not key or not endpoint:
        return None
    host = endpoint.split("://", 1)[-1].rstrip("/").split("/", 1)[0]
    return {"type": "azure", "base_url": host, "api_key": key}


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "fetch_macro",
            "description": "공개 거시 한 시리즈. country는 KR/US/한국, indicator는 real_rate|policy_rate|inflation|gdp_growth|gov_debt.",
            "parameters": {
                "type": "object",
                "properties": {
                    "country": {"type": "string"},
                    "indicator": {"type": "string"},
                },
                "required": ["country", "indicator"],
            },
        },
    }
]


def _azure_post(messages: list, stream: bool = False) -> dict:
    import urllib.request

    key = os.environ.get("AZURE_OPENAI_API_KEY") or os.environ.get("AZURE_OPENAI_KEY")
    endpoint = (os.environ.get("AZURE_OPENAI_ENDPOINT") or "").rstrip("/")
    dep = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-5-mini")
    ver = os.environ.get("AZURE_OPENAI_API_VERSION", "2025-04-01-preview")
    if not key or not endpoint:
        raise RuntimeError("azure not configured")
    url = f"{endpoint}/openai/deployments/{dep}/chat/completions?api-version={ver}"
    payload = {
        "messages": messages,
        "max_completion_tokens": 4000,
        "tools": TOOLS,
        "stream": stream,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "api-key": key},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=55) as res:
        return json.loads(res.read().decode("utf-8"))


def _azure_chat(message: str, instructions: str) -> str:
    from board import fetch_macro

    messages = [
        {"role": "system", "content": instructions},
        {"role": "user", "content": message},
    ]
    for _ in range(4):
        payload = _azure_post(messages, stream=False)
        choice = (payload.get("choices") or [{}])[0]
        msg = choice.get("message") or {}
        calls = msg.get("tool_calls") or []
        if calls:
            messages.append(msg)
            for call in calls:
                fn = (call.get("function") or {})
                args = json.loads(fn.get("arguments") or "{}")
                out = fetch_macro(str(args.get("country") or ""), str(args.get("indicator") or "real_rate"))
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.get("id"),
                        "content": out,
                    }
                )
            continue
        text = (msg.get("content") or "").strip()
        if not text:
            raise RuntimeError("empty azure content")
        return text
    raise RuntimeError("tool loop exceeded")


def _maf_worker(message: str, instructions: str) -> str:
    """MAF+Copilot SDK를 전용 스레드·전용 루프에서 돌린다.
    SDK의 CLI 런타임 다운로드/스폰이 동기라 메인 루프를 막으면 gunicorn이 워커를 죽인다(502 실측)."""
    import asyncio

    from agent_framework.github import GitHubCopilotAgent

    from board import fetch_macro

    provider = _azure_provider()
    options: dict = {
        "model": os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-5-mini"),
        "skill_directories": [SKILLS_DIR],
    }
    if provider:
        options["provider"] = provider

    async def _go() -> str:
        agent = GitHubCopilotAgent(
            instructions=instructions,
            default_options=options,
            tools=[fetch_macro],
        )
        async with agent:
            result = await agent.run(message)
        return (getattr(result, "text", None) or str(result) or "").strip()

    return asyncio.run(_go())


async def run_agent(message: str, board: dict) -> tuple[str, str]:
    import asyncio

    board_json = json.dumps(_compact_board(board), ensure_ascii=False)
    import datetime

    today = datetime.date.today().isoformat()
    instructions = (
        DOCTRINE
        + f"\n\n오늘은 {today}다. 아래 JSON 지표의 연도/기간이 오늘보다 오래됐으면 그 격차를 밝히고, 격차가 크면 판정을 조건부로 낮춰라. 아래 JSON만 숫자 근거로 써라. 없는 값을 만들지 마라.\n"
        + board_json
    )
    model = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-5-mini")
    # MAF는 CLI 자식을 띄우다 50초를 다 먹으면 프론트 65초와 겹쳐 사용자에게 타임아웃만 보인다.
    # CLI 런타임이 이미 있을 때만 짧게 시도한다. TRY_MAF=1 이면 강제.
    cli_root = Path(os.environ.get("COPILOT_CLI_EXTRACT_DIR", "/home/copilot-cli"))
    cli_ok = any(
        (cli_root / p).exists()
        for p in ("copilot", "bin/copilot", "copilot-linux", "bin/copilot-linux")
    )
    try_maf = os.environ.get("TRY_MAF") == "1" or cli_ok
    if try_maf:
        try:
            text = await asyncio.wait_for(
                asyncio.to_thread(_maf_worker, message, instructions), timeout=8
            )
            if text:
                return text, f"GitHubCopilotAgent:{model}"
        except Exception:
            pass
    reply = await asyncio.to_thread(_azure_chat, message, instructions)
    return reply, model + "+tools"
