#!/usr/bin/env bash
# Python App Service zip deploy. Does not touch righthon-hale.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
APP="${APP:-righthon-py}"
RG="${RG:-rg-matdathon}"

# MAF+Copilot SDK 동봉분. Oryx pip 금지 — 래퍼가 핀한 sdk==1.0.2가 PyPI에 없다(1.0.4로 조립).
if [ ! -d packages ]; then
  PLAT="--only-binary=:all: --platform manylinux2014_x86_64 --platform manylinux_2_17_x86_64 --platform any --python-version 312 --implementation cp"
  python3 -m pip install --target packages $PLAT 'agent-framework-core==1.15.0' 'github-copilot-sdk==1.0.4' -q
  python3 -m pip install --target packages --no-deps 'agent-framework-github-copilot==1.0.3' -q
fi

ZIP="$(mktemp -d)/righthon-py.zip"
trap 'rm -f "$ZIP"' EXIT
zip -q -r "$ZIP" main.py board.py agent_run.py requirements.txt public doctrine skills packages -x "packages/bin/*" "*/__pycache__/*"
az webapp deploy -g "$RG" -n "$APP" --src-path "$ZIP" --type zip
curl -sS --max-time 30 "https://${APP}.azurewebsites.net/healthz"
echo
