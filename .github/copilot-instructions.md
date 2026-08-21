# righthon — Copilot 현장 지시

이 파일을 항상 따른다. 추측으로 새 스택을 열지 않는다.

## 허용 도구 (주최 규칙)

- 심사에 보이는 면: **VS Code + Copilot Chat/Agent**, 보조로 **Copilot CLI**. Copilot app 쓰지 않음.
- 주최 문구: 타사 AI 코딩 **IDE/창** 금지 = 퇴장. Claude·Grok·Cursor·Codex **앱을 켜지 마.**

## OmO — Copilot이 bash로 부르는 도구 (창을 열지 마)

감독이 느슨하면(터미널 Always allow / YOLO) Copilot Agent가 **자기 bash에서 `omo`를 돌리고 stdout만 가져와** 쓰면 된다. hale이 채팅하는 면은 끝까지 Copilot이다. `omo` GUI·별도 터미널 탭·데모 화면에 OmO를 띄우지 마.

**언제:** 대규모 검색·다중파일 리서치·insane-search류. 배포·`az`·키는 여전히 Copilot+`az`만.

**호출 (탐색 인자 금지 — 모르는 서브커맨드는 전부 유료 프롬프트):**

```bash
command -v omo || export PATH="$HOME/.bun/bin:/opt/homebrew/bin:$PATH"
omo --help          # 조사는 이것만. completion/version/status 금지
omo -p "질문 한 줄. 답만. 레포 /Users/hale/GitHub/righthon"
```

`-p` = 비대화형. 없으면 `--help`로 비대화 플래그를 확인한 뒤만 실행.  
맥에 `omo` 없으면 hale에게 물어라. 몰래 `npm i -g` 하지 마(bun 전역이 정본). 설치가 안 되어 있으면 **이 절을 건너뛰고 Copilot만**.

**쓸 수 있는 OmO 쪽 능력** (있으면 켜고, 없으면 대체하지 마):

- 코드베이스 검색 / **insane-search** (스킬·플러그인으로 노출되면 `-p` 프롬프트에 명시)
- 다중파일 리서치·병렬 서브에이전트
- 해시라인 편집 등 senpi 기능

프롬프트에 적어라: 「파일을 직접 고치지 마. 조사·검색 결과와 패치 초안만 stdout. insane-search 가능하면 그걸 써.」  
가져온 초안은 **Copilot이 righthon에 적용**한다. omo가 git push / az / 키를 만지지 않게 하라.

**가드:** 같은 `omo -p`가 두 번 실패하면 중단. 루프·데몬(`omo app-server`) 금지. 종량 API 키로 폴백하지 마 — Copilot Max 정액만. 키·토큰을 stdout에 에코하지 마.

## 계정·레포

- IDE·Copilot 로그인: **`hale-righthon`** (Max는 여기만).
- 코드 집: **`77-comm/righthon`**. 새 레포·포크 만들지 마.
- Azure 구독: 이미 로그인된 **Azure for Students** (`hale_knu@office.knu.ac.kr`). 새 구독 생성 금지.
- 리소스: `rg-matdathon` / `aif-matdathon-hale` / deployment **`gpt-5-mini`**. 새 AI 계정 파지 마.

## 아키텍처 (변경 금지)

- 웹앱만. 네이티브·VM·AKS·Container Apps·App Service 단독 신설 금지.
- **Azure Static Web Apps + 관리형 Functions** (`api/`). IaaS 금지.
- 키는 Functions **Application settings**만. `index.html`·프론트 JS·채팅 로그에 키·endpoint 금지.
- `gpt-5-mini`는 `max_tokens` 금지 → **`max_completion_tokens`** (수천). 낮으면 HTTP 200에 `content` 빈 문자열.

## Azure: CLI 먼저, MCP는 조회만

| | 써라 | 쓰지 마라 |
|---|---|---|
| 생성·배포·설정·키 | **`az` / `azd`** (이미 설치됨) | MCP에 “만들어 줘” |
| 구독에 뭐가 있나 | Azure MCP 또는 `az` | 서버 6개 동시 |
| 로컬 SWA | VS Azure 확장. `swa`/`func` 글로벌 없음 | 없는 CLI를 설치부터 하지 마. 확장으로 |

배포 문장: 「새 리소스 그룹 만들지 마. 이 레포를 기존 Students 구독 SWA에 붙여. 키는 Functions 설정에만.」

## MCP — 적게 (컨텍스트 부패)

토큰·도구 목록이 매 턴 붙는다. **당일 켜둘 MCP는 최대 2.**

- 켜도 됨: **Azure MCP** (이미 확장), 필요 시 **GitHub MCP**
- 켜지 마: Microsoft Learn, Playwright, MarkItDown, Awesome Copilot, 그 외 탐색용
- 새 MCP를 주제에 맞춰 추가하지 마. 도구 검색이 답을 잡아먹는다.

`.vscode/mcp.json`이 비어 있으면 빈 채로 둬라. 확장 Azure MCP면 충분하다.

## 감독 — Copilot은 감독자가 아니다

VS Agent / Copilot CLI에는 77단식 별도 감독 에이전트가 없다. **감독은 hale.**

현장 확인:

1. 터미널·`az`는 **명령마다 승인**이 뜨는지.
2. **Always allow / YOLO / --allow-all / --yolo** 켜지 마. `az group delete`, 키 출력, 구독 변경이 그대로 나간다.
3. Auto-approve가 기본이면 위험한 명령(`delete`, `purge`, `account set`)만 수동으로 되돌릴 수 있는지 첫 30분에 테스트.
4. 같은 명령을 세 번 실패하면 도구를 바꾸거나 멈춰라. 루프가 쿼터를 먹는다.

감독이 **빡빡**하면(명령마다 승인): `omo`를 제안하지 마. `az`·편집만.
감독이 **느슨**하면(Always allow): 위 OmO 절을 **사용 가능 수단**으로 켜라. 그래도 MCP는 2개 초과 금지. `az group delete` 류는 느슨해도 실행 전 한 줄로 hale에게 확인.

## 당일 순서

주제는 **개인 생산성 향상 에이전트 앱**(참가 메일). 세부는 당일 공개. 껍데기는 그 주제로 두고, 당일 필수요소만 맞춰 살을 붙여.

1. 기능 **3개 이하**로 자른다.
2. 껍데기 이름만 바꿔 **먼저 배포**. 링크가 있어야 채점된다.
3. 30분마다 push → 배포 확인.
4. 기능 동결 시각을 지킨다. 마지막 push 여유.

새 프레임워크·새 Functions 언어·새 모델 공급자를 “더 좋아서” 들이지 마.
