# 🔐 GitHub Secrets Setup Guide

CI/CD 파이프라인이 올바르게 작동하려면 다음 GitHub Secrets를 설정해야 합니다.

## 📋 Required Secrets

### 1. 프라이빗 레지스트리 인증
GitHub Repository Settings → Secrets and variables → Actions → New repository secret

```
REGISTRY_PASSWORD = bingogo1
```

**설명:** registry.jclee.me 프라이빗 레지스트리 접근을 위한 비밀번호

### 2. GitHub Token (자동 생성됨)
```
GITHUB_TOKEN = <자동으로 생성됨>
```

**설명:** GitHub Actions가 자동으로 제공하는 토큰 (별도 설정 불필요)

## 🔧 설정 방법

### Step 1: GitHub Repository에서 설정

1. GitHub Repository 페이지로 이동
2. **Settings** 탭 클릭
3. 좌측 메뉴에서 **Secrets and variables** → **Actions** 클릭
4. **New repository secret** 버튼 클릭

### Step 2: REGISTRY_PASSWORD 추가

- **Name:** `REGISTRY_PASSWORD`
- **Value:** `bingogo1`
- **Add secret** 버튼 클릭

## 🧪 테스트 방법

Secrets 설정이 완료된 후 다음 방법으로 테스트할 수 있습니다:

### 1. Manual Workflow Trigger
```bash
# GitHub Actions 탭에서 "Advanced Multi-Image CI/CD Pipeline" 워크플로우 실행
# 또는 다음 명령으로 Push 트리거
git commit --allow-empty -m "test: trigger CI/CD pipeline"
git push
```

### 2. 로컬에서 레지스트리 접근 테스트
```bash
# Docker 로그인 테스트
docker login registry.jclee.me -u admin -p bingogo1

# 이미지 풀 테스트
docker pull registry.jclee.me/blacklist-app:latest
```

## 🚀 Automatic Version Management

버전 관리는 다음 규칙에 따라 자동으로 수행됩니다:

### Commit Message 기반 버전 증가

| Commit Type | Version Bump | Example |
|-------------|--------------|---------|
| `BREAKING CHANGE` | Major (1.0.0 → 2.0.0) | `feat!: redesign API` |
| `feat:` | Minor (1.0.0 → 1.1.0) | `feat: add new endpoint` |
| `fix:` | Patch (1.0.0 → 1.0.1) | `fix: resolve bug` |
| `chore:`, `docs:` | Patch (1.0.0 → 1.0.1) | `chore: update deps` |

### Manual Version Control

GitHub Actions에서 수동으로 버전을 제어할 수도 있습니다:

1. Actions 탭 → "Dynamic Version Management" 워크플로우
2. "Run workflow" 클릭
3. 원하는 버전 타입 선택 (patch/minor/major)

## 🐳 Multi-Image Building

파이프라인은 다음 이미지들을 자동으로 빌드하고 푸시합니다:

- `registry.jclee.me/blacklist-app:latest`
- `registry.jclee.me/blacklist-postgres:latest`
- `registry.jclee.me/blacklist-redis:latest`

각 이미지는 다음 태그를 가집니다:
- `latest`
- `{version}` (예: 1.2.3)
- `{version}-{commit}` (예: 1.2.3-abc1234)
- `build-{build_number}` (예: build-123)

## 🔍 변경사항 감지

파이프라인은 다음 경로의 변경사항을 감지하여 조건부로 빌드합니다:

```yaml
paths:
  - 'src/**'
  - 'Dockerfile*'
  - 'docker-compose*.yml'
  - 'requirements.txt'
  - 'VERSION'
  - '.github/workflows/**'
```

## 🛡️ Security Features

- **Non-root 컨테이너:** 모든 이미지는 non-root 사용자로 실행
- **보안 스캔:** Trivy를 사용한 취약점 스캔
- **Multi-stage 빌드:** 최적화된 이미지 크기
- **Health checks:** 모든 서비스에 헬스체크 구현

## 📊 모니터링 및 로깅

빌드 과정의 모든 메타데이터가 아티팩트로 저장됩니다:

- `build-metadata/` - 전체 빌드 메타데이터
- `version-info.json` - 버전 정보
- `git-info.json` - Git 메타데이터
- `docker-info.json` - Docker 이미지 정보

## ❗ 트러블슈팅

### 1. Registry 인증 실패
```
Error: authentication required
```
**해결방법:** REGISTRY_PASSWORD secret이 올바르게 설정되었는지 확인

### 2. 버전 계산 오류
```
Error: Unable to calculate version
```
**해결방법:** Git 히스토리가 완전한지 확인 (shallow clone 아닌지)

### 3. Docker 빌드 실패
```
Error: Dockerfile not found
```
**해결방법:** 필요한 Dockerfile들이 모두 커밋되었는지 확인

## 📞 지원

문제가 발생하면 다음을 확인하세요:

1. GitHub Actions 로그에서 상세한 오류 메시지 확인
2. Secrets 설정이 올바른지 확인
3. Docker 파일들이 모두 존재하는지 확인
4. Git 히스토리가 완전한지 확인

## 🎯 성공 지표

올바르게 설정되면 다음을 확인할 수 있습니다:

- ✅ GitHub Actions가 성공적으로 실행됨
- ✅ 새로운 버전이 자동으로 계산됨
- ✅ 모든 Docker 이미지가 빌드되고 푸시됨
- ✅ GitHub Release가 자동으로 생성됨
- ✅ Docker Compose 파일이 새 버전으로 업데이트됨