#!/bin/bash
# 한 줄 배포. 현장에서는 이것만 실행한다 — 약 40초.
#
#   ./deploy.sh
#
# GitHub Actions를 쓰지 않는 이유: CI 왕복 2~3분 + 실패 지점이 늘어난다.
# 6시간짜리 대회에서 30분마다 배포하려면 즉시 피드백이 낫다.
set -euo pipefail

APP=righthon-hale
RG=rg-matdathon
ZIP=$(mktemp -t righthon).zip

cd "$(dirname "$0")"

# 배포 대상만 담는다. node_modules·.git은 넣지 않는다.
zip -q -r "$ZIP" . \
  -x '.git/*' -x 'node_modules/*' -x '.github/*' -x '.vscode/*' \
  -x '*.sh' -x '.gitignore' -x 'README.md'

echo "▶ 배포 중..."
az webapp deploy -n "$APP" -g "$RG" --src-path "$ZIP" --type zip -o none

rm -f "$ZIP"

echo "▶ 헬스체크..."
sleep 8
curl -s --max-time 60 "https://$APP.azurewebsites.net/healthz"
echo
echo "✅ https://$APP.azurewebsites.net"
