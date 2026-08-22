#!/usr/bin/env bash
# Python App Service zip deploy. Does not touch righthon-hale.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
APP="${APP:-righthon-py}"
RG="${RG:-rg-matdathon}"

# MAF+Copilot SDK 동봉분. Oryx pip 금지 — 래퍼가 핀한 sdk==1.0.2가 PyPI에 없다(1.0.4로 조립).
# packages/ 는 gitignore. 한 번 만들면 재사용. 강제 재조립: PACKAGES_REBUILD=1
READY="$ROOT/packages/.ready"
if [ "${PACKAGES_REBUILD:-}" = "1" ]; then
  rm -rf "$ROOT/packages"
fi
if [ ! -f "$READY" ]; then
  echo "building packages/ (once; next deploys reuse)"
  mkdir -p "$ROOT/packages"
  PLAT="--only-binary=:all: --platform manylinux2014_x86_64 --platform manylinux_2_17_x86_64 --platform any --python-version 312 --implementation cp"
  python3 -m pip install --target packages $PLAT 'agent-framework-core==1.15.0' 'github-copilot-sdk==1.0.4'
  python3 -m pip install --target packages --no-deps 'agent-framework-github-copilot==1.0.3'
  date > "$READY"
else
  echo "reusing packages/ $(du -sh packages | awk '{print $1}')"
fi

# 다른 세션 배포가 돌면 겹치지 않는다.
SUB="$(az account show --query id -o tsv)"
ST="$(az rest --method get --url "/subscriptions/${SUB}/resourceGroups/${RG}/providers/Microsoft.Web/sites/${APP}/deployments?api-version=2022-03-01" --query "value[0].properties.status" -o tsv 2>/dev/null || echo 4)"
if [ "$ST" = "0" ] || [ "$ST" = "1" ] || [ "$ST" = "2" ]; then
  echo "refuse: ${APP} deploy already in progress (status=${ST})"
  exit 2
fi

ZIP="$(mktemp -d)/righthon-py.zip"
trap 'rm -f "$ZIP"' EXIT
zip -q -r "$ZIP" main.py board.py agent_run.py requirements.txt public doctrine skills packages -x "packages/bin/*" "*/__pycache__/*" "packages/.ready"
echo "zip $(du -h "$ZIP" | awk '{print $1}')"
az webapp deploy -g "$RG" -n "$APP" --src-path "$ZIP" --type zip
curl -sS --max-time 30 "https://${APP}.azurewebsites.net/healthz"
echo
