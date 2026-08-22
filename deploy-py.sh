#!/usr/bin/env bash
# Python App Service zip deploy. Does not touch righthon-hale.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
APP="${APP:-righthon-py}"
RG="${RG:-rg-matdathon}"
ZIP="$(mktemp -d)/righthon-py.zip"
trap 'rm -f "$ZIP"' EXIT
zip -q -r "$ZIP" main.py board.py requirements.txt public doctrine
az webapp deploy -g "$RG" -n "$APP" --src-path "$ZIP" --type zip
curl -sS --max-time 30 "https://${APP}.azurewebsites.net/healthz"
echo
