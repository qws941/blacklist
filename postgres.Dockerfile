# 커스텀 PostgreSQL 이미지 - blacklist 프로젝트용
FROM postgres:15-alpine

# 필요한 패키지 설치
RUN apk add --no-cache curl

# 데이터베이스 초기화 스크립트 디렉토리 생성
RUN mkdir -p /docker-entrypoint-initdb.d

# 커스텀 초기화 스크립트 복사
COPY <<'EOF' /docker-entrypoint-initdb.d/01-init-blacklist.sql
-- Blacklist 프로젝트 데이터베이스 초기화
-- 모든 필수 테이블과 데이터 생성

-- 블랙리스트 IP 테이블
CREATE TABLE IF NOT EXISTS blacklist_ips (
    id SERIAL PRIMARY KEY,
    ip_address INET NOT NULL UNIQUE,
    reason TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(100) DEFAULT 'manual',
    confidence_level INTEGER DEFAULT 5,
    category VARCHAR(50) DEFAULT 'unknown',
    last_seen TIMESTAMP,
    detection_count INTEGER DEFAULT 1
);

-- 시스템 로그 테이블
CREATE TABLE IF NOT EXISTS system_logs (
    id SERIAL PRIMARY KEY,
    level VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(100),
    context JSONB,
    request_id VARCHAR(50),
    user_agent TEXT,
    ip_address INET
);

-- 모니터링 데이터 테이블
CREATE TABLE IF NOT EXISTS monitoring_data (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tags JSONB,
    numeric_value DECIMAL,
    unit VARCHAR(20),
    alert_threshold DECIMAL
);

-- API 키 관리 테이블
CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    key_name VARCHAR(100) NOT NULL UNIQUE,
    key_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP,
    permissions JSONB,
    rate_limit INTEGER DEFAULT 1000,
    expires_at TIMESTAMP
);

-- 수집 이력 테이블
CREATE TABLE IF NOT EXISTS collection_history (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(100) NOT NULL,
    collection_type VARCHAR(50),
    items_collected INTEGER DEFAULT 0,
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    execution_time_ms INTEGER,
    data_quality_score DECIMAL,
    next_collection TIMESTAMP
);

-- 사용자 활동 테이블
CREATE TABLE IF NOT EXISTS user_activities (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT,
    success BOOLEAN DEFAULT true
);

-- 알림 설정 테이블
CREATE TABLE IF NOT EXISTS notification_settings (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100),
    notification_type VARCHAR(50) NOT NULL,
    enabled BOOLEAN DEFAULT true,
    settings JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성 (성능 최적화)
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_active ON blacklist_ips(is_active);
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_created ON blacklist_ips(created_at);
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_source ON blacklist_ips(source);
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_category ON blacklist_ips(category);

CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp ON system_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(level);
CREATE INDEX IF NOT EXISTS idx_system_logs_source ON system_logs(source);

CREATE INDEX IF NOT EXISTS idx_monitoring_timestamp ON monitoring_data(timestamp);
CREATE INDEX IF NOT EXISTS idx_monitoring_metric ON monitoring_data(metric_name);

CREATE INDEX IF NOT EXISTS idx_collection_timestamp ON collection_history(timestamp);
CREATE INDEX IF NOT EXISTS idx_collection_source ON collection_history(source_name);
CREATE INDEX IF NOT EXISTS idx_collection_success ON collection_history(success);

CREATE INDEX IF NOT EXISTS idx_activities_timestamp ON user_activities(timestamp);
CREATE INDEX IF NOT EXISTS idx_activities_user ON user_activities(user_id);
CREATE INDEX IF NOT EXISTS idx_activities_action ON user_activities(action);

-- 기본 데이터 삽입
INSERT INTO system_logs (level, message, source) 
VALUES ('INFO', 'Database initialized with custom schema', 'postgres-init')
ON CONFLICT DO NOTHING;

INSERT INTO monitoring_data (metric_name, metric_value, numeric_value) 
VALUES 
    ('database_status', 'initialized', 1),
    ('schema_version', '1.0', 1.0),
    ('tables_count', '7', 7)
ON CONFLICT DO NOTHING;

INSERT INTO api_keys (key_name, key_hash, permissions, rate_limit) 
VALUES ('system_default', 'hashed_system_key', '{"read": true, "write": false}', 10000)
ON CONFLICT (key_name) DO NOTHING;

-- 샘플 블랙리스트 데이터 (테스트용)
INSERT INTO blacklist_ips (ip_address, reason, source, category, confidence_level) 
VALUES 
    ('192.168.1.100'::INET, 'Test IP for development', 'system', 'test', 1),
    ('10.0.0.1'::INET, 'Internal test IP', 'manual', 'test', 1)
ON CONFLICT (ip_address) DO NOTHING;

-- 데이터베이스 설정 최적화
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_min_duration_statement = 1000;

-- 권한 설정
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO postgres;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- 완료 메시지
DO $$
BEGIN
    RAISE NOTICE 'Blacklist database initialization completed successfully!';
    RAISE NOTICE 'Tables created: blacklist_ips, system_logs, monitoring_data, api_keys, collection_history, user_activities, notification_settings';
    RAISE NOTICE 'Sample data inserted for testing';
END $$;
EOF

# 헬스체크용 스크립트 추가
COPY <<'EOF' /usr/local/bin/pg_health_check.sh
#!/bin/sh
# PostgreSQL 헬스체크 스크립트
set -e

# 기본 연결 테스트
pg_isready -h localhost -p 5432 -U postgres

# 데이터베이스 접근 테스트
psql -U postgres -d blacklist -c "SELECT COUNT(*) FROM blacklist_ips;" > /dev/null

# 테이블 존재 확인
TABLES=$(psql -U postgres -d blacklist -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
if [ "$TABLES" -lt 7 ]; then
    echo "ERROR: Missing tables in blacklist database"
    exit 1
fi

echo "PostgreSQL health check passed - blacklist database ready"
EOF

RUN chmod +x /usr/local/bin/pg_health_check.sh

# 환경변수 설정
ENV POSTGRES_DB=blacklist
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=postgres

# 포트 노출
EXPOSE 5432

# 헬스체크 설정
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD /usr/local/bin/pg_health_check.sh

# 라벨 추가
LABEL com.blacklist.service="postgres" \
      com.blacklist.version="1.0" \
      com.blacklist.description="Custom PostgreSQL with blacklist schema"