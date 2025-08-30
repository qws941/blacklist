#!/usr/bin/env python3
"""
검증 유틸리티 모듈
"""

import ipaddress
import logging
import re

logger = logging.getLogger(__name__)


class RegtechValidationUtils:
    """REGTECH 데이터 검증 유틸리티"""

    def __init__(self):
        self.ip_utils = None

    def set_ip_utils(self, ip_utils_class):
        """IP 유틸리티 클래스 설정"""
        self.ip_utils = ip_utils_class

    def is_valid_ip(self, ip_str: str) -> bool:
        """IP 주소 유효성 검사"""
        if not ip_str:
            return False

        try:
            ipaddress.ip_address(ip_str)
            return True
        except ValueError:
            return False

    def should_cancel(self, cancel_event) -> bool:
        """취소 요청 확인"""
        if cancel_event is None:
            return False
        return getattr(cancel_event, "is_set", lambda: False)()

    def validate_threat_data(self, data: dict) -> bool:
        """위협 데이터 유효성 검사"""
        required_fields = ["ip"]

        for field in required_fields:
            if field not in data or not data[field]:
                return False

        # IP 주소 검증
        if not self.is_valid_ip(data["ip"]):
            return False

        return True
