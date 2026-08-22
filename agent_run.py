"""MAF + Copilot SDK. Token/keys come from App Settings only."""

from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCTRINE = (ROOT / "doctrine" / "dalio.md").read_text(encoding="utf-8")


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


async def run_agent(message: str, board: dict) -> tuple[str, str]:
    board_json = json.dumps(_compact_board(board), ensure_ascii=False)
    instructions = (
        DOCTRINE
        + "\n\n아래 JSON만 숫자 근거로 써라. 없는 값을 만들지 마라.\n"
        + board_json
    )
    try:
        from agent_framework.github import GitHubCopilotAgent

        provider = _azure_provider()
        options: dict = {
            "model": os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-5-mini"),
        }
        if provider:
            options["provider"] = provider
        agent = GitHubCopilotAgent(
            instructions=instructions,
            default_options=options,
            tools=[__import__("board", fromlist=["fetch_macro"]).fetch_macro],
        )
        # CLI 런타임 첫 기동이 길어지면 폴백으로 넘어가게 상한을 건다.
        import asyncio

        async with agent:
            result = await asyncio.wait_for(agent.run(message), timeout=50)
        text = (getattr(result, "text", None) or str(result) or "").strip()
        if not text:
            raise RuntimeError("empty agent content")
        return text, f"GitHubCopilotAgent:{options['model']}"
    except Exception:
        return _azure_chat(message, instructions), os.environ.get(
            "AZURE_OPENAI_DEPLOYMENT", "gpt-5-mini"
        ) + "+tools"
