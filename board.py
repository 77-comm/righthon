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
        "creditor": "실질금리가 약양. 채권자는 간신히 보상받는다.",
        "debtor": "채무자 비용은 부담이나 극단은 아니다.",
        "tilt": "mixed",
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
        for fut in as_completed(futs):
            name = futs[fut]
            try:
                val = fut.result()
            except Exception:
                val = None
            if name in YF_SYMBOLS:
                yf[name] = val
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
        rr = metrics["real_rate"]["value"]
        cards.append({**c, "metrics": metrics, "sides": _side(rr)})

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
