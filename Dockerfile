# Blacklist 애플리케이션 - 단순화된 버전 (DB 초기화 제거)
FROM python:3.11-slim

# 시스템 패키지 업데이트 및 필수 도구 설치
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    postgresql-client \
    redis-tools \
    jq \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# 사용자 생성 (보안 향상)
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# 로그 디렉토리 생성 및 권한 설정
RUN mkdir -p /app/logs /app/src/logs /app/instance /app/data && \
    chmod 755 /app/logs /app/src/logs /app/instance /app/data && \
    chown -R appuser:appgroup /app

# Python 의존성 파일 복사 및 설치
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 추가 패키지 설치 (PostgreSQL, Redis 연결용)
RUN pip install --no-cache-dir psycopg2-binary redis python-dotenv

# 애플리케이션 소스 코드 복사 (전체 디렉토리 구조 유지)
COPY src/ /app/src/
COPY main.py /app/main.py
COPY instance/ /app/instance/

# 모니터링 대시보드 복사
COPY monitoring-dashboard.html /app/monitoring-dashboard.html

# collection_api.py가 확실히 복사되도록 명시적으로 추가
RUN ls -la /app/src/core/routes/ || echo "Routes directory check"

# 헬스체크 스크립트 추가 (단순화)
COPY <<'EOF' /app/health_check.py
#!/usr/bin/env python3
import requests
import sys
import os

def health_check():
    try:
        port = os.getenv('PORT', '2542')
        response = requests.get(f'http://localhost:{port}/health', timeout=10)
        if response.status_code == 200:
            print("✅ Health check passed")
            sys.exit(0)
        else:
            print(f"❌ Health check failed: {response.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Health check error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    health_check()
EOF

RUN chmod +x /app/health_check.py

# 환경변수 설정
ENV FLASK_ENV=production
ENV PYTHONPATH=/app
ENV PORT=2542
ENV POSTGRES_HOST=blacklist-postgres
ENV POSTGRES_PORT=5432
ENV POSTGRES_DB=blacklist
ENV POSTGRES_USER=postgres

# 권한 설정
RUN chown -R appuser:appgroup /app
USER appuser

# 포트 노출
EXPOSE 2542

# 헬스체크 설정
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python /app/health_check.py

# 애플리케이션 실행 (단순화 - DB 초기화 제거)
CMD ["python", "/app/main.py"]