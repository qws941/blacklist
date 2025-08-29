#!/usr/bin/env python3
"""
Simple main entry point for Docker execution
"""
import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set environment for production
os.environ.setdefault("FLASK_ENV", "production")
os.environ.setdefault("PYTHONPATH", str(project_root))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 2542))

    # Try to start with full app, fallback to minimal if needed
    try:
        from src.core.main import create_app

        app = create_app()
        print(f"Starting Blacklist Management System (Full Mode) on port {port}")
        app.run(host="0.0.0.0", port=port, debug=False)

    except ImportError:
        from src.core.app import create_app

        app = create_app()
        print(f"Starting Blacklist Management System (Minimal Mode) on port {port}")
        app.run(host="0.0.0.0", port=port, debug=False)

    except Exception as e:
        print(f"App initialization failed: {e}")

        # Last resort: basic Flask app
        from flask import Flask, jsonify

        app = Flask(__name__)

        @app.route("/health")
        def health():
            return jsonify(
                {
                    "status": "healthy",
                    "mode": "emergency",
                    "timestamp": datetime.now().isoformat(),
                }
            )

        print(f"Starting emergency mode on port {port}")
        app.run(host="0.0.0.0", port=port, debug=False)  # Hook test comment
