#!/usr/bin/env python3
"""
REGTECH 데이터 처리 모듈
"""

import logging
from typing import List, Dict, Any
import re
import json

logger = logging.getLogger(__name__)


class RegtechDataProcessor:
    """REGTECH 데이터 처리 클래스"""

    def __init__(self):
        self.validation_utils = None

    async def process_excel_response(self, response) -> List[Dict[str, Any]]:
        """Excel 응답 처리"""
        try:
            # Excel 처리 로직 (openpyxl 등 사용)
            logger.info("Processing Excel response")
            # 실제 구현 필요
            return []
        except Exception as e:
            logger.error(f"Excel processing failed: {e}")
            return []

    async def process_html_response(self, response) -> List[Dict[str, Any]]:
        """HTML 응답 처리"""
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(response.text, "html.parser")
            ips = []

            # IP 패턴 매칭
            ip_pattern = re.compile(r"\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b")
            text = soup.get_text()

            matches = ip_pattern.findall(text)
            for ip in matches:
                if self.validation_utils and self.validation_utils.is_valid_ip(ip):
                    ips.append(
                        {
                            "ip": ip,
                            "threat_level": "medium",
                            "source": "REGTECH_HTML",
                            "detection_date": "2025-08-30",
                        }
                    )

            logger.info(f"Extracted {len(ips)} IPs from HTML")
            return ips

        except Exception as e:
            logger.error(f"HTML processing failed: {e}")
            return []

    async def process_json_response(self, response) -> List[Dict[str, Any]]:
        """JSON 응답 처리"""
        try:
            data = response.json()

            # JSON 구조에 따라 IP 추출
            ips = []

            # 다양한 JSON 구조 지원
            if isinstance(data, list):
                for item in data:
                    ip_data = self._extract_ip_from_dict(item)
                    if ip_data:
                        ips.append(ip_data)
            elif isinstance(data, dict):
                # 네스트된 구조 처리
                if "data" in data:
                    for item in data["data"]:
                        ip_data = self._extract_ip_from_dict(item)
                        if ip_data:
                            ips.append(ip_data)
                else:
                    ip_data = self._extract_ip_from_dict(data)
                    if ip_data:
                        ips.append(ip_data)

            logger.info(f"Extracted {len(ips)} IPs from JSON")
            return ips

        except Exception as e:
            logger.error(f"JSON processing failed: {e}")
            return []

    def _extract_ip_from_dict(self, item: dict) -> Dict[str, Any]:
        """딕셔너리에서 IP 정보 추출"""
        try:
            # 다양한 키 이름 지원
            ip_keys = ["ip", "ip_address", "address", "host"]
            ip_value = None

            for key in ip_keys:
                if key in item:
                    ip_value = item[key]
                    break

            if (
                ip_value
                and self.validation_utils
                and self.validation_utils.is_valid_ip(ip_value)
            ):
                return {
                    "ip": ip_value,
                    "threat_level": item.get("threat_level", "medium"),
                    "country": item.get("country", "Unknown"),
                    "attack_type": item.get("attack_type", "blacklist"),
                    "detection_date": item.get("detection_date", "2025-08-30"),
                    "source": "REGTECH_JSON",
                }

        except Exception as e:
            logger.error(f"IP extraction failed for item {item}: {e}")

        return None

    def validate_and_transform_data(
        self, data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """데이터 검증 및 변환"""
        validated = []

        for item in data:
            if self.validation_utils and self.validation_utils.validate_threat_data(
                item
            ):
                validated.append(item)

        return validated

    def remove_duplicates(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """중복 제거"""
        seen_ips = set()
        unique_data = []

        for item in data:
            ip = item.get("ip")
            if ip and ip not in seen_ips:
                seen_ips.add(ip)
                unique_data.append(item)

        return unique_data
