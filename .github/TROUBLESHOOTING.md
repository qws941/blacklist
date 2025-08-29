# 🔧 CI/CD Pipeline Troubleshooting Guide

이 가이드는 CI/CD 파이프라인에서 발생할 수 있는 문제들과 해결 방법을 제공합니다.

## 🚨 Common Issues & Solutions

### 1. 🔐 Registry Authentication Failures

**문제:** `Password required` 오류 발생
```
Error: Password required
build-images (app, Dockerfile, ., true): .github#12
```

**해결방법:**
1. GitHub Repository → Settings → Secrets and variables → Actions
2. `REGISTRY_PASSWORD` secret 추가: 값은 `bingogo1`
3. Secret 이름이 정확한지 확인 (대소문자 구분)

**테스트:**
```bash
# 로컬에서 레지스트리 접근 테스트
docker login registry.jclee.me -u admin -p bingogo1
```

### 2. 📝 GitHub Token Permission Issues

**문제:** `Permission to qws941/blacklist.git denied to github-actions[bot]`
```
remote: Permission to qws941/blacklist.git denied to github-actions[bot].
fatal: unable to access 'https://github.com/qws941/blacklist/': The requested URL returned error: 403
```

**해결방법:**
1. Repository Settings → Actions → General
2. "Workflow permissions" 섹션에서 "Read and write permissions" 선택
3. "Allow GitHub Actions to create and approve pull requests" 체크박스 활성화

**또는 SHA-based workflow 사용:**
- 새로 추가된 `sha-based-version.yml`은 커밋 없이 버전 관리

### 3. 🏷️ Version Calculation Issues

**문제:** 빈 버전 값 생성 (`echo "" > VERSION`)

**해결방법:**
SHA-based 워크플로우를 사용하여 더 안정적인 버전 관리:
- 커밋 SHA + 시맨틱 버전 + 빌드 번호 조합
- Git 히스토리에 의존하지 않는 독립적 버전 생성

### 4. 🐳 Docker Build Failures

**문제:** Dockerfile을 찾을 수 없거나 빌드 실패

**해결방법:**
```bash
# 로컬에서 Docker 파일 검증
docker build -f Dockerfile -t test-app .
docker build -f postgres.Dockerfile -t test-postgres .  
docker build -f redis.Dockerfile -t test-redis .
```

**체크리스트:**
- [ ] 모든 Dockerfile이 repository root에 있는가?
- [ ] Dockerfile 이름이 정확한가? (`Dockerfile`, `postgres.Dockerfile`, `redis.Dockerfile`)
- [ ] 필요한 소스 파일들이 모두 커밋되었는가?

### 5. 🔍 Change Detection Issues

**문제:** 변경사항이 감지되지 않거나 불필요한 빌드 트리거

**해결방법:**
paths-filter 설정 확인:
```yaml
paths:
  - 'src/**'
  - 'Dockerfile*'  
  - 'docker-compose*.yml'
  - 'requirements.txt'
  - '.github/workflows/**'
```

**테스트:**
```bash
# 최근 커밋에서 변경된 파일 확인
git diff --name-only HEAD~1
```

## 📊 Expected Results Analysis

### ✅ 성공 시나리오

**Normal Flow:**
1. **코드 변경사항 푸시**
2. **워크플로우 자동 트리거**
3. **변경사항 감지 및 버전 계산**
4. **멀티 이미지 병렬 빌드**
5. **프라이빗 레지스트리 푸시**
6. **보안 스캔 및 테스트**
7. **GitHub Release 생성**

**Expected Outputs:**
- ✅ 3개 Docker 이미지가 성공적으로 빌드 및 푸시됨
- ✅ 새로운 버전이 계산되고 태깅됨  
- ✅ GitHub Release가 자동 생성됨
- ✅ 모든 보안 스캔 통과

### ❌ 실패 시나리오 & 해결

**Current Issues Observed:**

1. **Registry Authentication → Secret 설정 필요**
2. **GitHub Permissions → Repository 설정 변경 필요**  
3. **Version Calculation → SHA-based 워크플로우 사용**

## 🛠️ Debug Tools

### 1. GitHub Actions Debugging

**로그 확인:**
```bash
# 최신 실행 상태 확인
gh run list --limit 5

# 특정 실행의 상세 로그
gh run view <run-id> --log-failed

# 워크플로우 재실행
gh run rerun <run-id>
```

### 2. Local Testing

**Version Script 테스트:**
```bash
# 동적 버전 계산 테스트
python3 scripts/version/dynamic-version.py --get-version

# 빌드 메타데이터 생성 테스트  
./scripts/version/generate-build-metadata.sh

# 전체 파이프라인 검증
./scripts/validate-cicd-setup.sh
```

**Docker 빌드 테스트:**
```bash
# 각 이미지별 빌드 테스트
docker build -f Dockerfile -t blacklist-app:test .
docker build -f postgres.Dockerfile -t blacklist-postgres:test .
docker build -f redis.Dockerfile -t blacklist-redis:test .
```

### 3. Registry Testing

**프라이빗 레지스트리 연결 테스트:**
```bash
# 로그인 테스트
docker login registry.jclee.me -u admin -p bingogo1

# 이미지 푸시 테스트
docker tag blacklist-app:test registry.jclee.me/blacklist-app:test
docker push registry.jclee.me/blacklist-app:test

# 이미지 풀 테스트  
docker pull registry.jclee.me/blacklist-app:test
```

## 🚀 Recommended Workflows

### 1. SHA-based Version Management (추천)

새로 추가된 `sha-based-version.yml` 사용:
- ✅ 커밋 없이 버전 관리
- ✅ SHA + 시맨틱 버전 + 빌드 번호 조합
- ✅ 권한 문제 회피
- ✅ 더 안정적인 버전 계산

### 2. Manual Secret Configuration

GitHub Repository에서 반드시 설정해야 할 Secrets:
```
REGISTRY_PASSWORD = bingogo1
```

### 3. Repository Permissions

Settings → Actions → General → Workflow permissions:
- [x] Read and write permissions
- [x] Allow GitHub Actions to create and approve pull requests

## 🔄 Testing Strategy

### Phase 1: Basic Setup
1. [ ] GitHub Secrets 설정
2. [ ] Repository 권한 설정  
3. [ ] SHA-based workflow 테스트

### Phase 2: Build Validation
1. [ ] 단일 이미지 빌드 테스트
2. [ ] 멀티 이미지 병렬 빌드 테스트
3. [ ] 레지스트리 푸시 테스트

### Phase 3: Full Pipeline
1. [ ] 전체 CI/CD 파이프라인 실행
2. [ ] 자동 릴리스 생성 확인
3. [ ] 보안 스캔 결과 확인

## 📞 Support & Resources

- **GitHub Actions 로그**: Repository → Actions 탭
- **Docker Registry**: https://registry.jclee.me
- **Setup Guide**: `.github/SETUP-SECRETS.md`
- **Validation Script**: `./scripts/validate-cicd-setup.sh`

---

💡 **Pro Tip**: SHA-based workflow를 먼저 테스트해보세요. 더 안정적이고 권한 문제가 적습니다!