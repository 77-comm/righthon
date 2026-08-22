---
applyTo: "**"
---

🔴 **10:50 필수요소 공개 — 우선순위가 바뀌었다.**
1. **`.github/instructions/scoring.instructions.md`** ← **무엇을 만들지**를 정한다 (심사 배점)
2. **`.github/instructions/stack.instructions.md`** ← **어떻게 만들지** (Python + MAF + Copilot SDK)
3. `AGENTS.md` ← Azure 리소스·함정·공식 공지·제출 절차
4. `.github/instructions/aspire.instructions.md` ← Aspire는 **쓰지 않는다**(감점 근거)
5. `.github/copilot-instructions.md` ← 2026-08-21 초안, **F1·Node·SWA 서술 전부 폐기**

🎯 **배점 1순위는 「Copilot SDK + MAF 활용 깊이」 25%.** 단순 프록시로는 대부분 잃는다 —
**도구 호출 + 스트리밍**이 있어야 한다. Azure 18%는 새 서비스 추가가 아니라
**반복 가능한 배포·관찰 가능성·안정성**이며 우리는 이미 갖고 있다(적기만 하면 된다).

**필수요소: Microsoft Agent Framework + GitHub Copilot SDK + Azure 배포.** Node로는 불가(MAF에 JS 없음).
`GitHubCopilotAgent` + **Azure BYOK**로 두 요건 동시 충족, GitHub 토큰 불필요.

- 플랜 **B1 Basic + alwaysOn**. F1으로 내리지 마(콜드스타트 27.6초).
- 배포는 `./deploy.sh`만. 리소스·앱설정 재생성/재주입 금지. 키 stdout 금지.
- SWA 불가. `dependencies: {}` 유지. `max_tokens` 금지 → `max_completion_tokens` 4000.
- 정적 파일은 `public/`만. `url.pathname`에 decode 추가하지 마.

이유·명령 전문은 `AGENTS.md`. 이 파일은 자동첨부되는 어제 초안을 덮는 가드다.
