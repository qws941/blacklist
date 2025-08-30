#!/usr/bin/env python3
"""
인증 관리자 모듈
"""

import logging
import os
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class AuthManager:
    """인증 정보 관리 클래스"""

    def __init__(self):
        self.credentials_cache = {}

    def get_credentials(self, service: str) -> Optional[Dict[str, str]]:
        """서비스별 인증정보 반환"""
        try:
            # PostgreSQL에서 인증정보 조회
            import psycopg2
            from psycopg2.extras import RealDictCursor

            conn = psycopg2.connect(
                host=os.getenv("POSTGRES_HOST", "blacklist-postgres"),
                port=os.getenv("POSTGRES_PORT", "5432"),
                database=os.getenv("POSTGRES_DB", "blacklist"),
                user=os.getenv("POSTGRES_USER", "postgres"),
                password=os.getenv("POSTGRES_PASSWORD", "postgres"),
                cursor_factory=RealDictCursor,
            )
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT username, password 
                FROM collection_credentials 
                WHERE service_name = %s
                """,
                (service.upper(),),
            )
            result = cursor.fetchone()

            cursor.close()
            conn.close()

            if result:
                return {
                    "username": result["username"] or "",
                    "password": result["password"] or "",
                }
            else:
                logger.warning(f"No credentials found for service: {service}")
                return None

        except Exception as e:
            logger.error(f"Failed to get credentials for {service}: {e}")
            # Fallback to environment variables
            username = os.getenv(f"{service.upper()}_USERNAME")
            password = os.getenv(f"{service.upper()}_PASSWORD")

            if username and password:
                return {"username": username, "password": password}
            return None


# Global auth manager instance
_auth_manager = None


def get_auth_manager() -> AuthManager:
    """전역 인증 관리자 인스턴스 반환"""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
    return _auth_manager
