#!/usr/bin/env python3
"""
최소한의 Flask 애플리케이션 - PostgreSQL 연결 테스트용
"""
import os
import psycopg2
from flask import Flask, jsonify, redirect, send_file
from datetime import datetime
from pathlib import Path


def create_minimal_app():
    """최소한의 Flask 애플리케이션 생성"""
    app = Flask(__name__)

    # Register collection panel blueprint
    try:
        from src.core.routes.simple_collection_panel import simple_collection_bp
        from src.core.routes.collection_api import collection_api_bp

        app.register_blueprint(simple_collection_bp)
        app.register_blueprint(collection_api_bp)
    except ImportError:
        pass  # Collection panel not available

    @app.route("/health")
    def health_check():
        """헬스체크 엔드포인트"""
        try:
            # PostgreSQL 연결 테스트
            conn = psycopg2.connect(
                host=os.getenv("POSTGRES_HOST", "postgres"),
                port=os.getenv("POSTGRES_PORT", "5432"),
                database=os.getenv("POSTGRES_DB", "blacklist"),
                user=os.getenv("POSTGRES_USER", "postgres"),
                password=os.getenv("POSTGRES_PASSWORD", "postgres"),
            )

            cursor = conn.cursor()

            # 테이블 존재 확인
            cursor.execute(
                """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """
            )
            tables = [row[0] for row in cursor.fetchall()]

            # 블랙리스트 IP 개수 확인
            cursor.execute("SELECT COUNT(*) FROM blacklist_ips")
            ip_count = cursor.fetchone()[0]

            cursor.close()
            conn.close()

            return (
                jsonify(
                    {
                        "status": "healthy",
                        "timestamp": datetime.now().isoformat(),
                        "database": {
                            "connection": "successful",
                            "tables": tables,
                            "blacklist_ips_count": ip_count,
                        },
                        "message": "✅ PostgreSQL 커스텀 이미지 연결 성공!",
                    }
                ),
                200,
            )

        except Exception as e:
            return (
                jsonify(
                    {
                        "status": "unhealthy",
                        "timestamp": datetime.now().isoformat(),
                        "error": str(e),
                        "message": "❌ 데이터베이스 연결 실패",
                    }
                ),
                500,
            )

    @app.route("/")
    def index():
        """메인 페이지 - 모니터링 대시보드로 리다이렉트"""
        # Check if monitoring dashboard exists
        dashboard_path = Path("/app/monitoring-dashboard.html")
        if not dashboard_path.exists():
            # Try relative path
            dashboard_path = Path("monitoring-dashboard.html")

        if dashboard_path.exists():
            return send_file(str(dashboard_path), mimetype="text/html")
        else:
            # Fallback to API info if dashboard not found
            return jsonify(
                {
                    "service": "Blacklist Application",
                    "status": "running",
                    "version": "custom-postgres-test",
                    "timestamp": datetime.now().isoformat(),
                    "endpoints": ["/health", "/", "/dashboard"],
                    "message": "Monitoring dashboard not found, showing API info",
                }
            )

    @app.route("/dashboard")
    def dashboard():
        """모니터링 대시보드"""
        dashboard_path = Path("/app/monitoring-dashboard.html")
        if not dashboard_path.exists():
            dashboard_path = Path("monitoring-dashboard.html")

        if dashboard_path.exists():
            return send_file(str(dashboard_path), mimetype="text/html")
        else:
            return jsonify({"error": "Dashboard file not found"}), 404

    return app


if __name__ == "__main__":
    app = create_minimal_app()
    port = int(os.getenv("PORT", 2542))
    app.run(host="0.0.0.0", port=port, debug=False)
