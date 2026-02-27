# Codex CLI Handoff: Railway Auto-Deploy 검증 및 후속 작업

> **사용법**: 아래 프롬프트를 Codex CLI에서 그대로 붙여넣기
>
> ```bash
> cd /path/to/knowledge-copilot   # 또는 git clone 후 진입
> codex                            # Codex CLI 실행
> # 아래 프롬프트 붙여넣기
> ```

---

## Codex CLI 프롬프트

```
레포 doublesilver/knowledge-copilot의 CI/CD 파이프라인 검증 및 후속 작업을 수행해.
이 레포의 CODEX_HANDOFF.md에 전체 컨텍스트가 있으니 먼저 읽어.

## 컨텍스트 (빠른 요약)
- PR #8 (chore/railway-auto-deploy): Railway deploy hook/CLI 스텝 제거, Auto-deploy 전환
- Railway에 "Deploy Hook URL" 기능이 없어서, Railway의 GitHub Auto-deploy + Check Suites 사용
- GitHub Actions는 CI + Vercel 배포만 담당. Railway는 CI 통과 감지 후 자체 auto-deploy
- 프로젝트 구조: app/ (Next.js→Vercel), api/ (FastAPI→Railway)
- 삭제된 시크릿: RAILWAY_TOKEN, RAILWAY_SERVICE_NAME, RAILWAY_DEV_ENVIRONMENT
- 남은 시크릿: VERCEL_TOKEN, VERCEL_ORG_ID, VERCEL_PROJECT_ID, VERCEL_SCOPE

## Step 1: 검증 (순서대로 실행)

1-1. PR #8 CI 상태 확인
  gh pr view 8 --repo doublesilver/knowledge-copilot
  gh pr checks 8 --repo doublesilver/knowledge-copilot
  → CI 실패 시: gh run view <run-id> --log-failed 로 원인 분석하고 수정 커밋

1-2. 시크릿 확인
  gh secret list --repo doublesilver/knowledge-copilot
  → RAILWAY_* 시크릿이 0개여야 정상
  → VERCEL_* 시크릿 4개만 존재해야 함

1-3. 워크플로우 검증
  .github/workflows/ci-cd.yml 파일을 읽고:
  - railway, RAILWAY, deploy hook, curl.*railway 같은 Railway 관련 코드가 완전히 제거되었는지 grep
  - checks → deploy-development / deploy-production 의존관계(needs: checks) 정상인지 확인
  - Vercel 배포 스텝에 필요한 시크릿(VERCEL_TOKEN, VERCEL_SCOPE)이 참조되는지 확인

## Step 2: PR 머지 (검증 통과 시)

  gh pr merge 8 --repo doublesilver/knowledge-copilot --squash --delete-branch

## Step 3: dev 브랜치 동기화

  git checkout main && git pull origin main
  git checkout dev && git merge main && git push origin dev

## Step 4: 기존 불필요 브랜치 정리

아래 브랜치들을 리모트에서 삭제:
  git push origin --delete chore/railway-no-token-deploy 2>/dev/null || true
  git push origin --delete chore/refresh-secrets 2>/dev/null || true
  git push origin --delete chore/fix-vercel-deploy 2>/dev/null || true
  git push origin --delete chore/fix-vercel-deploy-flags 2>/dev/null || true

## Step 5: 배포 문서 업데이트

docs/DEPLOY_VERCEL_RAILWAY.md 파일이 있으면 아래 내용 반영:
- "Railway CLI 배포" 또는 "railway up" 관련 설명 → "Railway Auto-deploy (Check Suites)" 로 변경
- RAILWAY_TOKEN 관련 설명 제거
- 배포 플로우를 아래로 업데이트:
  push → GitHub Actions CI → Vercel deploy (FE) + Railway auto-deploy (BE, CI 통과 후)
- 변경 시 커밋: git add docs/ && git commit -m "docs: update deploy guide for Railway auto-deploy"
- git push origin dev

## Step 6: E2E 배포 검증

dev 브랜치에서 테스트:
1. gh run list --repo doublesilver/knowledge-copilot --branch dev --limit 3
   → 최근 CI가 통과했는지 확인
2. Railway 대시보드에서 dev 환경 배포 상태 확인 (자동화 불가, 사용자에게 안내)
3. API health check URL이 있으면 curl로 확인

## 수동 작업 안내 (사용자에게 출력)

아래는 Codex가 자동화할 수 없는 Railway 대시보드 설정이야.
사용자에게 아래 체크리스트를 출력해:

```
Railway 대시보드 수동 설정 체크리스트:
[ ] railway.com → knowledge-copilot 프로젝트 → API 서비스 → Settings
[ ] Source → Connect Repo: doublesilver/knowledge-copilot, Root: /api
[ ] Development 환경 → Branch: dev, Check Suites: ON
[ ] Production 환경 → Branch: main, Check Suites: ON
[ ] Railway GitHub App이 레포에 설치되어 있는지 확인
    (GitHub → Settings → Integrations → Railway 확인)
```

## 주의사항
- Railway 대시보드 설정(Check Suites)은 API/CLI로 자동화 불가. 반드시 수동
- PR 머지 전에 CI가 통과했는지 반드시 확인
- dev 브랜치 동기화 전에 main이 최신인지 확인
- CODEX_HANDOFF.md 파일은 모든 작업 완료 후 삭제해도 됨
```
