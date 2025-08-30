#!/usr/bin/env python3
"""
REGTECH 인증 모듈
"""

import logging
import json
import os
from typing import Optional
import requests

logger = logging.getLogger(__name__)


class RegtechAuth:
    """REGTECH 인증 처리 클래스"""

    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.cookie_auth_mode = False
        self.cookies = {}

    def set_cookie_string(self, cookie_string: str):
        """쿠키 문자열 설정"""
        try:
            if cookie_string:
                # 쿠키 문자열을 딕셔너리로 파싱
                cookie_pairs = cookie_string.split(";")
                cookies = {}
                for pair in cookie_pairs:
                    if "=" in pair:
                        key, value = pair.strip().split("=", 1)
                        cookies[key] = value

                self.cookies = cookies
                self.cookie_auth_mode = True
                logger.info("Cookie authentication mode enabled")
            else:
                self.cookie_auth_mode = False
                logger.warning("Empty cookie string provided")

        except Exception as e:
            logger.error(f"Failed to set cookies: {e}")
            self.cookie_auth_mode = False

    def create_authenticated_session(self) -> Optional[requests.Session]:
        """인증된 세션 생성"""
        if not self.cookie_auth_mode:
            return None

        session = requests.Session()
        session.cookies.update(self.cookies)
        session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

        return session

    def robust_login(self, session: requests.Session) -> bool:
        """강화된 로그인 시도"""
        try:
            login_url = f"{self.base_url}/login"
            login_data = {"username": self.username, "password": self.password}

            response = session.post(
                login_url,
                data=login_data,
                verify=False,
                timeout=30,
                allow_redirects=False,
            )

            # 로그인 성공 확인
            if response.status_code in [200, 302]:
                logger.info("Login successful")
                return True
            else:
                logger.error(f"Login failed with status: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False

    def _is_cookie_expired(self, response: requests.Response) -> bool:
        """쿠키 만료 확인"""
        # 로그인 페이지로 리다이렉트되거나 401 에러면 만료된 것으로 판단
        if response.status_code == 401:
            return True
        if response.status_code == 302:
            location = response.headers.get("Location", "")
            if "login" in location.lower():
                return True
        return False

    def create_session(self) -> requests.Session:
        """새 세션 생성"""
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )
        return session
