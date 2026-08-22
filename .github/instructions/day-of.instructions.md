---
applyTo: "**"
---

🔴 **10:50 필수요소 공개 — 우선순위가 바뀌었다.**
1. **`.github/instructions/stack.instructions.md`** ← 스택·배포는 여기가 정본 (Python + MAF + Copilot SDK)
2. `AGENTS.md` ← Azure 리소스·함정·공식 공지·제출 절차
3. `.github/copilot-instructions.md` ← 2026-08-21 초안, **F1·Node·SWA 서술 전부 폐기**

**필수요소: Microsoft Agent Framework + GitHub Copilot SDK + Azure 배포.** Node로는 불가(MAF에 JS 없음).
`GitHubCopilotAgent` + **Azure BYOK**로 두 요건 동시 충족, GitHub 토큰 불필요.

- 플랜 **B1 Basic + alwaysOn**. F1으로 내리지 마(콜드스타트 27.6초).
- 배포는 `./deploy.sh`만. 리소스·앱설정 재생성/재주입 금지. 키 stdout 금지.
- SWA 불가. `dependencies: {}` 유지. `max_tokens` 금지 → `max_completion_tokens` 4000.
- 정적 파일은 `public/`만. `url.pathname`에 decode 추가하지 마.

이유·명령 전문은 `AGENTS.md`. 이 파일은 자동첨부되는 어제 초안을 덮는 가드다.
