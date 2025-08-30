#!/usr/bin/env python3
"""
REGTECH 데이터 수집 및 처리 모듈
실제 데이터 수집, 페이지 처리, 검증 등의 기능을 담당
"""

import asyncio
import logging
from typing import Any, Dict, List

import requests

from .helpers.data_transform import RegtechDataTransform
from .regtech_data_processor import RegtechDataProcessor

logger = logging.getLogger(__name__)


class RegtechCollectorData:
    """
    REGTECH 수집기의 데이터 수집 및 처리 기능을 담당하는 모듈
    """

    def __init__(self, base_url: str, auth_module, validation_utils):
        self.base_url = base_url
        self.auth_module = auth_module
        self.validation_utils = validation_utils
        self.request_timeout = 30
        self.page_delay = 1
        self.max_page_errors = 5

        # 데이터 처리 컴포넌트 초기화
        self.data_processor = RegtechDataProcessor()
        self.data_transform = RegtechDataTransform()

        # 데이터 프로세서에 검증 유틸리티 설정
        self.data_processor.validation_utils = validation_utils

        logger.info("REGTECH data collection module initialized")

    async def collect_with_cookies(self) -> List[Any]:
        """쿠키 기반 데이터 수집"""
        collected_ips = []

        try:
            # 인증된 세션 생성
            session = self.auth_module.get_authenticated_session()
            if not session:
                logger.error("Failed to get authenticated session")
                return []

            logger.info("Starting cookie-based data collection")

            # 실제 REGTECH 사이트 구조에 맞는 블랙리스트 페이지들
            blacklist_urls = [
                "/board/11/boardList",  # 공지사항 게시판 (위협 정보 포함 가능)
                "/fcti/securityAdvisory/advisoryList",  # 보안 권고 목록
                "/fcti/securityAdvisory/blacklistDownload",  # 블랙리스트 다운로드
                "/fcti/threat/threatList",  # 위협 정보 목록
                "/fcti/threat/ipBlacklist",  # IP 블랙리스트
                "/fcti/report/threatReport",  # 위협 리포트
                "/board/boardList?menuCode=FCTI",  # FCTI 관련 게시판
                "/threat/intelligence/ipList",  # 위협 인텔리전스 IP 목록
            ]

            for path in blacklist_urls:
                try:
                    url = f"{self.base_url}{path}"
                    logger.info(f"Trying URL: {url}")

                    response = session.get(
                        url, verify=False, timeout=self.request_timeout
                    )

                    # 쿠키 만료 확인
                    if self.auth_module.is_cookie_expired(response):
                        logger.warning(
                            f"Cookies expired at {url} - will trigger re-extraction"
                        )
                        return []  # 빈 결과 반환하여 상위에서 재추출 트리거

                    if response.status_code == 200:
                        content_type = response.headers.get("content-type", "").lower()

                        # 데이터 프로세서로 위임
                        if "excel" in content_type or "spreadsheet" in content_type:
                            ips = await self.data_processor.process_excel_response(
                                response
                            )
                            if ips:
                                collected_ips.extend(ips)
                                logger.info(
                                    f"Collected {len(ips)} IPs from Excel download"
                                )
                                break

                        elif "text/html" in content_type:
                            ips = await self.data_processor.process_html_response(
                                response
                            )
                            if ips:
                                collected_ips.extend(ips)
                                logger.info(f"Collected {len(ips)} IPs from HTML page")
                                if len(ips) > 10:  # 충분한 데이터가 있으면 중단
                                    break

                        elif "application/json" in content_type:
                            ips = await self.data_processor.process_json_response(
                                response
                            )
                            if ips:
                                collected_ips.extend(ips)
                                logger.info(f"Collected {len(ips)} IPs from JSON API")
                                break

                    elif (
                        response.status_code == 302
                        and "login" in response.headers.get("Location", "")
                    ):
                        logger.warning("Redirected to login - cookies may be expired")
                        break

                except Exception as e:
                    logger.error(f"Error accessing {path}: {e}")
                    continue

            # 수집된 데이터 검증 및 변환
            if collected_ips:
                validated_ips = self.data_processor.validate_and_transform_data(
                    collected_ips
                )
                logger.info(
                    f"Validated {len(validated_ips)} out of {len(collected_ips)} collected IPs"
                )
                return validated_ips
            else:
                logger.warning("No IPs collected - check cookies or access permissions")
                return []

        except Exception as e:
            logger.error(f"Cookie-based collection failed: {e}")
            return []

    async def robust_collect_ips(
        self, session: requests.Session, start_date: str, end_date: str
    ) -> List[Dict[str, Any]]:
        """강화된 IP 수집 로직"""
        all_ips = []
        page = 0
        consecutive_errors = 0
        max_pages = 100  # 안전장치

        logger.info(f"IP 수집 시작: {start_date} ~ {end_date}")

        while page < max_pages and consecutive_errors < self.max_page_errors:
            try:
                # 취소 요청 확인
                if self.validation_utils.should_cancel(
                    getattr(self, "_cancel_event", None)
                ):
                    logger.info("사용자 취소 요청으로 수집 중단")
                    break

                # 페이지 지연
                if page > 0:
                    await asyncio.sleep(self.page_delay)

                # 페이지 데이터 수집
                page_ips = await self.auth_module.request_utils.collect_single_page(
                    session, page, start_date, end_date
                )

                # IP 유효성 검사 적용
                valid_page_ips = []
                for ip_data in page_ips:
                    if self.validation_utils.is_valid_ip(ip_data.get("ip", "")):
                        valid_page_ips.append(ip_data)
                page_ips = valid_page_ips

                if not page_ips:
                    logger.info(f"페이지 {page + 1}에서 더 이상 데이터 없음, 수집 종료")
                    break

                all_ips.extend(page_ips)
                consecutive_errors = 0  # 성공 시 에러 카운트 리셋

                logger.info(f"페이지 {page + 1}: {len(page_ips)}개 수집 (총 {len(all_ips)}개)")
                page += 1

            except requests.exceptions.RequestException as e:
                consecutive_errors += 1
                logger.warning(
                    f"페이지 {page + 1} 수집 실패 (연속 에러: {consecutive_errors}/{self.max_page_errors}): {e}"
                )

                if consecutive_errors < self.max_page_errors:
                    await asyncio.sleep(2 * consecutive_errors)  # 점진적 지연

            except Exception as e:
                consecutive_errors += 1
                logger.error(f"페이지 {page + 1} 처리 중 예상치 못한 오류: {e}")

                if consecutive_errors < self.max_page_errors:
                    await asyncio.sleep(1)

        if consecutive_errors >= self.max_page_errors:
            logger.error(f"연속 페이지 에러 한계 도달 ({self.max_page_errors})")

        # 중복 제거
        unique_ips = self.data_processor.remove_duplicates(all_ips)
        logger.info(f"중복 제거 후 최종 수집: {len(unique_ips)}개 IP")

        return unique_ips

    def transform_data(self, raw_data: dict) -> dict:
        """데이터 변환 - 헬퍼 모듈 위임"""
        return self.data_transform.transform_data(raw_data)

    def validate_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate data for test compatibility"""
        valid_data = []
        for item in data:
            ip = item.get("ip", "")
            if self.validation_utils.is_valid_ip(ip):
                valid_data.append(item)
        return valid_data
