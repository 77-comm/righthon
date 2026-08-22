"""Keyless macro board. World Bank + optional Yahoo. No 77-dan, no API keys."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

UA = "PerpMachine/1.0 (matdathon; educational)"
WB = "https://api.worldbank.org/v2"
YF = "https://query1.finance.yahoo.com/v8/finance/chart"

COUNTRIES: list[dict[str, Any]] = [
    {"id": "KR", "iso3": "KOR", "name": "한국", "role": "focus"},
    {"id": "US", "iso3": "USA", "name": "미국", "role": "focus"},
    {"id": "JP", "iso3": "JPN", "name": "일본", "role": "focus"},
    {"id": "DE", "iso3": "DEU", "name": "독일", "role": "focus"},
    {"id": "CN", "iso3": "CHN", "name": "중국", "role": "focus"},
    {"id": "GB", "iso3": "GBR", "name": "영국", "role": "focus"},
    {"id": "BR", "iso3": "BRA", "name": "브라질", "role": "focus"},
    # BC Ch.17: 부채보다 유동자산이 많은 완충 사례. 가우시안 모집단이 아님.
    {"id": "SG", "iso3": "SGP", "name": "싱가포르", "role": "buffer"},
    {"id": "NO", "iso3": "NOR", "name": "노르웨이", "role": "buffer"},
    {"id": "CH", "iso3": "CHE", "name": "스위스", "role": "buffer"},
]

# layer: productivity | long | short
INDICATORS: dict[str, dict[str, str]] = {
    "real_rate": {"code": "FR.INR.RINR", "layer": "short", "unit": "%", "label": "실질금리"},
    "inflation": {"code": "FP.CPI.TOTL.ZG", "layer": "short", "unit": "%", "label": "인플레"},
    "gdp_growth": {"code": "NY.GDP.MKTP.KD.ZG", "layer": "short", "unit": "%", "label": "GDP성장"},
    "productivity": {"code": "NY.GDP.PCAP.KD.ZG", "layer": "productivity", "unit": "%", "label": "1인당성장"},
    "gov_debt": {"code": "GC.DOD.TOTL.GD.ZS", "layer": "long", "unit": "%GDP", "label": "정부부채"},
    "fx_reserves": {"code": "FI.RES.TOTL.CD", "layer": "long", "unit": "USD", "label": "외환보유"},
}

YF_SYMBOLS = {
    "us_10y": "^TNX",
    "us_3m": "^IRX",
}

BIS_POL = "https://stats.bis.org/api/v2/data/dataflow/BIS/WS_CBPOL/1.0/M.{iso2}?lastNObservations=4&format=csv"

_CACHE: dict[str, Any] = {"ts": 0.0, "data": None}
_TTL = 600.0


def _http_json(url: str, timeout: float = 12.0) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as res:
        return json.loads(res.read().decode("utf-8"))


def _wb_series(code: str) -> dict[str, list[dict[str, Any]]]:
    ids = ";".join(c["iso3"] for c in COUNTRIES)
    url = (
        f"{WB}/country/{ids}/indicator/{code}"
        f"?format=json&per_page=80&mrv=8&mrvd=y"
    )
    out: dict[str, list[dict[str, Any]]] = {c["iso3"]: [] for c in COUNTRIES}
    try:
        payload = _http_json(url)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, IndexError):
        return out
    rows = payload[1] if isinstance(payload, list) and len(payload) > 1 else None
    if not rows:
        return out
    for row in rows:
        iso = (row.get("countryiso3code") or "").upper()
        if iso not in out:
            continue
        val = row.get("value")
        if val is None:
            continue
        out[iso].append({"year": row.get("date"), "value": float(val)})
    for iso in out:
        out[iso].sort(key=lambda x: x["year"] or "")
    return out


def _yahoo_last(symbol: str) -> dict[str, Any] | None:
    from urllib.parse import quote

    url = f"{YF}/{quote(symbol, safe='')}?interval=1d&range=1mo"
    try:
        payload = _http_json(url, timeout=8.0)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None
    result = ((payload.get("chart") or {}).get("result") or [None])[0]
    if not result:
        return None
    meta = result.get("meta") or {}
    price = meta.get("regularMarketPrice")
    if price is None:
        return None
    closes = ((result.get("indicators") or {}).get("quote") or [{}])[0].get("close") or []
    spark = [c for c in closes if c is not None][-12:]
    return {"symbol": symbol, "price": float(price), "spark": spark}


def _bis_policy(iso2: str) -> dict[str, Any] | None:
    import csv
    import io

    url = BIS_POL.format(iso2=iso2)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/csv"})
        with urllib.request.urlopen(req, timeout=10.0) as res:
            raw = res.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError):
        return None
    rows = list(csv.DictReader(io.StringIO(raw)))
    if not rows:
        return None
    last = rows[-1]
    try:
        return {
            "year": last.get("TIME_PERIOD"),
            "value": float(last["OBS_VALUE"]),
            "label": "정책금리",
            "layer": "short",
            "unit": "%",
            "code": "BIS.WS_CBPOL",
            "spark": [float(r["OBS_VALUE"]) for r in rows if r.get("OBS_VALUE")],
        }
    except (KeyError, ValueError, TypeError):
        return None


def fetch_macro(country: str, indicator: str) -> str:
    """Tool: one live series. country=KR/US/이름, indicator=real_rate|policy_rate|WB code."""
    board = build_board()
    key = (country or "").strip()
    hit = None
    for c in board.get("cards") or []:
        if key.upper() in {c["id"], c["iso3"], c["name"].upper()} or key in c["name"]:
            hit = c
            break
    if not hit:
        return f"unknown country: {country}"
    ind = (indicator or "real_rate").strip()
    aliases = {spec["code"]: name for name, spec in INDICATORS.items()}
    aliases.update({name: name for name in INDICATORS})
    aliases["policy_rate"] = "policy_rate"
    aliases["policy"] = "policy_rate"
    name = aliases.get(ind) or aliases.get(ind.upper())
    if not name:
        return f"unknown indicator: {indicator}"
    m = (hit.get("metrics") or {}).get(name) or {}
    return json.dumps(
        {
            "country": hit["id"],
            "indicator": name,
            "value": m.get("value"),
            "year": m.get("year"),
            "code": m.get("code"),
            "unit": m.get("unit"),
        },
        ensure_ascii=False,
    )


def _latest(points: list[dict[str, Any]]) -> dict[str, Any] | None:
    return points[-1] if points else None


def _side(real_rate: float | None) -> dict[str, str]:
    if real_rate is None:
        return {
            "creditor": "숫자 없음 — 빈티지가 비어 있다.",
            "debtor": "숫자 없음 — 빈티지가 비어 있다.",
            "tilt": "unknown",
        }
    if real_rate >= 2:
        return {
            "creditor": "실질금리가 높다. 현금·채권 보유가 물가를 이긴다.",
            "debtor": "같은 숫자는 빚의 실질비용이다. 차입은 비싸다.",
            "tilt": "creditor",
        }
    if real_rate <= 0:
        return {
            "creditor": "실질금리가 0 이하. 명목 이자가 물가에 진다.",
            "debtor": "빚의 실질비용이 싸다. 소득만 버텨 주면 채무자가 유리하다.",
            "tilt": "debtor",
        }
    return {
        "creditor": "실질금리가 0~2 사이. 채권자는 간신히 보상받는다.",
        "debtor": "채무자 비용은 부담이나 극단은 아니다.",
        "tilt": "mixed",
    }


# 도구 '계층' 메뉴. 개별 상품·종목 아님 (책임AI).
_MENU: dict[str, dict[str, str]] = {
    "KR": {
        "park": "RP(환매조건부)·통안채·CMA/MMF",
        "long": "국고채 3년·10년물",
        "linker": "물가연동국고채(KTBi)",
    },
    "US": {
        "park": "T-bill 3개월물·MMF",
        "long": "T-note 10년물",
        "linker": "TIPS",
    },
    "_": {
        "park": "단기 국채·정책금리 연동 파킹형",
        "long": "장기 국채",
        "linker": "물가연동 국채",
    },
}

_DISCLAIMER = "도구 계층의 성질 설명이다(교육용). 특정 상품·종목·시점의 매매 권유가 아니다."


def _playbook(cid: str, real_rate: float | None, tilt: str) -> dict[str, Any]:
    """tilt를 사람 말로 번역: 현금 판정 → 도구 계층 제안 → 빚 있는 쪽."""
    m = _MENU.get(cid) or _MENU["_"]
    if tilt == "creditor":
        return {
            "cash": "이 통화를 들고 있는 게 이득이다. 이자가 물가를 이겨 구매력이 자란다.",
            "do": [
                f"이자를 실제로 받아라 — {m['park']}가 실질금리를 그대로 챙기는 계층이다.",
                f"금리가 꺾일 때 자본이득 성질까지 원하면 {m['long']}. 단, 금리가 더 오르면 평가손 쪽이다.",
                f"물가 재점화가 걱정이면 {m['linker']} — 원금이 물가에 연동된다.",
            ],
            "debt": [
                "신규 차입은 비싸다. 변동금리 부채가 있으면 고정 전환·조기상환 검토가 이 환경의 정석이다."
            ],
            "disclaimer": _DISCLAIMER,
        }
    if tilt == "debtor":
        return {
            "cash": "이 통화를 현금·보통예금으로 들고 있으면 손해다. 이자가 물가에 져서 구매력이 깎인다.",
            "do": [
                f"놀리는 돈이라도 최소 {m['park']}로 옮겨 손실 폭부터 줄여라.",
                f"물가만큼은 지키고 싶으면 {m['linker']} — 인플레를 보상하는 성질이다.",
                f"장기 고정금리 {m['long']}는 인플레가 더 오르면 실질가치가 더 깎이는 쪽이다.",
            ],
            "debt": [
                "고정금리 부채의 실질 부담은 인플레가 깎아 준다. 무리한 조기상환보다 소득 유지가 먼저다."
            ],
            "disclaimer": _DISCLAIMER,
        }
    if tilt == "mixed":
        return {
            "cash": "현금이 크게 이득도 손해도 아니다. 이자가 물가를 간신히 따라간다.",
            "do": [
                f"{m['park']}에 두고 관망해도 벌점이 없는 구간이다.",
                f"방향을 정하기 싫으면 만기를 나눠라 — 일부 {m['park']}, 일부 {m['long']}.",
            ],
            "debt": [
                "차입 비용이 극단이 아니다. 금리 방향보다 본인 현금흐름이 결정 변수다."
            ],
            "disclaimer": _DISCLAIMER,
        }
    return {
        "cash": "이 나라 실질금리 빈티지가 비어 있다. 판정 보류.",
        "do": [],
        "debt": [],
        "disclaimer": _DISCLAIMER,
    }


def build_board() -> dict[str, Any]:
    now = time.time()
    cached = _CACHE.get("data")
    if cached is not None and now - float(_CACHE["ts"]) < _TTL:
        return cached

    wb: dict[str, dict[str, list]] = {}
    yf: dict[str, Any] = {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        futs = {pool.submit(_wb_series, spec["code"]): key for key, spec in INDICATORS.items()}
        futs.update({pool.submit(_yahoo_last, sym): name for name, sym in YF_SYMBOLS.items()})
        futs.update({pool.submit(_bis_policy, c["id"]): f"bis:{c['id']}" for c in COUNTRIES})
        bis: dict[str, Any] = {}
        for fut in as_completed(futs):
            name = futs[fut]
            try:
                val = fut.result()
            except Exception:
                val = None
            if name in YF_SYMBOLS:
                yf[name] = val
            elif name.startswith("bis:"):
                bis[name.split(":", 1)[1]] = val
            else:
                wb[name] = val or {}

    cards = []
    for c in COUNTRIES:
        iso = c["iso3"]
        metrics = {}
        for key, spec in INDICATORS.items():
            pts = (wb.get(key) or {}).get(iso) or []
            last = _latest(pts)
            metrics[key] = {
                "label": spec["label"],
                "layer": spec["layer"],
                "unit": spec["unit"],
                "code": spec["code"],
                "year": last["year"] if last else None,
                "value": last["value"] if last else None,
                "spark": [p["value"] for p in pts],
            }
        pol = bis.get(c["id"])
        if pol:
            metrics["policy_rate"] = pol
        else:
            metrics["policy_rate"] = {
                "label": "정책금리",
                "layer": "short",
                "unit": "%",
                "code": "BIS.WS_CBPOL",
                "year": None,
                "value": None,
                "spark": [],
            }
        rr = metrics["real_rate"]["value"]
        sides = _side(rr)
        cards.append(
            {**c, "metrics": metrics, "sides": sides, "playbook": _playbook(c["id"], rr, sides["tilt"])}
        )

    def _median(vals: list[float]) -> float | None:
        if not vals:
            return None
        s = sorted(vals)
        n = len(s)
        mid = n // 2
        return s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2

    benches: dict[str, Any] = {}
    for key in INDICATORS:
        all_v = [c["metrics"][key]["value"] for c in cards if c["metrics"][key]["value"] is not None]
        buf_v = [
            c["metrics"][key]["value"]
            for c in cards
            if c["role"] == "buffer" and c["metrics"][key]["value"] is not None
        ]
        benches[key] = {
            "peer_median": _median(all_v),
            "buffer_median": _median(buf_v),
            "n_peer": len(all_v),
            "n_buffer": len(buf_v),
        }
        for c in cards:
            v = c["metrics"][key]["value"]
            med = benches[key]["peer_median"]
            if v is None or med is None:
                c["metrics"][key]["vs_peer"] = None
            else:
                c["metrics"][key]["vs_peer"] = v - med

    us10 = (yf.get("us_10y") or {}).get("price")
    us3m = (yf.get("us_3m") or {}).get("price")
    market = {
        "source": "Yahoo Finance (키 없음, 비공식). Azure에서 막히면 이 블록만 빠진다.",
        "us_10y": yf.get("us_10y"),
        "us_3m": yf.get("us_3m"),
        "us_curve": None
        if us10 is None or us3m is None
        else {"value": round(us10 - us3m, 3), "unit": "pp", "label": "미국 10년−3개월"},
    }

    data = {
        "ok": True,
        "vintage_note": "WB는 연간·후행. 실질금리가 핵심. 기준선은 동료 중앙값이지 달리오 가우시안이 아니다.",
        "benchmark_note": (
            "달리오 원전은 z-score로 사이클을 분류하지 않는다. "
            "완충국(SG/NO/CH)은 BC Ch.17 재무상태 사례다. n이 작아 정규분포 적합은 하지 않는다."
        ),
        "benchmarks": benches,
        "cards": cards,
        "market": market,
        "fetched_at": int(now),
    }
    _CACHE["ts"] = now
    _CACHE["data"] = data
    return data
