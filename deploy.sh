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

# mktemp -d 로 디렉터리를 잡고 그 안에 만든다.
# `$(mktemp -t x).zip` 형태는 mktemp가 만든 원본 파일이 그대로 남아 매번 찌꺼기가 쌓인다.
TMPDIR_=$(mktemp -d)
ZIP="$TMPDIR_/righthon.zip"
trap 'rm -rf "$TMPDIR_"' EXIT

cd "$(dirname "$0")"

# 배포 대상을 화이트리스트로 명시한다.
# 제외 목록(-x) 방식은 새 파일이 생길 때마다 조용히 새어나가므로 쓰지 않는다.
zip -q -r "$ZIP" public server.js package.json

echo "▶ 배포 중..."
az webapp deploy -n "$APP" -g "$RG" --src-path "$ZIP" --type zip -o none

rm -f "$ZIP"

echo "▶ 헬스체크..."
sleep 8
curl -s --max-time 60 "https://$APP.azurewebsites.net/healthz"
echo
echo "✅ https://$APP.azurewebsites.net"
