#!/usr/bin/env python3
"""
데이터 변환 유틸리티 모듈
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)


class RegtechDataTransform:
    """REGTECH 데이터 변환 유틸리티"""

    def __init__(self):
        pass

    def get_date_range(self, config) -> Tuple[str, str]:
        """날짜 범위 계산"""
        if hasattr(config, "get_date_range"):
            return config.get_date_range()
        else:
            # Fallback
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")

    def transform_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """원시 데이터를 표준 형식으로 변환"""
        try:
            # 기본 변환 로직
            transformed = {
                "ip": raw_data.get("ip", ""),
                "threat_level": raw_data.get("threat_level", "medium"),
                "country": raw_data.get("country", "Unknown"),
                "attack_type": raw_data.get("attack_type", "blacklist"),
                "detection_date": raw_data.get(
                    "detection_date", datetime.now().strftime("%Y-%m-%d")
                ),
                "source": "REGTECH",
            }

            return transformed

        except Exception as e:
            logger.error(f"Data transformation failed: {e}")
            return raw_data
