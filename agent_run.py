"""MAF + Copilot SDK. Token/keys come from App Settings only."""

from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CLI_DIR = Path(os.environ.get("COPILOT_CLI_EXTRACT_DIR") or (ROOT / "cli-linux"))
CLI_BIN = CLI_DIR / "copilot"
_CLI_LINUX_URL = "https://github.com/github/copilot-cli/releases/download/v1.0.65/copilot-linux-x64.tar.gz"
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
    return {"type": "azure", "base_url": f"https://{host}", "api_key": key}


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


def cli_ready() -> bool:
    return CLI_BIN.is_file() and CLI_BIN.stat().st_size > 1_000_000


def warmup_linux_cli() -> str:
    """Download Linux Copilot CLI into COPILOT_CLI_EXTRACT_DIR. Safe to call in a thread."""
    if cli_ready():
        return str(CLI_BIN)
    import tarfile
    import tempfile
    import urllib.request

    CLI_DIR.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(_CLI_LINUX_URL, headers={"User-Agent": "PerpMachine"})
    with urllib.request.urlopen(req, timeout=120) as res:
        blob = res.read()
    with tarfile.open(fileobj=__import__("io").BytesIO(blob), mode="r:gz") as tf:
        member = next(
            (m for m in tf.getmembers() if m.isfile() and Path(m.name).name == "copilot"),
            None,
        )
        if member is None:
            raise RuntimeError("copilot binary missing in archive")
        src = tf.extractfile(member)
        data = src.read() if src else b""
    tmp = Path(tempfile.mkstemp(dir=CLI_DIR, prefix=".copilot.")[1])
    tmp.write_bytes(data)
    tmp.chmod(0o755)
    tmp.replace(CLI_BIN)
    return str(CLI_BIN)


def maf_importable() -> bool:
    try:
        from agent_framework_github_copilot import GitHubCopilotAgent  # noqa: F401

        return True
    except Exception:
        return False


def _maf_worker(message: str, instructions: str) -> str:
    """MAF+Copilot SDK를 전용 스레드·전용 루프에서 돌린다.
    SDK의 CLI 런타임 다운로드/스폰이 동기라 메인 루프를 막으면 gunicorn이 워커를 죽인다(502 실측)."""
    import asyncio

    _ensure_local_cli()

    from agent_framework.github import GitHubCopilotAgent

    from board import fetch_macro

    provider = _azure_provider()
    options: dict = {
        "model": os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-5-mini"),
        "skill_directories": [SKILLS_DIR],
        "cli_path": str(CLI_BIN),
        "timeout": 40,
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


# MAF 상태: Azure Files의 143MB CLI exec이 느려 첫 시도가 타임아웃 나기 쉽다.
# 실패하면 쿨다운 동안 폴백 직행으로 심사 요청 지연을 막는다.
_MAF = {"cooldown_until": 0.0, "last_error": None, "last_ok": None, "cli_local": False}
_MAF_TIMEOUT = 35.0
_MAF_COOLDOWN = 120.0


def _ensure_local_cli() -> None:
    """/home(Azure Files)의 CLI를 로컬 디스크 /tmp로 한 번 복사해 스폰을 빠르게 한다."""
    if _MAF["cli_local"]:
        return
    import shutil
    import stat

    src = Path(os.environ.get("COPILOT_CLI_EXTRACT_DIR", "/home/copilot-cli")) / "copilot"
    dst_dir = Path("/tmp/copilot-cli")
    dst = dst_dir / "copilot"
    try:
        if dst.is_file() and dst.stat().st_size > 1e6:
            os.environ["COPILOT_CLI_EXTRACT_DIR"] = str(dst_dir)
            _MAF["cli_local"] = True
            return
        if src.is_file() and src.stat().st_size > 1e6:
            dst_dir.mkdir(parents=True, exist_ok=True)
            tmp = dst_dir / ".copying"
            shutil.copyfile(src, tmp)
            os.replace(tmp, dst)
            dst.chmod(dst.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            os.environ["COPILOT_CLI_EXTRACT_DIR"] = str(dst_dir)
            _MAF["cli_local"] = True
    except Exception as exc:  # 복사 실패면 기존 경로로 진행
        _MAF["last_error"] = f"cli-copy: {exc}"


def maf_status() -> dict:
    import time

    return {
        "cli_local": _MAF["cli_local"],
        "cooldown": max(0, round(_MAF["cooldown_until"] - time.time())),
        "last_ok": _MAF["last_ok"],
        "last_error": (_MAF["last_error"] or "")[:200] or None,
    }


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
    import time

    _ensure_local_cli()
    try_maf = os.environ.get("TRY_MAF") == "1" or (maf_importable() and cli_ready())
    if try_maf and time.time() >= _MAF["cooldown_until"]:
        try:
            text = await asyncio.wait_for(
                asyncio.to_thread(_maf_worker, message, instructions), timeout=_MAF_TIMEOUT
            )
            if not text:
                raise RuntimeError("empty agent content")
            _MAF["last_ok"] = time.strftime("%H:%M:%S")
            _MAF["last_error"] = None
            return text, f"GitHubCopilotAgent:{model}"
        except Exception as exc:
            _MAF["last_error"] = f"{type(exc).__name__}: {exc}"
            _MAF["cooldown_until"] = time.time() + _MAF_COOLDOWN
            print(f"[maf] fail -> fallback: {_MAF['last_error'][:300]}", flush=True)
    reply = await asyncio.to_thread(_azure_chat, message, instructions)
    return reply, model + "+tools"
