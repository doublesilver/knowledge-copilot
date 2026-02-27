# Codex Handoff: Railway Auto-Deploy 검증 및 후속 작업

## 현재 상태
- **PR**: https://github.com/doublesilver/knowledge-copilot/pull/8
- **브랜치**: `chore/railway-auto-deploy` (base: `main`)
- **변경 내용**: Railway deploy hook/CLI 스텝 제거, GitHub Auto-deploy 전략으로 전환
- **삭제된 시크릿**: `RAILWAY_TOKEN`, `RAILWAY_SERVICE_NAME`, `RAILWAY_DEV_ENVIRONMENT`
- **남은 시크릿**: `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`, `VERCEL_SCOPE`

## 아키텍처
```
doublesilver/knowledge-copilot
├── app/          # Next.js frontend → Vercel (GitHub Actions에서 배포)
├── api/          # Python FastAPI backend → Railway (auto-deploy)
└── .github/workflows/ci-cd.yml
```

### 배포 플로우 (변경 후)
```
push to dev/main
  → GitHub Actions: checks job (FE build + BE test)
  → GitHub Actions: Vercel deploy (FE)
  → Railway: auto-deploy (BE) — CI 통과 후 자동 (Check Suites)
```

---

## Codex 프롬프트 (복사해서 사용)

```
너는 doublesilver/knowledge-copilot 프로젝트의 CI/CD 파이프라인을 검증하고 후속 작업을 수행해야 한다.

## 배경
- PR #8 (chore/railway-auto-deploy)에서 Railway deploy hook 스텝을 제거하고
  Railway의 GitHub Auto-deploy + Check Suites 방식으로 전환함
- Railway에는 "Deploy Hook URL" 기능이 존재하지 않음 (feature request 상태)
- GitHub Actions는 CI 검증 + Vercel 배포만 담당, Railway 배포는 Railway가 자체 처리

## 검증 체크리스트

### 1. PR 상태 확인
gh pr view 8 --repo doublesilver/knowledge-copilot
- CI checks가 통과했는지 확인
- 실패 시 로그를 분석하고 수정

### 2. GitHub secrets 확인
gh secret list --repo doublesilver/knowledge-copilot
- RAILWAY_* 시크릿이 없어야 함 (이미 삭제됨)
- Vercel 시크릿 4개만 존재해야 함: VERCEL_TOKEN, VERCEL_ORG_ID, VERCEL_PROJECT_ID, VERCEL_SCOPE

### 3. 워크플로우 문법 검증
.github/workflows/ci-cd.yml 파일을 읽고:
- YAML 문법 오류 없는지 확인
- checks → deploy-development / deploy-production 의존 관계 정상인지 확인
- Railway 관련 스텝이 완전히 제거되었는지 확인 (curl, railway CLI 호출 없어야 함)
- Vercel 배포 스텝이 정상 동작할 수 있는지 확인

### 4. Railway 대시보드 설정 안내 (자동화 불가, 수동 필요)
사용자에게 아래 Railway 대시보드 설정을 안내:

a) railway.com → knowledge-copilot 프로젝트 → API 서비스 클릭
b) Settings → Source 섹션:
   - Connect Repo: doublesilver/knowledge-copilot
   - Root Directory: /api
c) Development 환경:
   - Branch: dev
   - Check Suites: ON (활성화)
d) Production 환경:
   - Branch: main
   - Check Suites: ON (활성화)

### 5. PR 머지 판단
- CI 통과 + 검증 완료 시 PR 머지 추천 여부를 판단
- 머지 후 main에서 Railway auto-deploy가 트리거되는지 확인

## 후속 작업 (선택)

### A. dev 브랜치 동기화
PR이 main에 머지된 후:
git checkout dev && git merge main && git push origin dev
→ dev 환경도 auto-deploy 트리거됨

### B. 기존 deploy hook 브랜치 정리
chore/railway-no-token-deploy 브랜치 삭제:
gh api repos/doublesilver/knowledge-copilot/git/refs/heads/chore/railway-no-token-deploy -X DELETE
gh api repos/doublesilver/knowledge-copilot/git/refs/heads/chore/refresh-secrets -X DELETE
gh api repos/doublesilver/knowledge-copilot/git/refs/heads/chore/fix-vercel-deploy -X DELETE
gh api repos/doublesilver/knowledge-copilot/git/refs/heads/chore/fix-vercel-deploy-flags -X DELETE

### C. E2E 배포 검증
dev 브랜치에 테스트 커밋을 push하고:
1. GitHub Actions CI가 통과하는지 확인
2. Railway가 자동 배포하는지 확인 (Railway 대시보드에서 deployment 상태 확인)
3. API health check: curl https://<railway-url>/api/v1/health

### D. README 업데이트
배포 방식 변경을 README나 docs/DEPLOY_VERCEL_RAILWAY.md에 반영:
- "Railway CLI 배포" → "Railway Auto-deploy (Check Suites)"
- RAILWAY_TOKEN 관련 설명 제거
- 새 배포 플로우 다이어그램 추가

## 주의사항
- Railway 대시보드 설정(Check Suites 활성화)은 CLI/API로 자동화 불가 — 반드시 수동
- Vercel 배포는 기존과 동일하게 GitHub Actions에서 처리
- Railway auto-deploy는 GitHub push webhook을 기반으로 작동하므로
  Railway GitHub App이 레포에 설치되어 있어야 함
```

---

## 빠른 검증 명령어
```bash
# PR 상태
gh pr view 8 --repo doublesilver/knowledge-copilot

# CI 실행 상태
gh run list --repo doublesilver/knowledge-copilot --limit 5

# 시크릿 확인
gh secret list --repo doublesilver/knowledge-copilot

# 워크플로우 문법 검증 (act 사용 시)
act -n --workflows .github/workflows/ci-cd.yml
```
