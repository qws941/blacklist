#!/usr/bin/env python3
"""
Flask 애플리케이션 - PostgreSQL 연결 및 수집 관리
"""
import os
import psycopg2
from flask import Flask, jsonify, redirect, send_file
from datetime import datetime
from pathlib import Path


def create_app():
    """Flask 애플리케이션 생성"""
    app = Flask(__name__)

    # Register collection panel blueprint
    try:
        from src.core.routes.collection_panel import collection_bp
        from src.core.routes.collection_api import collection_api_bp

        app.register_blueprint(collection_bp)
        app.register_blueprint(collection_api_bp)
    except ImportError:
        pass  # Collection panel not available

    # Register NextTrade dashboard
    try:
        from src.core.simple_dashboard import dashboard_bp

        app.register_blueprint(dashboard_bp)
    except ImportError:
        pass  # Dashboard not available

    # Register unified API routes
    try:
        from src.core.routes.unified_api import unified_api_bp

        app.register_blueprint(unified_api_bp)
    except ImportError:
        pass  # Unified API not available

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
        """메인 페이지 - 수집기 대시보드로 리다이렉트"""
        return redirect("/collection-panel/")

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("PORT", 2542))
    app.run(host="0.0.0.0", port=port, debug=False)
