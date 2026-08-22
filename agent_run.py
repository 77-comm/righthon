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


async def run_agent(message: str, board: dict) -> tuple[str, str]:
    from agent_framework.github import GitHubCopilotAgent

    model = os.environ.get("COPILOT_MODEL", "gpt-5.6-luna")
    board_json = json.dumps(_compact_board(board), ensure_ascii=False)
    instructions = (
        DOCTRINE
        + "\n\n아래 JSON만 숫자 근거로 써라. 없는 값을 만들지 마라.\n"
        + board_json
    )
    options: dict = {"model": model}
    provider = _azure_provider()
    # GitHub 카탈로그(luna) 우선. 토큰이 없고 Azure만 있으면 BYOK.
    if os.environ.get("GITHUB_TOKEN") or os.environ.get("COPILOT_GITHUB_TOKEN"):
        pass
    elif provider:
        options["provider"] = provider
        options["model"] = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-5-mini")

    agent = GitHubCopilotAgent(instructions=instructions, default_options=options)
    async with agent:
        result = await agent.run(message)
    text = getattr(result, "text", None) or str(result)
    text = (text or "").strip()
    if not text:
        raise RuntimeError("empty agent content")
    return text, model
