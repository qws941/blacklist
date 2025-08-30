#!/usr/bin/env python3
"""
REGTECH 브라우저 자동화 모듈
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class RegtechBrowserAutomation:
    """REGTECH 브라우저 자동화 클래스"""

    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url
        self.username = username
        self.password = password

    def auto_extract_cookies(self) -> Optional[str]:
        """자동 쿠키 추출 (현재는 파일에서 로드)"""
        try:
            # 저장된 쿠키 파일에서 로드
            cookie_file_paths = [
                "data/regtech_cookies.json",
                "instance/regtech_cookies.json",
                "/home/jclee/app/blacklist/data/regtech_cookies.json",
            ]

            for cookie_file in cookie_file_paths:
                try:
                    import json

                    with open(cookie_file, "r", encoding="utf-8") as f:
                        cookie_data = json.load(f)
                        cookie_string = cookie_data.get("cookie_string")
                        if cookie_string:
                            logger.info(f"Cookie loaded from {cookie_file}")
                            return cookie_string
                except FileNotFoundError:
                    continue
                except Exception as e:
                    logger.error(f"Error reading {cookie_file}: {e}")
                    continue

            logger.warning("No valid cookie files found")
            return None

        except Exception as e:
            logger.error(f"Cookie extraction failed: {e}")
            return None
