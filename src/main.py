#!/usr/bin/env python3
"""
Simple main entry point for Docker execution
"""
import sys
import os
from pathlib import Path
from datetime import datetime
from flask import jsonify

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set environment for production
os.environ.setdefault("FLASK_ENV", "production")
os.environ.setdefault("PYTHONPATH", str(project_root))


def setup_version_routes(app):
    """파이프라인에서 주입된 버전 정보 API 엔드포인트 설정"""

    @app.route("/version")
    def version():
        """파이프라인에서 주입된 버전 정보 API"""
        return jsonify(
            {
                "version": os.environ.get("VERSION", "unknown"),
                "build_number": os.environ.get("BUILD_NUMBER", "unknown"),
                "commit": os.environ.get("VCS_REF", "unknown"),
                "build_date": os.environ.get("BUILDTIME", "unknown"),
                "timestamp": datetime.now().isoformat(),
            }
        )

    @app.route("/version/short")
    def version_short():
        """간단한 버전 정보"""
        return jsonify(
            {
                "version": os.environ.get("VERSION", "unknown"),
                "build": os.environ.get("BUILD_NUMBER", "unknown"),
                "commit": os.environ.get("VCS_REF", "unknown")[:8]
                if os.environ.get("VCS_REF")
                else "unknown",
                "timestamp": datetime.now().isoformat(),
            }
        )

    @app.route("/health")
    def health():
        """헬스체크 (파이프라인 버전 정보 포함)"""
        return jsonify(
            {
                "status": "healthy",
                "mode": getattr(app, "mode", "unknown"),
                "version": os.environ.get("VERSION", "unknown"),
                "build_number": os.environ.get("BUILD_NUMBER", "unknown"),
                "commit": os.environ.get("VCS_REF", "unknown")[:8]
                if os.environ.get("VCS_REF")
                else "unknown",
                "timestamp": datetime.now().isoformat(),
            }
        )


# Initialize app for gunicorn
app = None


def initialize_app():
    """Initialize Flask app with fallback logic"""
    global app
    if app is not None:
        return app

    version_str = os.environ.get("VERSION", "unknown")

    print(f"🚀 Blacklist Management System")
    print(f"📦 Version: {version_str}")
    print(f"🏷️ Build: {os.environ.get('BUILD_NUMBER', 'unknown')}")
    print(
        f"📝 Commit: {os.environ.get('VCS_REF', 'unknown')[:8] if os.environ.get('VCS_REF') else 'unknown'}"
    )

    # Try to start with full app, fallback to minimal if needed
    try:
        from src.core.main import create_app

        app = create_app()
        app.mode = "full"
        setup_version_routes(app)

        print(f"🎯 Full Mode initialized")
        return app

    except ImportError:
        from src.core.app import create_app

        app = create_app()
        app.mode = "minimal"
        setup_version_routes(app)

        print(f"⚡ Minimal Mode initialized")
        return app

    except Exception as e:
        print(f"❌ App initialization failed: {e}")
        print(f"🆘 Emergency Mode initialized")

        # Last resort: basic Flask app
        from flask import Flask, jsonify

        app = Flask(__name__)
        app.mode = "emergency"
        setup_version_routes(app)

        return app


# Initialize app for gunicorn
app = initialize_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 2542))

    # App is already initialized above for gunicorn
    print(f"🎯 Starting {getattr(app, 'mode', 'unknown').title()} Mode on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
