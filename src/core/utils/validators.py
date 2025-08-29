"""
입력 검증 유틸리티
"""
import re
import ipaddress
from typing import Union


def validate_ip(ip_str: str) -> bool:
    """IP 주소 유효성 검증"""
    try:
        ipaddress.ip_address(ip_str)
        return True
    except ValueError:
        return False


class ValidationError(Exception):
    """검증 오류 예외"""

    pass
