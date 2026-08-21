// righthon — App Service(Linux/Node 20) 단일 프로세스 서버.
//
// 의존성 0개로 유지한다. npm install 실패는 배포 실패의 가장 흔한 원인이고,
// 해커톤 현장 네트워크에서 그걸 디버깅할 시간이 없다.
// Node 20 내장 fetch를 쓰므로 node-fetch도 불필요하다.
//
// 원래 Azure Static Web Apps + 관리형 Functions로 설계했으나, 이 구독의
// "Allowed resource deployment regions" 정책이 SWA 지원 리전(Central US /
// East US 2 / West US 2 / West Europe / East Asia)을 전부 차단해 생성 자체가
// 불가능했다(RequestDisallowedByAzure, 2026-08-21 실측). koreacentral에서
// 되는 PaaS가 App Service라 이쪽으로 옮겼다.

const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');

const PORT = process.env.PORT || 8080;

// 자격증명은 App Service 애플리케이션 설정에서만 읽는다.
// 프론트 JS에 두면 개발자도구에 그대로 노출된다.
const ENDPOINT = process.env.AZURE_OPENAI_ENDPOINT;
const API_KEY = process.env.AZURE_OPENAI_KEY;
const DEPLOYMENT = process.env.AZURE_OPENAI_DEPLOYMENT || 'gpt-5-mini';
const API_VERSION = process.env.AZURE_OPENAI_API_VERSION || '2025-04-01-preview';

const SYSTEM_PROMPT =
  '너는 사용자의 생산성을 돕는 비서다. 입력을 실행 가능한 항목으로 정리해 한국어로 간결히 답하라.';

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.ico': 'image/x-icon',
};

function sendJson(res, status, body) {
  const payload = JSON.stringify(body);
  res.writeHead(status, {
    'Content-Type': 'application/json; charset=utf-8',
    'Content-Length': Buffer.byteLength(payload),
  });
  res.end(payload);
}

async function handleChat(req, res) {
  if (!ENDPOINT || !API_KEY) {
    console.error('Azure OpenAI 설정 누락');
    return sendJson(res, 500, { error: '서버 설정 누락' });
  }

  let raw = '';
  for await (const chunk of req) {
    raw += chunk;
    if (raw.length > 1e6) {
      req.destroy();
      return;
    }
  }

  let message;
  try {
    ({ message } = JSON.parse(raw));
  } catch {
    return sendJson(res, 400, { error: '잘못된 JSON' });
  }
  if (!message || typeof message !== 'string') {
    return sendJson(res, 400, { error: 'message 필드가 필요합니다' });
  }

  const url =
    `${ENDPOINT.replace(/\/$/, '')}/openai/deployments/${DEPLOYMENT}` +
    `/chat/completions?api-version=${API_VERSION}`;

  let upstream;
  try {
    upstream = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'api-key': API_KEY },
      body: JSON.stringify({
        messages: [
          { role: 'system', content: SYSTEM_PROMPT },
          { role: 'user', content: message },
        ],
        // gpt-5 계열은 max_tokens를 거부한다. 또한 이 한도는 reasoning 토큰까지
        // 함께 소모하므로 너무 낮으면 본문이 빈 채로 200이 돌아온다.
        max_completion_tokens: 4000,
      }),
    });
  } catch (err) {
    console.error('모델 호출 실패:', err.message);
    return sendJson(res, 502, { error: '모델 호출 실패' });
  }

  if (!upstream.ok) {
    // 응답 본문에 자격증명이 섞일 수 있으므로 상태 코드만 남긴다.
    console.error('모델 응답 오류:', upstream.status);
    return sendJson(res, 502, { error: `모델 응답 오류 ${upstream.status}` });
  }

  const data = await upstream.json();
  sendJson(res, 200, { reply: data.choices?.[0]?.message?.content ?? '' });
}

function serveStatic(req, res) {
  const url = new URL(req.url, `http://${req.headers.host}`);
  const rel = url.pathname === '/' ? 'index.html' : url.pathname.slice(1);

  // 경로 이탈 차단: 해석된 절대경로가 프로젝트 루트 밖이면 거부한다.
  const root = __dirname;
  const target = path.resolve(root, rel);
  if (target !== root && !target.startsWith(root + path.sep)) {
    res.writeHead(403).end('Forbidden');
    return;
  }

  fs.readFile(target, (err, buf) => {
    if (err) {
      res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' }).end('Not Found');
      return;
    }
    res.writeHead(200, {
      'Content-Type': MIME[path.extname(target)] || 'application/octet-stream',
      'X-Content-Type-Options': 'nosniff',
      'Referrer-Policy': 'strict-origin-when-cross-origin',
    });
    res.end(buf);
  });
}

const server = http.createServer((req, res) => {
  const pathname = new URL(req.url, `http://${req.headers.host}`).pathname;

  if (pathname === '/healthz') {
    return sendJson(res, 200, { ok: true, deployment: DEPLOYMENT, configured: Boolean(ENDPOINT && API_KEY) });
  }
  if (pathname === '/api/chat') {
    if (req.method !== 'POST') return sendJson(res, 405, { error: 'POST만 허용' });
    return handleChat(req, res).catch((err) => {
      console.error('처리 중 예외:', err.message);
      sendJson(res, 500, { error: '서버 오류' });
    });
  }
  if (req.method !== 'GET') return sendJson(res, 405, { error: 'GET만 허용' });
  serveStatic(req, res);
});

server.listen(PORT, () => console.log(`righthon listening on ${PORT}`));
