# Knowledge Copilot

이 프로젝트는 포트폴리오 목적의 **AI 문서 기반 지식 코파일럿**입니다.
- 문서 업로드 (텍스트)
- RAG 기반 검색 + 질의
- 근거(citation) 표시
- 액션형 기능 (문서 요약)
- 피드백/메트릭 집계

## 폴더 구성
- `api/`: FastAPI 백엔드
- `app/`: Next.js 프론트엔드
- `docs/`: 설계/로드맵 메모
- `docker-compose.yml`: 통합 실행 환경

## 빠른 시작

1. Python 의존성 설치
```bash
cd /mnt/c/Users/korea/project3/api
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

2. API 실행
```bash
cp ../.env.example ../.env   # 최초 1회만
uvicorn src.main:app --reload --env-file ../.env
```

3. 프론트 실행
```bash
cd ../app
npm install
npm run dev
```

4. 배포 환경 기준
- Frontend: Vercel
- Backend: Railway

> 실제 운영 배포에서는 Vercel/Railway 환경 변수에 `NEXT_PUBLIC_API_BASE`, `OPENAI_API_KEY` 등을 설정합니다.

5. 또는 Docker로 통합 실행
```bash
docker compose up --build
```

## 배포 플로우 (Git 기준)

### 브랜치 전략
- `dev` 또는 `development`: 개발/스테이징 배포 대상
- `main`: 실운영(Production) 배포 대상

### 배포 규칙
1. 로컬에서 코드 수정
2. `git add`, `git commit`, `git push`  
   - `dev` 브랜치에 push → 자동으로 **개발 배포** 실행
   - `main` 브랜치에 push → 자동으로 **실운영 배포** 실행
3. 실운영 배포는 개발 배포가 통과한 커밋만 머지 전제(`main` 머지/리뷰 정책을 이용)

### GitHub Actions 설정 항목
`Settings > Secrets and variables > Actions`에 아래 값이 있어야 합니다.
- `VERCEL_TOKEN`
- `VERCEL_ORG_ID`
- `VERCEL_PROJECT_ID`
- `RAILWAY_TOKEN`
- `RAILWAY_SERVICE_NAME`
- `RAILWAY_DEV_ENVIRONMENT`

### Vercel/배포 환경 대응
- Vercel은 기본적으로 브랜치별 Preview/Production 라우팅을 사용하도록 `.github/workflows/ci-cd.yml`에서 분기 처리
- Railway는 환경명을 `production` / `development`로 나눠 배포하도록 구성
- 배포 시점은 GitHub Push 이벤트 기준으로 자동 실행

## API
- `POST /api/v1/documents`: 문서 업로드
- `GET /api/v1/documents`: 문서 목록
- `GET /api/v1/documents/{id}`: 문서 상세
- `POST /api/v1/queries`: 질문 질의
- `GET /api/v1/queries/{id}`: 질의 상세
- `POST /api/v1/evals`: 질의 피드백
- `POST /api/v1/agent/actions`: 액션 실행
- `GET /api/v1/metrics`: 메트릭
- `GET /api/v1/health`: 상태 체크

## 운영 메모
- OpenAI API 키가 없을 경우 로컬 임베딩(데모 모드) 및 단순 응답 경로로 동작합니다.
- `CORS_ORIGINS`는 배포 환경에 맞춰 업데이트합니다.
- 배포 가이드는 [docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md)를 참고하세요.
