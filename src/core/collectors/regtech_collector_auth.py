#!/usr/bin/env python3
"""
REGTECH 인증 및 세션 관리 모듈
인증, 쿠키 관리, 세션 생성 등의 기능을 담당
"""

import logging
from typing import Optional

import requests

from ..common.ip_utils import IPUtils
from .helpers.request_utils import RegtechRequestUtils
from .helpers.validation_utils import RegtechValidationUtils
from .regtech_auth import RegtechAuth
from .regtech_browser import RegtechBrowserAutomation

logger = logging.getLogger(__name__)


class RegtechCollectorAuth:
    """
    REGTECH 수집기의 인증 관련 기능을 담당하는 모듈
    """

    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.request_timeout = 30

        # 모듈화된 컴포넌트들 초기화
        self.auth = RegtechAuth(self.base_url, self.username, self.password)
        self.browser_automation = RegtechBrowserAutomation(
            self.base_url, self.username, self.password
        )

        # Helper 객체들 초기화
        self.request_utils = RegtechRequestUtils(self.base_url, self.request_timeout)
        self.validation_utils = RegtechValidationUtils()
        self.validation_utils.set_ip_utils(IPUtils)

        logger.info("REGTECH authentication module initialized")

    def set_cookie_string(self, cookie_string: str):
        """외부에서 쿠키 문자열 설정"""
        self.auth.set_cookie_string(cookie_string)
        logger.info("Cookie string updated through auth module")

    def get_authenticated_session(self) -> Optional[requests.Session]:
        """인증된 세션 반환"""
        if self.auth.cookie_auth_mode:
            return self.auth.create_authenticated_session()
        return None

    def robust_login(self, session: requests.Session) -> bool:
        """강화된 로그인 로직 - 인증 모듈로 위임"""
        return self.auth.robust_login(session)

    def auto_extract_cookies(self) -> Optional[str]:
        """자동 쿠키 추출"""
        return self.browser_automation.auto_extract_cookies()

    def is_cookie_expired(self, response: requests.Response) -> bool:
        """쿠키 만료 확인"""
        return self.auth._is_cookie_expired(response)

    def create_session(self) -> requests.Session:
        """새 세션 생성"""
        return self.request_utils.create_session()

    @property
    def cookie_auth_mode(self) -> bool:
        """쿠키 인증 모드 여부"""
        return self.auth.cookie_auth_mode
