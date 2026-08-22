# Python 배포 (`./deploy-py.sh`)

병목은 회선이 아니다. zip 앱 파일은 ~30KB. 느렸던 것:

1. `packages/` 없이 **매 배포 pip** (26MB wheel)
2. 배포를 **겹침** → B1 Kudu 8–10분 기동/503

## 한 번만

```bash
./deploy-py.sh          # 첫 실행: packages/ 조립 + zip + az
./deploy-py.sh          # 다음: reusing packages/ 후 바로 업로드
PACKAGES_REBUILD=1 ./deploy-py.sh   # wheel 바꿀 때만
```

- `packages/` gitignore. 노드마다 한 번.
- 이미 배포 중이면 스크립트가 거부한다. 기다렸다가 다시.
- `RuntimeSuccessful` ≠ 동작. `/healthz` + `/api/chat`까지.

Node 보험은 `./deploy.sh`. 이 스크립트는 `righthon-hale`을 안 건드린다.
