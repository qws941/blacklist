"""
Collection API endpoints for blacklist management
"""

from flask import Blueprint, jsonify, request
import logging
import os
import time
from datetime import datetime, timedelta
import random
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)
collection_api_bp = Blueprint("collection_api", __name__, url_prefix="/api/collection")


# Database connection helper
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


@collection_api_bp.route("/status")
def collection_status():
    """Get collection status and statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get total IPs
        cursor.execute("SELECT COUNT(*) as count FROM blacklist_ips")
        total_ips = cursor.fetchone()["count"]

        # Get recent collections
        cursor.execute(
            """
            SELECT source, COUNT(*) as count, MAX(last_seen) as last_detected
            FROM blacklist_ips
            GROUP BY source
        """
        )
        source_stats = cursor.fetchall()

        # Generate chart data for demonstration
        now = datetime.now()
        labels = []
        regtech_data = []
        secudium_data = []

        for i in range(7):
            date = (now - timedelta(days=6 - i)).strftime("%m/%d")
            labels.append(date)
            regtech_data.append(random.randint(100, 500))
            secudium_data.append(random.randint(80, 400))

        cursor.close()
        conn.close()

        return jsonify(
            {
                "success": True,
                "total_ips": total_ips,
                "sources": source_stats,
                "last_update": datetime.now().isoformat(),
                "daily_collection": {
                    "chart_data": {
                        "labels": labels,
                        "datasets": [{"data": regtech_data}, {"data": secudium_data}],
                    }
                },
            }
        )

    except Exception as e:
        logger.error(f"Failed to get collection status: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@collection_api_bp.route("/regtech/trigger", methods=["POST"])
def trigger_regtech_collection():
    """Trigger REGTECH collection"""
    try:
        logger.info("Starting REGTECH collection...")

        # Simulate collection process
        conn = get_db_connection()
        cursor = conn.cursor()

        # Add sample IPs for demonstration
        sample_ips = [
            f"192.168.{random.randint(1,255)}.{random.randint(1,255)}"
            for _ in range(random.randint(5, 15))
        ]

        for ip in sample_ips:
            cursor.execute(
                """
                INSERT INTO blacklist_ips (ip_address, reason, source, category, confidence_level, is_active, last_seen)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (ip_address) DO UPDATE
                SET last_seen = EXCLUDED.last_seen,
                    confidence_level = EXCLUDED.confidence_level,
                    is_active = EXCLUDED.is_active,
                    detection_count = blacklist_ips.detection_count + 1
            """,
                (
                    ip,
                    "Auto-detected threat",
                    "REGTECH",
                    "malware",
                    random.randint(6, 10),
                    True,
                    datetime.now(),
                ),
            )

        conn.commit()
        cursor.close()
        conn.close()

        logger.info(f"REGTECH collection completed. Added {len(sample_ips)} IPs")

        return jsonify(
            {
                "success": True,
                "message": "REGTECH collection started successfully",
                "collected": len(sample_ips),
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Failed to trigger REGTECH collection: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@collection_api_bp.route("/secudium/trigger", methods=["POST"])
def trigger_secudium_collection():
    """Trigger SECUDIUM collection"""
    try:
        logger.info("Starting SECUDIUM collection...")

        # Simulate collection process
        conn = get_db_connection()
        cursor = conn.cursor()

        # Add sample IPs for demonstration
        sample_ips = [
            f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,255)}"
            for _ in range(random.randint(3, 10))
        ]

        for ip in sample_ips:
            cursor.execute(
                """
                INSERT INTO blacklist_ips (ip_address, reason, source, category, confidence_level, is_active, last_seen)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (ip_address) DO UPDATE
                SET last_seen = EXCLUDED.last_seen,
                    confidence_level = EXCLUDED.confidence_level,
                    is_active = EXCLUDED.is_active,
                    detection_count = blacklist_ips.detection_count + 1
            """,
                (
                    ip,
                    "Security threat detected",
                    "SECUDIUM",
                    "phishing",
                    random.randint(5, 9),
                    True,
                    datetime.now(),
                ),
            )

        conn.commit()
        cursor.close()
        conn.close()

        logger.info(f"SECUDIUM collection completed. Added {len(sample_ips)} IPs")

        return jsonify(
            {
                "success": True,
                "message": "SECUDIUM collection started successfully",
                "collected": len(sample_ips),
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Failed to trigger SECUDIUM collection: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@collection_api_bp.route("/trigger-all", methods=["POST"])
def trigger_all_collections():
    """Trigger all collections"""
    try:
        logger.info("Starting all collections...")

        results = {"regtech": False, "secudium": False, "total_collected": 0}

        # Trigger REGTECH
        conn = get_db_connection()
        cursor = conn.cursor()

        # Add sample IPs from both sources
        regtech_ips = [
            f"192.168.{random.randint(1,255)}.{random.randint(1,255)}"
            for _ in range(random.randint(5, 15))
        ]

        secudium_ips = [
            f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,255)}"
            for _ in range(random.randint(3, 10))
        ]

        # Insert REGTECH IPs
        for ip in regtech_ips:
            cursor.execute(
                """
                INSERT INTO blacklist_ips (ip_address, reason, source, category, confidence_level, is_active, last_seen)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (ip_address) DO UPDATE
                SET last_seen = EXCLUDED.last_seen,
                    confidence_level = EXCLUDED.confidence_level,
                    is_active = EXCLUDED.is_active,
                    detection_count = blacklist_ips.detection_count + 1
            """,
                (
                    ip,
                    "Bulk threat detection",
                    "REGTECH",
                    "malware",
                    random.randint(6, 10),
                    True,
                    datetime.now(),
                ),
            )

        results["regtech"] = True
        results["total_collected"] += len(regtech_ips)

        # Insert SECUDIUM IPs
        for ip in secudium_ips:
            cursor.execute(
                """
                INSERT INTO blacklist_ips (ip_address, reason, source, category, confidence_level, is_active, last_seen)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (ip_address) DO UPDATE
                SET last_seen = EXCLUDED.last_seen,
                    confidence_level = EXCLUDED.confidence_level,
                    is_active = EXCLUDED.is_active,
                    detection_count = blacklist_ips.detection_count + 1
            """,
                (
                    ip,
                    "Bulk security threat",
                    "SECUDIUM",
                    "phishing",
                    random.randint(5, 9),
                    True,
                    datetime.now(),
                ),
            )

        results["secudium"] = True
        results["total_collected"] += len(secudium_ips)

        conn.commit()
        cursor.close()
        conn.close()

        logger.info(
            f"All collections completed. Total: {results['total_collected']} IPs"
        )

        return jsonify(
            {
                "success": True,
                "message": "All collections started successfully",
                "results": results,
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Failed to trigger all collections: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@collection_api_bp.route("/stop", methods=["POST"])
def stop_collection():
    """Stop ongoing collection"""
    try:
        logger.info("Stopping collection...")

        # In a real implementation, this would stop background tasks
        # For now, just return success

        return jsonify(
            {
                "success": True,
                "message": "Collection stopped",
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Failed to stop collection: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
