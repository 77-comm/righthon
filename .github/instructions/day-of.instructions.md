---
applyTo: "**"
---

당일 진실은 레포 루트 `AGENTS.md`. `.github/copilot-instructions.md`는 2026-08-21 초안이며 **F1 서술은 폐기**. 충돌하면 AGENTS.md.

- 플랜 **B1 Basic + alwaysOn**. F1으로 내리지 마(콜드스타트 27.6초).
- 배포는 `./deploy.sh`만. 리소스·앱설정 재생성/재주입 금지. 키 stdout 금지.
- SWA 불가. `dependencies: {}` 유지. `max_tokens` 금지 → `max_completion_tokens` 4000.
- 정적 파일은 `public/`만. `url.pathname`에 decode 추가하지 마.

이유·명령 전문은 `AGENTS.md`. 이 파일은 자동첨부되는 어제 초안을 덮는 가드다.
