"""
새로운 통합 API - collection_api 방식 사용
"""
from flask import Blueprint, jsonify, request, Response
import logging
import os
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)
unified_api_bp = Blueprint("unified_api", __name__, url_prefix="/api")


# Database connection helper (collection_api와 동일)
def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "postgres"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        database=os.getenv("POSTGRES_DB", "blacklist"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        cursor_factory=RealDictCursor,
    )


@unified_api_bp.route("/stats")
def get_statistics():
    """시스템 통계"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 전체 통계
        cursor.execute("SELECT COUNT(*) as count FROM blacklist_ips")
        total_ips = cursor.fetchone()["count"]

        cursor.execute(
            "SELECT COUNT(*) as count FROM blacklist_ips WHERE is_active = true"
        )
        active_ips = cursor.fetchone()["count"]

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
            sources[row["source"]] = {
                "count": row["count"],
                "avg_confidence": float(row["avg_confidence"])
                if row["avg_confidence"]
                else 0,
            }

        # 카테고리별 통계
        cursor.execute(
            """
            SELECT category, COUNT(*) as count 
            FROM blacklist_ips 
            GROUP BY category
        """
        )
        categories = {}
        for row in cursor.fetchall():
            categories[row["category"]] = row["count"]

        cursor.close()
        conn.close()

        return jsonify(
            {
                "success": True,
                "total_ips": total_ips,
                "active_ips": active_ips,
                "sources": sources,
                "categories": categories,
                "last_updated": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Statistics retrieval failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@unified_api_bp.route("/blacklist/active")
def get_active_blacklist():
    """활성 블랙리스트 조회 (텍스트)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT ip_address FROM blacklist_ips WHERE is_active = true ORDER BY last_seen DESC"
        )
        ips = [row["ip_address"] for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        # 텍스트 형식으로 반환
        response = Response(
            "\n".join(ips) + "\n",
            mimetype="text/plain",
            headers={
                "Cache-Control": "public, max-age=300",
                "Content-Disposition": 'inline; filename="blacklist.txt"',
            },
        )
        return response

    except Exception as e:
        logger.error(f"Active blacklist retrieval failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@unified_api_bp.route("/blacklist/json")
def get_blacklist_json():
    """활성 블랙리스트 JSON 형식"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT ip_address, reason, source, category, confidence_level, 
                   is_active, last_seen, detection_count
            FROM blacklist_ips 
            WHERE is_active = true 
            ORDER BY last_seen DESC
        """
        )

        data = []
        for row in cursor.fetchall():
            item = dict(row)
            if item["last_seen"]:
                item["last_seen"] = item["last_seen"].isoformat()
            data.append(item)

        cursor.close()
        conn.close()

        return jsonify(
            {
                "success": True,
                "data": data,
                "count": len(data),
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"JSON blacklist retrieval failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@unified_api_bp.route("/fortigate")
def get_fortigate_format():
    """FortiGate External Connector 형식"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT ip_address FROM blacklist_ips WHERE is_active = true")
        ips = [row["ip_address"] for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        data = {
            "entries": [{"ip": ip, "action": "block"} for ip in ips],
            "total": len(ips),
            "format": "fortigate_external_connector",
            "timestamp": datetime.now().isoformat(),
        }

        return jsonify(data)

    except Exception as e:
        logger.error(f"FortiGate format retrieval failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@unified_api_bp.route("/search/<ip>")
def search_single_ip(ip: str):
    """단일 IP 검색"""
    try:
        conn = get_db_connection()
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
            data = dict(result)
            if data["last_seen"]:
                data["last_seen"] = data["last_seen"].isoformat()

            return jsonify(
                {
                    "success": True,
                    "found": True,
                    "data": data,
                    "timestamp": datetime.now().isoformat(),
                }
            )
        else:
            return jsonify(
                {
                    "success": True,
                    "found": False,
                    "data": None,
                    "timestamp": datetime.now().isoformat(),
                }
            )

    except Exception as e:
        logger.error(f"IP search failed for {ip}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@unified_api_bp.route("/status")
def service_status():
    """서비스 상태 조회"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 기본 헬스 체크
        cursor.execute("SELECT COUNT(*) as count FROM blacklist_ips")
        ip_count = cursor.fetchone()["count"]

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

        components = {
            "database": {"status": "healthy", "ip_count": ip_count},
            "regtech": {"status": "healthy", "enabled": True},
            "secudium": {"status": "healthy", "enabled": True},
        }

        source_stats = {}
        for source in sources:
            source_stats[source["source"].lower()] = {
                "total_ips": source["count"],
                "last_seen": source["last_seen"].isoformat()
                if source["last_seen"]
                else None,
                "enabled": True,
            }

        return jsonify(
            {
                "service": {
                    "name": "blacklist-unified",
                    "version": "1.0.0",
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                },
                "components": components,
                "sources": source_stats,
                "collection": {"collection_enabled": True, "total_ips": ip_count},
                "healthy": True,
            }
        )

    except Exception as e:
        logger.error(f"Service status check failed: {e}")
        return (
            jsonify(
                {
                    "service": {
                        "name": "blacklist-unified",
                        "version": "1.0.0",
                        "status": "degraded",
                        "timestamp": datetime.now().isoformat(),
                    },
                    "error": str(e),
                    "healthy": False,
                }
            ),
            500,
        )
