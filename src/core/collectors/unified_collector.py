#!/usr/bin/env python3
"""
통합 컬렉터 기본 클래스 및 설정
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CollectionConfig:
    """컬렉션 설정 클래스"""

    def __init__(self):
        self.enabled = True
        self.days_interval = 7  # 기본 7일
        self.max_retries = 3
        self.timeout = 30
        self.batch_size = 100

    def get_date_range(self, days: int = None) -> tuple:
        """날짜 범위 반환"""
        if days is None:
            days = self.days_interval

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")


class BaseCollector(ABC):
    """기본 컬렉터 추상 클래스"""

    def __init__(self, source_name: str, config: CollectionConfig):
        self.source_name = source_name
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{source_name}")

    @abstractmethod
    async def _collect_data(self) -> List[Any]:
        """데이터 수집 추상 메서드"""
        pass

    @property
    @abstractmethod
    def source_type(self) -> str:
        """소스 타입 반환"""
        pass

    def validate_config(self) -> bool:
        """설정 검증"""
        return self.config.enabled

    def get_status(self) -> Dict[str, Any]:
        """상태 정보 반환"""
        return {
            "source": self.source_name,
            "enabled": self.config.enabled,
            "last_run": None,
            "status": "ready",
        }
