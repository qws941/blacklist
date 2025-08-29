"""
통합 API 라우트
모든 블랙리스트 API를 하나로 통합한 라우트 시스템
"""
from flask import Blueprint, request, jsonify, Response, render_template
from typing import Dict, Any
import logging
import asyncio
from datetime import datetime

# Import service and utilities
from src.core.services.blacklist_service import service
from src.core.utils.validators import validate_ip, ValidationError
from src.core.utils.error_handlers import handle_exception

logger = logging.getLogger(__name__)

# 통합 라우트 블루프린트
unified_bp = Blueprint("unified", __name__)

# === 웹 인터페이스 ===


@unified_bp.route("/api/docs", methods=["GET"])
def api_dashboard():
    """API 문서"""
    return jsonify(
        {
            "message": "API Documentation",
            "dashboard_url": "/dashboard",
            "note": "Visit /dashboard for the web interface",
            "api_endpoints": {
                "health": "/health",
                "stats": "/api/stats",
                "blacklist": "/api/blacklist/active",
                "fortigate": "/api/fortigate",
                "collection": "/api/collection/status",
            },
        }
    )


@unified_bp.route("/dashboard", methods=["GET"])
def dashboard():
    """웹 대시보드 - 간단한 응답으로 임시 변경"""
    # 임시로 간단한 HTML 응답 (템플릿 문제 해결 후 복원)
    return """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Blacklist Management Dashboard</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
        <style>
            .dashboard-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 2rem;
                border-radius: 1rem;
                margin-bottom: 2rem;
            }
            .stat-card {
                background: white;
                border-radius: 1rem;
                padding: 1.5rem;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
                border: 1px solid rgba(0, 0, 0, 0.05);
                transition: all 0.3s ease;
                height: 100%;
            }
            .stat-card:hover {
                transform: translateY(-4px);
                box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
            }
            .stat-icon {
                width: 56px;
                height: 56px;
                border-radius: 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 24px;
                margin-bottom: 1rem;
            }
            .stat-icon.primary { background: rgba(80, 70, 229, 0.1); color: #5046e5; }
            .stat-icon.success { background: rgba(16, 185, 129, 0.1); color: #10b981; }
            .stat-icon.info { background: rgba(59, 130, 246, 0.1); color: #3b82f6; }
            .stat-icon.warning { background: rgba(245, 158, 11, 0.1); color: #f59e0b; }
        </style>
    </head>
    <body class="bg-light">
        <nav class="navbar navbar-expand-lg navbar-light fixed-top bg-white shadow-sm">
            <div class="container-fluid">
                <a class="navbar-brand d-flex align-items-center" href="/">
                    <img src="https://www.nextrade.co.kr/images/main/header_logo_color.svg" alt="Nextrade" style="height: 32px; margin-right: 10px;" onerror="this.style.display='none'; this.nextElementSibling.style.display='inline-flex';">
                    <span style="display: none; align-items: center;"><i class="bi bi-shield-lock"></i> Nextrade Black List</span>
                </a>
                <span class="badge bg-success">LIVE</span>
            </div>
        </nav>

        <div class="container mt-5 pt-4">
            <!-- Dashboard Header -->
            <div class="dashboard-header">
                <div class="row align-items-center">
                    <div class="col-md-8">
                        <h1 class="h3 mb-1">🛡️ 시스템 대시보드</h1>
                        <p class="mb-0 opacity-75">Nextrade Black List Management System</p>
                    </div>
                    <div class="col-md-4 text-md-end">
                        <span class="badge bg-success me-2">
                            <i class="bi bi-circle-fill"></i> 실시간 모니터링
                        </span>
                    </div>
                </div>
            </div>

            <!-- Statistics Cards -->
            <div class="row g-4 mb-4">
                <div class="col-lg-3 col-md-6">
                    <div class="stat-card">
                        <div class="stat-icon primary">
                            <i class="bi bi-database-fill"></i>
                        </div>
                        <h2 class="fw-bold mb-1" id="total-ips">로딩중...</h2>
                        <p class="text-muted mb-0">전체 블랙리스트 IP</p>
                    </div>
                </div>
                <div class="col-lg-3 col-md-6">
                    <div class="stat-card">
                        <div class="stat-icon success">
                            <i class="bi bi-shield-fill-check"></i>
                        </div>
                        <h2 class="fw-bold mb-1" id="active-ips">로딩중...</h2>
                        <p class="text-muted mb-0">활성 차단 IP</p>
                    </div>
                </div>
                <div class="col-lg-3 col-md-6">
                    <div class="stat-card">
                        <div class="stat-icon info">
                            <i class="bi bi-cpu-fill"></i>
                        </div>
                        <h2 class="fw-bold mb-1" id="system-status">로딩중...</h2>
                        <p class="text-muted mb-0">시스템 상태</p>
                    </div>
                </div>
                <div class="col-lg-3 col-md-6">
                    <div class="stat-card">
                        <div class="stat-icon warning">
                            <i class="bi bi-collection-fill"></i>
                        </div>
                        <h2 class="fw-bold mb-1" id="sources-count">로딩중...</h2>
                        <p class="text-muted mb-0">활성 데이터 소스</p>
                    </div>
                </div>
            </div>

            <!-- Action Cards -->
            <div class="row g-4">
                <div class="col-lg-6">
                    <div class="stat-card">
                        <h5 class="fw-semibold mb-3">
                            <i class="bi bi-pie-chart text-info"></i> 소스별 분포
                        </h5>
                        <div id="source-distribution">
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <span class="text-muted">REGTECH</span>
                                <span class="fw-semibold" id="regtech-percent">계산중...</span>
                            </div>
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <span class="text-muted">SECUDIUM</span>
                                <span class="fw-semibold" id="secudium-percent">계산중...</span>
                            </div>
                            <div class="d-flex justify-content-between align-items-center">
                                <span class="text-muted">Public Sources</span>
                                <span class="fw-semibold" id="public-percent">계산중...</span>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-lg-6">
                    <div class="stat-card">
                        <h5 class="fw-semibold mb-3">
                            <i class="bi bi-lightning text-warning"></i> 빠른 작업
                        </h5>
                        <div class="d-grid gap-2">
                            <a href="/api/blacklist/active" class="btn btn-primary" target="_blank">
                                <i class="bi bi-list"></i> 활성 IP 목록
                            </a>
                            <a href="/api/fortigate" class="btn btn-success" target="_blank">
                                <i class="bi bi-gear"></i> FortiGate 형식
                            </a>
                            <a href="/api/collection/status" class="btn btn-info" target="_blank">
                                <i class="bi bi-info-circle"></i> 수집 상태
                            </a>
                            <button class="btn btn-warning" onclick="location.reload()">
                                <i class="bi bi-arrow-clockwise"></i> 새로고침
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            async function loadDashboardData() {
                try {
                    // Health check
                    const healthResponse = await fetch('/health');
                    const health = await healthResponse.json();
                    document.getElementById('system-status').textContent = health.status || 'unknown';
                    
                    // Stats
                    const statsResponse = await fetch('/api/stats');
                    const stats = await statsResponse.json();
                    document.getElementById('total-ips').textContent = stats.total_ips || '0';
                    document.getElementById('active-ips').textContent = stats.total_ips || '0';
                    
                    // Collection status
                    const collectionResponse = await fetch('/api/collection/status');
                    const collection = await collectionResponse.json();
                    const sources = collection.status?.sources || {};
                    document.getElementById('sources-count').textContent = Object.keys(sources).length;
                    
                    // Source distribution
                    const regtech = sources.regtech?.total_ips || 0;
                    const secudium = sources.secudium?.total_ips || 0;
                    const total = regtech + secudium;
                    
                    if (total > 0) {
                        document.getElementById('regtech-percent').textContent = 
                            Math.round((regtech / total) * 100) + '% (' + regtech + '개)';
                        document.getElementById('secudium-percent').textContent = 
                            Math.round((secudium / total) * 100) + '% (' + secudium + '개)';
                        document.getElementById('public-percent').textContent = '0% (0개)';
                    } else {
                        document.getElementById('regtech-percent').textContent = '0% (0개)';
                        document.getElementById('secudium-percent').textContent = '0% (0개)';
                        document.getElementById('public-percent').textContent = '0% (0개)';
                    }
                    
                } catch (error) {
                    console.error('Dashboard data loading failed:', error);
                    document.getElementById('total-ips').textContent = 'Error';
                    document.getElementById('system-status').textContent = 'Error';
                }
            }
            
            // Load data on page load
            loadDashboardData();
            
            // Auto refresh every 30 seconds
            setInterval(loadDashboardData, 30000);
        </script>
    </body>
    </html>
    """


# === 통합 서비스 상태 ===


@unified_bp.route("/api/status", methods=["GET"])
def service_status():
    """서비스 상태 조회"""
    try:
        health = service.get_health()
        collection_status = service.get_collection_status()

        return jsonify(
            {
                "service": {
                    "name": "blacklist-unified",
                    "version": health.version,
                    "status": health.status,
                    "timestamp": datetime.now().isoformat(),
                },
                "components": health.components,
                "collection": collection_status,
                "healthy": health.status == "healthy",
            }
        )

    except Exception as e:
        return handle_exception(e, "서비스 상태 조회 실패")


# === 블랙리스트 조회 ===


@unified_bp.route("/api/blacklist/active", methods=["GET"])
def get_active_blacklist():
    """활성 블랙리스트 조회 (플레인 텍스트)"""
    try:
        result = asyncio.run(service.get_active_blacklist(format_type="text"))

        if result["success"]:
            response = Response(
                "\n".join(result["data"]) + "\n",
                mimetype="text/plain",
                headers={
                    "Cache-Control": "public, max-age=300",
                    "Content-Disposition": 'inline; filename="blacklist.txt"',
                },
            )
            return response
        else:
            return jsonify({"error": result["error"]}), 500

    except Exception as e:
        return handle_exception(e, "활성 블랙리스트 조회 실패")


@unified_bp.route("/api/fortigate", methods=["GET"])
def get_fortigate_format():
    """FortiGate External Connector 형식"""
    try:
        result = asyncio.run(service.get_active_blacklist(format_type="fortigate"))

        if result["success"]:
            return jsonify(result["data"])
        else:
            return jsonify({"error": result["error"]}), 500

    except Exception as e:
        return handle_exception(e, "FortiGate 형식 조회 실패")


@unified_bp.route("/api/blacklist/json", methods=["GET"])
def get_blacklist_json():
    """블랙리스트 JSON 형식"""
    try:
        result = asyncio.run(service.get_active_blacklist(format_type="json"))

        if result["success"]:
            return jsonify(
                {
                    "success": True,
                    "data": result["data"],
                    "count": len(result["data"])
                    if isinstance(result["data"], list)
                    else 0,
                    "timestamp": result["timestamp"],
                }
            )
        else:
            return jsonify({"error": result["error"]}), 500

    except Exception as e:
        return handle_exception(e, "JSON 블랙리스트 조회 실패")


# === IP 검색 ===


@unified_bp.route("/api/search/<ip>", methods=["GET"])
def search_single_ip(ip: str):
    """단일 IP 검색"""
    try:
        # IP 주소 유효성 검사
        if not validate_ip(ip):
            raise ValidationError(f"유효하지 않은 IP 주소: {ip}")

        result = asyncio.run(service.search_ip(ip))

        if result["success"]:
            return jsonify(result)
        else:
            return jsonify({"error": result["error"]}), 400

    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return handle_exception(e, f"IP 검색 실패: {ip}")


@unified_bp.route("/api/search", methods=["POST"])
def search_batch_ips():
    """배치 IP 검색"""
    try:
        data = request.get_json()
        if not data or "ips" not in data:
            raise ValidationError("IP 목록이 필요합니다")

        ips = data["ips"]
        if not isinstance(ips, list) or len(ips) > 100:
            raise ValidationError("IP 목록은 배열이며 100개 이하여야 합니다")

        results = {}
        for ip in ips:
            if validate_ip(ip):
                result = asyncio.run(service.search_ip(ip))
                results[ip] = result
            else:
                results[ip] = {"success": False, "error": "Invalid IP address"}

        return jsonify(
            {
                "success": True,
                "results": results,
                "total_searched": len(ips),
                "timestamp": datetime.now().isoformat(),
            }
        )

    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return handle_exception(e, "배치 IP 검색 실패")


# === 통계 ===


@unified_bp.route("/api/stats", methods=["GET"])
def get_statistics():
    """시스템 통계"""
    try:
        result = asyncio.run(service.get_statistics())

        if result["success"]:
            return jsonify(result["statistics"])
        else:
            return jsonify({"error": result["error"]}), 500

    except Exception as e:
        return handle_exception(e, "통계 조회 실패")


@unified_bp.route("/api/v2/analytics/summary", methods=["GET"])
def get_analytics_summary():
    """분석 요약"""
    try:
        result = asyncio.run(service.get_statistics())

        if result["success"]:
            stats = result["statistics"]

            # 요약 정보 생성
            summary = {
                "total_ips": stats.get("total_ips", 0),
                "active_ips": stats.get("active_ips", 0),
                "sources": stats.get("sources", {}),
                "last_updated": stats.get("last_updated"),
                "collection_status": service.get_collection_status(),
                "service_health": service.get_health().status,
            }

            return jsonify(
                {
                    "success": True,
                    "summary": summary,
                    "timestamp": datetime.now().isoformat(),
                }
            )
        else:
            return jsonify({"error": result["error"]}), 500

    except Exception as e:
        return handle_exception(e, "분석 요약 조회 실패")


# === 수집 관리 ===


@unified_bp.route("/api/collection/status", methods=["GET"])
def get_collection_status():
    """수집 시스템 상태"""
    try:
        status = service.get_collection_status()
        return jsonify(status)
    except Exception as e:
        return handle_exception(e, "수집 상태 조회 실패")


@unified_bp.route("/api/collection/enable", methods=["POST"])
def enable_collection():
    """수집 시스템 활성화"""
    try:
        result = asyncio.run(service.enable_collection())

        if result["success"]:
            return jsonify(result)
        else:
            return jsonify({"error": result["error"]}), 500

    except Exception as e:
        return handle_exception(e, "수집 시스템 활성화 실패")


@unified_bp.route("/api/collection/disable", methods=["POST"])
def disable_collection():
    """수집 시스템 비활성화"""
    try:
        result = asyncio.run(service.disable_collection())

        if result["success"]:
            return jsonify(result)
        else:
            return jsonify({"error": result["error"]}), 500

    except Exception as e:
        return handle_exception(e, "수집 시스템 비활성화 실패")


@unified_bp.route("/api/collection/trigger", methods=["POST"])
def trigger_collection():
    """수동 데이터 수집 트리거"""
    try:
        # 요청 파라미터 확인
        data = request.get_json() or {}
        sources = data.get("sources", ["regtech", "secudium"])
        force = data.get("force", False)

        # 유효한 소스인지 확인
        valid_sources = ["regtech", "secudium"]
        if isinstance(sources, str):
            sources = [sources]

        invalid_sources = [s for s in sources if s not in valid_sources]
        if invalid_sources:
            raise ValidationError(f"유효하지 않은 소스: {invalid_sources}")

        # 수집 실행
        result = asyncio.run(service.collect_all_data(force=force))

        return jsonify(
            {
                "success": result["success"],
                "message": "데이터 수집이 완료되었습니다"
                if result["success"]
                else "데이터 수집 중 오류가 발생했습니다",
                "results": result["results"],
                "summary": result["summary"],
            }
        )

    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return handle_exception(e, "수동 수집 실행 실패")


@unified_bp.route("/api/collection/regtech/trigger", methods=["POST"])
def trigger_regtech_collection():
    """REGTECH 수집 트리거"""
    try:
        # JSON과 폼 데이터 모두 지원
        data = {}
        if request.is_json:
            data = request.get_json() or {}
        elif request.form:
            data = request.form.to_dict()

        force = data.get("force", False)

        if "regtech" not in service._components:
            return jsonify({"error": "REGTECH 수집기가 비활성화되어 있습니다"}), 400

        result = asyncio.run(service._collect_regtech_data(force))

        return jsonify(
            {
                "success": result.get("success", False),
                "message": "REGTECH 수집이 완료되었습니다"
                if result.get("success")
                else "REGTECH 수집 실패",
                "result": result,
            }
        )

    except Exception as e:
        return handle_exception(e, "REGTECH 수집 실행 실패")


@unified_bp.route("/api/collection/secudium/trigger", methods=["POST"])
def trigger_secudium_collection():
    """SECUDIUM 수집 트리거"""
    try:
        # JSON과 폼 데이터 모두 지원
        data = {}
        if request.is_json:
            data = request.get_json() or {}
        elif request.form:
            data = request.form.to_dict()

        force = data.get("force", False)

        if "secudium" not in service._components:
            return jsonify({"error": "SECUDIUM 수집기가 비활성화되어 있습니다"}), 400

        result = asyncio.run(service._collect_secudium_data(force))

        return jsonify(
            {
                "success": result.get("success", False),
                "message": "SECUDIUM 수집이 완료되었습니다"
                if result.get("success")
                else "SECUDIUM 수집 실패",
                "result": result,
            }
        )

    except Exception as e:
        return handle_exception(e, "SECUDIUM 수집 실행 실패")


# === 고급 기능 ===


@unified_bp.route("/api/v2/blacklist/enhanced", methods=["GET"])
def get_enhanced_blacklist():
    """향상된 블랙리스트 (메타데이터 포함)"""
    try:
        result = asyncio.run(service.get_active_blacklist(format_type="enhanced"))

        if result["success"]:
            return jsonify(
                {
                    "success": True,
                    "data": result["data"],
                    "metadata": {
                        "total_count": len(result["data"])
                        if isinstance(result["data"], list)
                        else 0,
                        "last_updated": result["timestamp"],
                        "sources": list(service._components.keys()),
                        "collection_status": service.get_collection_status(),
                    },
                }
            )
        else:
            return jsonify({"error": result["error"]}), 500

    except Exception as e:
        return handle_exception(e, "향상된 블랙리스트 조회 실패")


# === 에러 핸들러 ===


@unified_bp.errorhandler(404)
def not_found(error):
    """404 에러 핸들러"""
    return (
        jsonify(
            {
                "error": "API 엔드포인트를 찾을 수 없습니다",
                "available_endpoints": [
                    "/health",
                    "/api/status",
                    "/api/blacklist/active",
                    "/api/fortigate",
                    "/api/search/<ip>",
                    "/api/stats",
                    "/api/collection/status",
                    "/api/collection/trigger",
                ],
            }
        ),
        404,
    )


@unified_bp.errorhandler(500)
def internal_error(error):
    """500 에러 핸들러"""
    logger.error(f"내부 서버 오류: {error}")
    return (
        jsonify({"error": "내부 서버 오류가 발생했습니다", "timestamp": datetime.now().isoformat()}),
        500,
    )
