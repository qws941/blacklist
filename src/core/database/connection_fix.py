#!/usr/bin/env python3
"""
PostgreSQL 연결 개선 모듈 - 환경변수 기반 유연한 연결 설정
"""
import os
import psycopg2
from typing import Optional, Dict, Any
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class PostgreSQLConnectionManager:
    """PostgreSQL 연결 관리자 - 환경변수 기반 연결 설정"""

    def __init__(self):
        self.connection_params = self._get_connection_params()

    def _get_connection_params(self) -> Dict[str, Any]:
        """환경변수에서 PostgreSQL 연결 파라미터 추출"""
        # 여러 환경변수 형태 지원
        database_url = os.getenv("DATABASE_URL")
        postgres_url = os.getenv("POSTGRES_URL")

        # URL 형태로 제공된 경우 파싱
        if database_url or postgres_url:
            url = database_url or postgres_url
            parsed = urlparse(url)
            return {
                "host": parsed.hostname or "localhost",
                "port": parsed.port or 5432,
                "database": parsed.path.lstrip("/") or "blacklist",
                "user": parsed.username or "postgres",
                "password": parsed.password or "",
            }

        # 개별 환경변수에서 설정 추출
        return {
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": int(os.getenv("POSTGRES_PORT", "5432")),
            "database": os.getenv("POSTGRES_DB", "blacklist"),
            "user": os.getenv("POSTGRES_USER", "postgres"),
            "password": os.getenv("POSTGRES_PASSWORD", ""),
        }

    def get_connection(self) -> Optional[psycopg2.extensions.connection]:
        """PostgreSQL 연결 시도 (fallback 포함)"""
        hosts_to_try = [
            self.connection_params["host"],
            "blacklist-postgres",  # Docker 컨테이너명
            "postgres",  # 일반적인 서비스명
            "localhost",  # 로컬 fallback
        ]

        for host in hosts_to_try:
            try:
                params = self.connection_params.copy()
                params["host"] = host

                logger.info(f"PostgreSQL 연결 시도: {host}:{params['port']}")

                conn = psycopg2.connect(
                    host=params["host"],
                    port=params["port"],
                    database=params["database"],
                    user=params["user"],
                    password=params["password"],
                    connect_timeout=5,  # 5초 타임아웃
                )

                logger.info(f"PostgreSQL 연결 성공: {host}")
                return conn

            except Exception as e:
                logger.warning(f"PostgreSQL 연결 실패 ({host}): {e}")
                continue

        logger.error("모든 PostgreSQL 호스트 연결 실패")
        return None

    def get_stats_with_fallback(self) -> Dict[str, Any]:
        """PostgreSQL 통계 조회 (fallback 포함)"""
        conn = self.get_connection()
        if not conn:
            return {
                "status": "disconnected",
                "message": "PostgreSQL 연결 불가",
                "tables": 0,
                "connections": 0,
            }

        try:
            with conn.cursor() as cursor:
                # 테이블 수 조회
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """
                )
                table_count = cursor.fetchone()[0]

                # 활성 연결 수 조회
                cursor.execute("SELECT COUNT(*) FROM pg_stat_activity")
                connection_count = cursor.fetchone()[0]

                return {
                    "status": "connected",
                    "message": "PostgreSQL 연결 정상",
                    "tables": table_count,
                    "connections": connection_count,
                    "host": conn.get_dsn_parameters().get("host", "unknown"),
                }

        except Exception as e:
            logger.error(f"PostgreSQL 통계 조회 실패: {e}")
            return {
                "status": "error",
                "message": f"쿼리 실패: {str(e)}",
                "tables": 0,
                "connections": 0,
            }
        finally:
            if conn:
                conn.close()


# 전역 연결 관리자 인스턴스
connection_manager = PostgreSQLConnectionManager()


def get_postgres_stats():
    """PostgreSQL 통계 조회 - 개선된 버전"""
    return connection_manager.get_stats_with_fallback()


def test_connection():
    """연결 테스트"""
    conn = connection_manager.get_connection()
    if conn:
        conn.close()
        return True
    return False


if __name__ == "__main__":
    # 테스트 실행
    print("PostgreSQL 연결 테스트:")
    stats = get_postgres_stats()
    print(f"결과: {stats}")
