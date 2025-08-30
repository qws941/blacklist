#!/usr/bin/env python3
"""
REGTECH 수집기 - 모듈화된 구조 (메인 진입점)
BaseCollector 상속 및 강화된 에러 핸들링
이 파일은 다른 모듈들을 조합하는 메인 진입점 역할만 합니다.
"""

# Re-export the main collector from the core module
from .regtech_collector_core import RegtechCollector

__all__ = ["RegtechCollector"]


if __name__ == "__main__":
    # 모듈화된 REGTECH 컬렉터 테스트
    import sys

    all_validation_failures = []
    total_tests = 0

    # Test 1: 기본 컬렉터 생성
    total_tests += 1
    try:
        from .unified_collector import CollectionConfig

        config = CollectionConfig()
        collector = RegtechCollector(config)
        if not hasattr(collector, "auth_module") or not hasattr(
            collector, "data_module"
        ):
            all_validation_failures.append("필수 컴포넌트 누락")
    except Exception as e:
        all_validation_failures.append(f"컬렉터 생성 실패: {e}")

    # Test 2: 메서드 존재 확인
    total_tests += 1
    try:
        from .unified_collector import CollectionConfig

        config = CollectionConfig()
        collector = RegtechCollector(config)
        required_methods = [
            "_collect_data",
            "collect_from_web",
        ]
        for method_name in required_methods:
            if not hasattr(collector, method_name):
                all_validation_failures.append(f"필수 메서드 누락: {method_name}")
    except Exception as e:
        all_validation_failures.append(f"메서드 검증 실패: {e}")

    # 결과 출력
    if all_validation_failures:
        print(f"❌ 검증 실패: {len(all_validation_failures)}/{total_tests}")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ 모든 검증 통과: {total_tests}/{total_tests}")
        sys.exit(0)
