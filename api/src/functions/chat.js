const { app } = require('@azure/functions');

// Azure OpenAI 자격증명은 SWA 앱 설정(서버 측 환경변수)에서만 읽는다.
// 프론트 JS에 키를 두면 개발자도구에 그대로 노출된다.
const ENDPOINT = process.env.AZURE_OPENAI_ENDPOINT;
const API_KEY = process.env.AZURE_OPENAI_KEY;
const DEPLOYMENT = process.env.AZURE_OPENAI_DEPLOYMENT || 'gpt-5-mini';
const API_VERSION = process.env.AZURE_OPENAI_API_VERSION || '2025-04-01-preview';

const SYSTEM_PROMPT =
  '너는 사용자의 생산성을 돕는 비서다. 입력을 실행 가능한 항목으로 정리해 한국어로 간결히 답하라.';

app.http('chat', {
  methods: ['POST'],
  authLevel: 'anonymous',
  handler: async (request, context) => {
    if (!ENDPOINT || !API_KEY) {
      context.error('Azure OpenAI 설정 누락');
      return { status: 500, jsonBody: { error: '서버 설정 누락' } };
    }

    let message;
    try {
      ({ message } = await request.json());
    } catch {
      return { status: 400, jsonBody: { error: '잘못된 JSON' } };
    }
    if (!message || typeof message !== 'string') {
      return { status: 400, jsonBody: { error: 'message 필드가 필요합니다' } };
    }

    const url = `${ENDPOINT.replace(/\/$/, '')}/openai/deployments/${DEPLOYMENT}` +
                `/chat/completions?api-version=${API_VERSION}`;

    let res;
    try {
      res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'api-key': API_KEY },
        body: JSON.stringify({
          messages: [
            { role: 'system', content: SYSTEM_PROMPT },
            { role: 'user', content: message }
          ],
          // gpt-5 계열은 max_tokens를 거부한다. 또한 이 한도는 reasoning 토큰까지
          // 함께 소모하므로 너무 낮으면 본문이 빈 채로 돌아온다.
          max_completion_tokens: 4000
        })
      });
    } catch (err) {
      context.error('모델 호출 실패', err);
      return { status: 502, jsonBody: { error: '모델 호출 실패' } };
    }

    if (!res.ok) {
      // 응답 본문에 자격증명이 섞일 수 있으므로 상태 코드만 남긴다.
      context.error(`모델 응답 오류: ${res.status}`);
      return { status: 502, jsonBody: { error: `모델 응답 오류 ${res.status}` } };
    }

    const data = await res.json();
    const reply = data.choices?.[0]?.message?.content ?? '';

    return { jsonBody: { reply } };
  }
});
