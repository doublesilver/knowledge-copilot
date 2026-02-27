# Deployment Guide (Vercel + Railway)

## Backend (Railway) - `api/`

1. Railway에서 GitHub 레포를 연동하고 루트 경로가 `api`가 되도록 설정하거나,
   `Dockerfile`이 있는 폴더를 지정합니다.
2. 환경변수 설정
- `OPENAI_API_KEY`
- `OPENAI_EMBEDDING_MODEL` (옵션, 기본: `text-embedding-3-small`)
- `OPENAI_CHAT_MODEL` (옵션, 기본: `gpt-4o-mini`)
- `OPENAI_REQUEST_TIMEOUT` (옵션, 기본: `30`)
- `CORS_ORIGINS` (예: `https://<your-vercel-app>.vercel.app`)
- `KNOWLEDGE_COPILOT_DATABASE_PATH` (옵션, 기본: `data/knowledge_copilot.db`)
3. 포트 확인: 기본 컨테이너 포트가 `8000`으로 동작합니다.
4. 배포 후 헬스체크: `GET /api/v1/health`

## Frontend (Vercel) - `app/`

1. Vercel에서 루트 디렉터리를 `app`으로 설정해 배포합니다.
2. 환경변수 설정
- `NEXT_PUBLIC_API_BASE=https://<your-railway-domain>`
3. Vercel에서는 `app/.env.local`이 아니라, **Project Settings의 Environment Variables**에 등록해야 합니다.
4. 본 레포지토리는 프론트 프로젝트 루트가 `app/`이므로, Vercel 프로젝트 Root Directory를 `app`으로 설정해야 합니다.

## Local dev

1. `.env.example`을 복사해 `.env`를 만들고 OpenAI 키를 채웁니다.
2. API 실행
- `cd api`
- `uvicorn src.main:app --reload --env-file ../.env`
3. 웹 실행
- `cd app`
- `npm install && npm run dev`
4. Docker 실행
- 프로젝트 루트에서 `docker compose up --build`

## Deployment preflight

로컬 `.env`의 값이 배포 기준을 충족하는지 미리 점검:

```bash
cd /path/to/project3
bash ./scripts/check-deploy-env.sh
```

확인 항목
- Railway API
  - `OPENAI_EMBEDDING_MODEL`, `OPENAI_CHAT_MODEL`, `OPENAI_REQUEST_TIMEOUT`, `CORS_ORIGINS`
- Vercel Web
- `NEXT_PUBLIC_API_BASE`
- 로컬 토큰 관리
  - `VERCEL_TOKEN`, `GITHUB_TOKEN` (로컬 용도)

## Git 기반 자동 배포 흐름

1. 코드 수정 후 commit
2. 브랜치 전략에 따라 push
- `dev`/`development` → 자동 개발 배포
- `main` → 자동 실운영 배포
3. 실운영 배포는 개발 배포가 통과된 커밋 기준으로 운영 브랜치에 반영 후 진행

`.github/workflows/ci-cd.yml`가 다음을 수행합니다.
- `app/` frontend build 점검
- `api/` backend 테스트 실행
- 브랜치별 자동 배포(Vercel + Railway)

### 필요한 GitHub Actions 시크릿
- `VERCEL_TOKEN`
- `VERCEL_SCOPE` (`doublesilvers-projects`)
- `RAILWAY_DEV_DEPLOY_HOOK`
- `RAILWAY_PROD_DEPLOY_HOOK`

현재 저장소 기준으로 확정된 값
- `VERCEL_SCOPE=doublesilvers-projects`

Railway 배포는 더 이상 CLI 토큰(`RAILWAY_TOKEN`)을 사용하지 않고, GitHub Actions에서 각 환경별 **Deploy Hook URL**(`RAILWAY_DEV_DEPLOY_HOOK`, `RAILWAY_PROD_DEPLOY_HOOK`)을 POST 호출해 트리거합니다.

참고: Deploy Hook URL은 Railway 프로젝트 Settings → Deployments → Deployment Hooks 에서 발급합니다.

## 운영 주의

- 이번 백엔드는 기본적으로 SQLite를 사용하므로 파일 DB가 컨테이너/빌드 재시작 시 초기화될 수 있습니다.
- 포트폴리오 데모는 가능하지만, 장기 운영/실서비스 목적이면 PostgreSQL 전환을 권장합니다.
