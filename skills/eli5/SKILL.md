---
name: eli5
description: >
  Explain a hard idea with a short visual-first answer, then the precise numbers.
  Use when the user is not a macro specialist, or when dual creditor/debtor
  advice would otherwise be a wall of text.
---

# ELI5 — 모르는 사람에게 먼저, 정밀은 바로 아래

이 스킬은 Anthropic `/eli5` 플러그인이 **아니다**. 우리 레포 문구다.
MAF `GitHubCopilotAgent`와 Azure 채팅이 같은 파일을 읽는다.

## 언제

- 실질금리·부채/GDP·양면 제안을 사용자가 한눈에 못 읽을 때
- “그래서 나한테 뭐가 유리하냐”만 있을 때

## 형식 (채팅 답)

1. **한 줄 그림** (2문장 이하). 비유는 돈·이자·물가만. 쿠키·자동차 API 비유 금지.
2. **채권자 (lender-creditor)** — 그 숫자가 현금 보유자에게 의미하는 것 + 연도/시리즈.
3. **채무자 (borrower-debtor)** — 같은 숫자가 빚진 사람에게 의미하는 것.
4. **빈티지** — 연간/월간인지. 지난주 데이터가 아니면 그렇다고 써라.

원전 용어(lender-creditor, borrower-debtor, 실질금리)는 지우지 마라.
쉽게 = 구조를 보이게. 유치하게 ≠ 쉽게.

## 하지 말 것

- 매수/매도
- 없는 숫자
- 올웨더 일변
- ELI5만 하고 양면을 생략
