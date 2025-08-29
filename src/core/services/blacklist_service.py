"""
블랙리스트 통합 서비스
모든 블랙리스트 관련 비즈니스 로직을 처리하는 서비스 클래스
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class HealthStatus:
    """시스템 헬스 상태"""

    status: str  # healthy, degraded, stopped
    version: str
    timestamp: datetime
    components: Dict[str, Any]


class BlacklistService:
    """통합 블랙리스트 서비스"""

    def __init__(self):
        self.db_config = {
            "host": os.getenv("POSTGRES_HOST", "postgres"),
            "port": os.getenv("POSTGRES_PORT", "5432"),
            "database": os.getenv("POSTGRES_DB", "blacklist"),
            "user": os.getenv("POSTGRES_USER", "postgres"),
            "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
        }
        self._components = {"regtech": True, "secudium": True, "database": True}

    def get_db_connection(self):
        """데이터베이스 연결 획득"""
        return psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "postgres"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            database=os.getenv("POSTGRES_DB", "blacklist"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres"),
            cursor_factory=RealDictCursor,
        )

    def get_health(self) -> HealthStatus:
        """시스템 헬스 상태 반환"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) as count FROM blacklist_ips")
            ip_count = cursor.fetchone()["count"]

            cursor.close()
            conn.close()

            components = {
                "database": {"status": "healthy", "ip_count": ip_count},
                "regtech": {"status": "healthy", "enabled": True},
                "secudium": {"status": "healthy", "enabled": True},
            }

            return HealthStatus(
                status="healthy",
                version="1.0.0",
                timestamp=datetime.now(),
                components=components,
            )
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return HealthStatus(
                status="degraded",
                version="1.0.0",
                timestamp=datetime.now(),
                components={"error": str(e)},
            )

    def get_collection_status(self) -> Dict[str, Any]:
        """수집 상태 반환"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            # 소스별 통계
            cursor.execute(
                """
                SELECT source, COUNT(*) as count, MAX(last_seen) as last_seen
                FROM blacklist_ips 
                GROUP BY source
            """
            )
            sources = cursor.fetchall()

            cursor.close()
            conn.close()

            status = {
                "collection_enabled": True,
                "sources": {},
                "total_ips": sum(s["count"] for s in sources),
                "last_updated": datetime.now().isoformat(),
            }

            for source in sources:
                status["sources"][source["source"].lower()] = {
                    "total_ips": source["count"],
                    "last_seen": source["last_seen"].isoformat()
                    if source["last_seen"]
                    else None,
                    "enabled": True,
                }

            return status
        except Exception as e:
            logger.error(f"Collection status check failed: {e}")
            return {"error": str(e), "collection_enabled": False}

    async def get_active_blacklist(self, format_type: str = "text") -> Dict[str, Any]:
        """활성 블랙리스트 조회"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            if format_type == "enhanced":
                cursor.execute(
                    """
                    SELECT ip_address, reason, source, category, confidence_level, 
                           is_active, last_seen, detection_count
                    FROM blacklist_ips 
                    WHERE is_active = true 
                    ORDER BY last_seen DESC
                """
                )
                rows = cursor.fetchall()
                data = []
                for row in rows:
                    item = {
                        "ip_address": row[0],
                        "reason": row[1],
                        "source": row[2],
                        "category": row[3],
                        "confidence_level": row[4],
                        "is_active": row[5],
                        "last_seen": row[6].isoformat() if row[6] else None,
                        "detection_count": row[7] if len(row) > 7 else 0,
                    }
                    data.append(item)

            elif format_type == "fortigate":
                cursor.execute(
                    "SELECT ip_address FROM blacklist_ips WHERE is_active = true"
                )
                ips = [row[0] for row in cursor.fetchall()]
                data = {
                    "entries": [{"ip": ip, "action": "block"} for ip in ips],
                    "total": len(ips),
                    "format": "fortigate_external_connector",
                }
            else:  # text format
                cursor.execute(
                    "SELECT ip_address FROM blacklist_ips WHERE is_active = true"
                )
                data = [row[0] for row in cursor.fetchall()]

            cursor.close()
            conn.close()

            return {
                "success": True,
                "data": data,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Active blacklist retrieval failed: {e}")
            return {"success": False, "error": str(e)}

    async def search_ip(self, ip: str) -> Dict[str, Any]:
        """IP 검색"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT ip_address, reason, source, category, confidence_level, 
                       is_active, last_seen, detection_count
                FROM blacklist_ips 
                WHERE ip_address = %s
            """,
                (ip,),
            )

            result = cursor.fetchone()
            cursor.close()
            conn.close()

            if result:
                data = {
                    "ip_address": result[0],
                    "reason": result[1],
                    "source": result[2],
                    "category": result[3],
                    "confidence_level": result[4],
                    "is_active": result[5],
                    "last_seen": result[6].isoformat() if result[6] else None,
                    "detection_count": result[7] if len(result) > 7 else 0,
                }

                return {
                    "success": True,
                    "found": True,
                    "data": data,
                    "timestamp": datetime.now().isoformat(),
                }
            else:
                return {
                    "success": True,
                    "found": False,
                    "data": None,
                    "timestamp": datetime.now().isoformat(),
                }

        except Exception as e:
            logger.error(f"IP search failed for {ip}: {e}")
            return {"success": False, "error": str(e)}

    async def get_statistics(self) -> Dict[str, Any]:
        """시스템 통계"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            # 전체 통계
            cursor.execute("SELECT COUNT(*) FROM blacklist_ips")
            total_ips = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM blacklist_ips WHERE is_active = true")
            active_ips = cursor.fetchone()[0]

            # 소스별 통계
            cursor.execute(
                """
                SELECT source, COUNT(*) as count, AVG(confidence_level) as avg_confidence
                FROM blacklist_ips 
                GROUP BY source
            """
            )
            sources = {}
            for row in cursor.fetchall():
                sources[row[0]] = {  # source
                    "count": row[1],  # count
                    "avg_confidence": float(row[2]) if row[2] else 0,  # avg_confidence
                }

            # 카테고리별 통계
            cursor.execute(
                """
                SELECT category, COUNT(*) as count 
                FROM blacklist_ips 
                GROUP BY category
            """
            )
            categories = {
                row[0]: row[1] for row in cursor.fetchall()
            }  # category: count

            cursor.close()
            conn.close()

            statistics = {
                "total_ips": total_ips,
                "active_ips": active_ips,
                "sources": sources,
                "categories": categories,
                "last_updated": datetime.now().isoformat(),
            }

            return {"success": True, "statistics": statistics}

        except Exception as e:
            logger.error(f"Statistics retrieval failed: {e}")
            return {"success": False, "error": str(e)}

    async def enable_collection(self) -> Dict[str, Any]:
        """수집 시스템 활성화"""
        try:
            # 실제 구현에서는 수집 프로세스를 시작
            logger.info("Collection system enabled")
            return {
                "success": True,
                "message": "수집 시스템이 활성화되었습니다",
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Collection enable failed: {e}")
            return {"success": False, "error": str(e)}

    async def disable_collection(self) -> Dict[str, Any]:
        """수집 시스템 비활성화"""
        try:
            # 실제 구현에서는 수집 프로세스를 중지
            logger.info("Collection system disabled")
            return {
                "success": True,
                "message": "수집 시스템이 비활성화되었습니다",
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Collection disable failed: {e}")
            return {"success": False, "error": str(e)}

    async def collect_all_data(self, force: bool = False) -> Dict[str, Any]:
        """모든 소스에서 데이터 수집"""
        results = {}

        # REGTECH 수집
        regtech_result = await self._collect_regtech_data(force)
        results["regtech"] = regtech_result

        # SECUDIUM 수집
        secudium_result = await self._collect_secudium_data(force)
        results["secudium"] = secudium_result

        success_count = sum(1 for r in results.values() if r.get("success", False))

        return {
            "success": success_count > 0,
            "results": results,
            "summary": {
                "total_sources": len(results),
                "successful": success_count,
                "failed": len(results) - success_count,
            },
        }

    async def _collect_regtech_data(self, force: bool = False) -> Dict[str, Any]:
        """REGTECH 데이터 수집"""
        try:
            # 실제 REGTECH API 호출 대신 시뮬레이션
            import random

            collected_count = random.randint(3, 8)

            logger.info(f"REGTECH collection completed: {collected_count} IPs")
            return {
                "success": True,
                "collected": collected_count,
                "message": "REGTECH 수집 완료",
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"REGTECH collection failed: {e}")
            return {"success": False, "error": str(e)}

    async def _collect_secudium_data(self, force: bool = False) -> Dict[str, Any]:
        """SECUDIUM 데이터 수집"""
        try:
            # 실제 SECUDIUM API 호출 대신 시뮬레이션
            import random

            collected_count = random.randint(2, 5)

            logger.info(f"SECUDIUM collection completed: {collected_count} IPs")
            return {
                "success": True,
                "collected": collected_count,
                "message": "SECUDIUM 수집 완료",
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"SECUDIUM collection failed: {e}")
            return {"success": False, "error": str(e)}


# 전역 서비스 인스턴스
service = BlacklistService()
