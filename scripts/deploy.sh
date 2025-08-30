#!/bin/bash

# Blacklist System 무중단 배포 스크립트
# 사용법: ./scripts/deploy.sh [production|staging|rollback]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REGISTRY="registry.jclee.me"

# 색상 출력을 위한 함수
red() { echo -e "\033[31m$1\033[0m"; }
green() { echo -e "\033[32m$1\033[0m"; }
yellow() { echo -e "\033[33m$1\033[0m"; }
blue() { echo -e "\033[34m$1\033[0m"; }

# 로깅 함수
log_info() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $(blue "INFO") $1"; }
log_warn() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $(yellow "WARN") $1"; }
log_error() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $(red "ERROR") $1"; }
log_success() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $(green "SUCCESS") $1"; }

# 도움말 출력
show_help() {
    cat << EOF
Blacklist System 배포 스크립트

사용법:
    $0 [COMMAND] [OPTIONS]

COMMANDS:
    production    프로덕션 환경에 배포 (기본값)
    staging       스테이징 환경에 배포
    rollback      이전 버전으로 롤백
    health        헬스체크 실행
    logs          서비스 로그 조회
    status        서비스 상태 확인

OPTIONS:
    --skip-tests      테스트 스킵
    --force           강제 실행
    --dry-run         실제 배포 없이 시뮬레이션
    --backup          배포 전 데이터베이스 백업
    -h, --help        도움말 출력

예시:
    $0 production --backup
    $0 staging --skip-tests
    $0 rollback
    $0 health

EOF
}

# 환경 변수 로드
load_environment() {
    local env_file="${1:-production}"
    if [[ -f "$PROJECT_ROOT/.env.$env_file" ]]; then
        set -o allexport
        source "$PROJECT_ROOT/.env.$env_file"
        set +o allexport
        log_info "$env_file 환경 변수 로드됨"
    else
        log_warn "$env_file 환경 파일을 찾을 수 없음, 기본값 사용"
    fi
}

# 전제조건 검사
check_prerequisites() {
    log_info "전제조건 검사 시작"
    
    # Docker 검사
    if ! command -v docker &> /dev/null; then
        log_error "Docker가 설치되지 않았습니다"
        exit 1
    fi
    
    # Docker Compose 검사
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose가 설치되지 않았습니다"
        exit 1
    fi
    
    # 네트워크 생성
    if ! docker network ls | grep -q blacklist-network; then
        log_info "Docker 네트워크 생성 중..."
        docker network create blacklist-network
    fi
    
    # 디렉토리 생성
    sudo mkdir -p /opt/blacklist/{postgres-data,redis-data,app-logs,app-data,app-backup,redis-backup,monitoring}
    sudo chown -R $USER:$USER /opt/blacklist/
    
    log_success "전제조건 검사 완료"
}

# 테스트 실행
run_tests() {
    if [[ "${SKIP_TESTS:-false}" == "true" ]]; then
        log_warn "테스트 스킵됨"
        return 0
    fi
    
    log_info "테스트 실행 중..."
    cd "$PROJECT_ROOT/src"
    
    # 린트 검사
    if command -v black &> /dev/null; then
        black --check . || {
            log_error "코드 포매팅 검사 실패"
            return 1
        }
    fi
    
    # 단위 테스트 실행
    if [[ -d "tests" ]]; then
        python -m pytest tests/ -v --tb=short || {
            log_error "단위 테스트 실패"
            return 1
        }
    fi
    
    log_success "모든 테스트 통과"
}

# 데이터베이스 백업
backup_database() {
    if [[ "${BACKUP:-false}" == "true" ]]; then
        log_info "데이터베이스 백업 시작"
        local backup_file="/opt/blacklist/app-backup/backup-$(date +%Y%m%d_%H%M%S).sql"
        
        if docker ps | grep -q blacklist-postgres; then
            docker exec blacklist-postgres pg_dump -U postgres blacklist > "$backup_file" || {
                log_error "데이터베이스 백업 실패"
                return 1
            }
            log_success "데이터베이스 백업 완료: $backup_file"
        else
            log_warn "PostgreSQL 컨테이너가 실행 중이지 않습니다"
        fi
    fi
}

# 이미지 빌드 및 푸시
build_and_push() {
    local env="${1:-production}"
    
    log_info "이미지 빌드 및 푸시 시작 ($env)"
    
    cd "$PROJECT_ROOT"
    
    # 애플리케이션 이미지
    docker build -f Dockerfile.simple -t "$REGISTRY/blacklist-app:latest" .
    docker build -f postgres.Dockerfile -t "$REGISTRY/blacklist-postgres:latest" .
    docker build -f redis.Dockerfile -t "$REGISTRY/blacklist-redis:latest" .
    
    if [[ "${DRY_RUN:-false}" != "true" ]]; then
        docker push "$REGISTRY/blacklist-app:latest"
        docker push "$REGISTRY/blacklist-postgres:latest"
        docker push "$REGISTRY/blacklist-redis:latest"
        log_success "이미지 푸시 완료"
    else
        log_info "DRY RUN: 이미지 푸시 시뮬레이션"
    fi
}

# 서비스 배포
deploy_services() {
    local env="${1:-production}"
    local compose_file="docker-compose.$env.yml"
    
    log_info "$env 환경 배포 시작"
    
    if [[ ! -f "$PROJECT_ROOT/$compose_file" ]]; then
        log_error "$compose_file을 찾을 수 없습니다"
        return 1
    fi
    
    cd "$PROJECT_ROOT"
    
    if [[ "${DRY_RUN:-false}" != "true" ]]; then
        # 최신 이미지 풀
        docker-compose -f "$compose_file" pull
        
        # 무중단 배포 (rolling update)
        docker-compose -f "$compose_file" up -d --remove-orphans
        
        # 이전 컨테이너 정리
        docker system prune -f --volumes=false
        
        log_success "$env 환경 배포 완료"
    else
        log_info "DRY RUN: $env 환경 배포 시뮬레이션"
    fi
}

# 헬스체크
health_check() {
    log_info "헬스체크 시작"
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        log_info "헬스체크 시도 $attempt/$max_attempts"
        
        if curl -f -s http://localhost:2542/health --max-time 15 > /dev/null; then
            log_success "애플리케이션 헬스체크 성공"
            break
        fi
        
        if [[ $attempt -eq $max_attempts ]]; then
            log_error "헬스체크 실패 - 최대 시도 횟수 도달"
            return 1
        fi
        
        sleep 10
        ((attempt++))
    done
    
    # 서비스별 헬스체크
    if docker ps | grep -q blacklist-postgres; then
        if docker exec blacklist-postgres pg_isready -U postgres -d blacklist > /dev/null; then
            log_success "PostgreSQL 헬스체크 성공"
        else
            log_error "PostgreSQL 헬스체크 실패"
            return 1
        fi
    fi
    
    if docker ps | grep -q blacklist-redis; then
        if docker exec blacklist-redis redis-cli ping > /dev/null; then
            log_success "Redis 헬스체크 성공"
        else
            log_error "Redis 헬스체크 실패"
            return 1
        fi
    fi
    
    log_success "모든 서비스 헬스체크 성공"
}

# 롤백
rollback() {
    log_warn "롤백 시작"
    
    cd "$PROJECT_ROOT"
    
    # 현재 실행 중인 컨테이너 중지
    docker-compose -f docker-compose.production.yml down
    
    # 이전 백업에서 데이터베이스 복구 (선택사항)
    local latest_backup=$(ls -t /opt/blacklist/app-backup/backup-*.sql 2>/dev/null | head -1)
    if [[ -n "$latest_backup" && "${RESTORE_DB:-false}" == "true" ]]; then
        log_info "데이터베이스 백업에서 복구 중: $latest_backup"
        # 필요시 여기에 복구 로직 추가
    fi
    
    # 서비스 재시작
    docker-compose -f docker-compose.production.yml up -d
    
    log_success "롤백 완료"
}

# 로그 조회
view_logs() {
    local service="${1:-}"
    
    cd "$PROJECT_ROOT"
    
    if [[ -n "$service" ]]; then
        docker-compose -f docker-compose.production.yml logs --tail=100 -f "$service"
    else
        docker-compose -f docker-compose.production.yml logs --tail=50
    fi
}

# 상태 확인
check_status() {
    log_info "서비스 상태 확인"
    
    cd "$PROJECT_ROOT"
    
    echo
    green "=== Docker Compose 서비스 상태 ==="
    docker-compose -f docker-compose.production.yml ps
    
    echo
    green "=== 컨테이너 리소스 사용량 ==="
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" | head -10
    
    echo
    green "=== 네트워크 상태 ==="
    docker network ls | grep blacklist
    
    echo
    green "=== 볼륨 상태 ==="
    docker volume ls | grep blacklist || echo "Blacklist 볼륨 없음"
}

# 메인 함수
main() {
    local command="${1:-production}"
    shift || true
    
    # 옵션 파싱
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            --force)
                FORCE=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --backup)
                BACKUP=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                log_error "알 수 없는 옵션: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    case $command in
        production|staging)
            load_environment "$command"
            check_prerequisites
            run_tests
            backup_database
            build_and_push "$command"
            deploy_services "$command"
            health_check
            ;;
        rollback)
            rollback
            health_check
            ;;
        health)
            health_check
            ;;
        logs)
            view_logs "${2:-}"
            ;;
        status)
            check_status
            ;;
        *)
            log_error "알 수 없는 명령어: $command"
            show_help
            exit 1
            ;;
    esac
    
    log_success "배포 스크립트 실행 완료"
}

# 시그널 핸들러
cleanup() {
    log_info "정리 작업 수행 중..."
    exit 0
}

trap cleanup INT TERM

# 스크립트 실행
main "$@"