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
