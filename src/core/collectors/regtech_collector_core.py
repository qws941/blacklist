#!/usr/bin/env python3
"""
REGTECH 컬렉터 메인 모듈
전체 수집 프로세스 조정 및 메인 로직을 담당
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests

from .regtech_collector_auth import RegtechCollectorAuth
from .regtech_collector_data import RegtechCollectorData
from .unified_collector import BaseCollector, CollectionConfig

logger = logging.getLogger(__name__)


class RegtechCollector(BaseCollector):
    """
    BaseCollector를 상속받은 REGTECH 수집기
    모듈화된 구조로 강화된 에러 핸들링과 복구 메커니즘 포함
    """

    def __init__(self, config: Optional[CollectionConfig] = None):
        if config is None:
            config = CollectionConfig()
        super().__init__("REGTECH", config)

        # 기본 설정
        self.base_url = "https://regtech.fsec.or.kr"
        self.config_data = {}

        # Auth manager에서 설정 로드
        from ..auth_manager import get_auth_manager

        auth_manager = get_auth_manager()
        credentials = auth_manager.get_credentials("regtech")

        if credentials:
            self.username = credentials["username"]
            self.password = credentials["password"]
        else:
            # Fallback to env vars if needed
            self.username = os.getenv("REGTECH_USERNAME")
            self.password = os.getenv("REGTECH_PASSWORD")

        # DB에서 설정 로드 (선택적)
        self._load_db_config()

        # 에러 핸들링 설정
        self.session_retry_limit = 3
        self.current_session = None
        self.total_collected = 0

        # 모듈화된 컴포넌트들 초기화
        self.auth_module = RegtechCollectorAuth(
            self.base_url, self.username, self.password
        )
        self.data_module = RegtechCollectorData(
            self.base_url, self.auth_module, self.auth_module.validation_utils
        )

        logger.info("REGTECH collector initialized with modular components")

    def _load_db_config(self):
        """DB에서 설정 로드 (선택적)"""
        try:
            from ..database.collection_settings import CollectionSettingsDB

            self.db = CollectionSettingsDB()

            # DB에서 REGTECH 설정 가져오기
            source_config = self.db.get_source_config("regtech")
            credentials = self.db.get_credentials("regtech")

            if source_config:
                self.base_url = source_config.get("base_url", self.base_url)
                self.config_data = source_config.get("config", {})

            if credentials:
                self.username = credentials["username"]
                self.password = credentials["password"]
            else:
                # 환경변수 fallback
                self.username = os.getenv("REGTECH_USERNAME")
                self.password = os.getenv("REGTECH_PASSWORD")

        except ImportError:
            # DB 없으면 기본값/환경변수 사용
            self.base_url = "https://regtech.fsec.or.kr"
            self.username = os.getenv("REGTECH_USERNAME")
            self.password = os.getenv("REGTECH_PASSWORD")
            self.config_data = {}

    def set_cookie_string(self, cookie_string: str):
        """외부에서 쿠키 문자열 설정"""
        self.auth_module.set_cookie_string(cookie_string)
        logger.info("Cookie string updated through auth module")

    @property
    def source_type(self) -> str:
        return "REGTECH"

    async def _collect_data(self) -> List[Any]:
        """
        메인 데이터 수집 메서드 - 자동 쿠키 관리 포함
        """
        # 1. 쿠키가 없으면 자동 추출 시도
        if not self.auth_module.cookie_auth_mode:
            logger.info("🔄 No cookies available - attempting automatic extraction...")
            cookie_string = self.auth_module.auto_extract_cookies()
            if cookie_string:
                self.auth_module.set_cookie_string(cookie_string)
                logger.info("✅ Automatic cookie extraction successful")
            else:
                logger.warning(
                    "❌ Automatic cookie extraction failed - falling back to login mode"
                )
                return await self._collect_with_login()

        # 2. 쿠키 기반 수집 시도
        if self.auth_module.cookie_auth_mode:
            collected_data = await self.data_module.collect_with_cookies()

            # 3. 수집 결과가 없거나 쿠키 만료 의심 시 재추출 시도
            if not collected_data:
                logger.warning(
                    "🔄 No data collected - cookies might be expired, attempting re-extraction..."
                )
                cookie_string = self.auth_module.auto_extract_cookies()
                if cookie_string:
                    self.auth_module.set_cookie_string(cookie_string)
                    logger.info(
                        "✅ Cookie re-extraction successful - retrying collection..."
                    )
                    collected_data = await self.data_module.collect_with_cookies()
                else:
                    logger.error(
                        "❌ Cookie re-extraction failed - falling back to login mode"
                    )
                    return await self._collect_with_login()

            return collected_data
        else:
            return await self._collect_with_login()

    async def _collect_with_login(self) -> List[Any]:
        """기존 로그인 기반 데이터 수집"""
        collected_ips = []
        session_retry_count = 0

        while session_retry_count < self.session_retry_limit:
            try:
                # 세션 초기화
                session = self.auth_module.create_session()
                self.current_session = session

                # 로그인 시도
                if not self.auth_module.robust_login(session):
                    raise Exception("로그인 실패 후 재시도 한계 도달")

                # 데이터 수집
                start_date, end_date = self.data_module.data_transform.get_date_range(
                    self.config
                )
                collected_ips = await self.data_module.robust_collect_ips(
                    session, start_date, end_date
                )

                # 성공적으로 수집 완료
                logger.info(f"REGTECH 수집 완료: {len(collected_ips)}개 IP")

                # 데이터베이스에 저장
                if collected_ips:
                    saved_count = self.save_to_database(collected_ips)
                    logger.info(f"✅ PostgreSQL에 {saved_count}개 IP 저장 완료")
                else:
                    logger.warning("⚠️ 저장할 IP 데이터가 없습니다")

                break

            except requests.exceptions.ConnectionError as e:
                session_retry_count += 1
                logger.warning(
                    f"연결 오류 (재시도 {session_retry_count}/{self.session_retry_limit}): {e}"
                )
                if session_retry_count < self.session_retry_limit:
                    await asyncio.sleep(5 * session_retry_count)  # 지수적 백오프

            except requests.exceptions.Timeout as e:
                session_retry_count += 1
                logger.warning(
                    f"타임아웃 오류 (재시도 {session_retry_count}/{self.session_retry_limit}): {e}"
                )
                if session_retry_count < self.session_retry_limit:
                    await asyncio.sleep(3 * session_retry_count)

            except Exception as e:
                logger.error(f"예상치 못한 오류: {e}")
                session_retry_count += 1
                if session_retry_count < self.session_retry_limit:
                    await asyncio.sleep(2 * session_retry_count)

            finally:
                if hasattr(self, "current_session") and self.current_session:
                    self.current_session.close()
                    self.current_session = None

        if session_retry_count >= self.session_retry_limit:
            raise Exception(f"최대 재시도 횟수 ({self.session_retry_limit}) 초과")

        return collected_ips

    def save_to_database(self, collected_ips: List[Dict[str, Any]]) -> int:
        """수집된 IP 데이터를 PostgreSQL에 저장"""
        if not collected_ips:
            logger.warning("저장할 IP 데이터가 없습니다")
            return 0

        try:
            import psycopg2
            from datetime import datetime

            # PostgreSQL 연결
            conn = psycopg2.connect(
                host="blacklist-postgres",
                database="blacklist",
                user="postgres",
                password="postgres",
            )
            cur = conn.cursor()

            # 기존 REGTECH 데이터 정리 (선택사항 - 중복 방지)
            cur.execute("DELETE FROM blacklist_ips WHERE source = 'REGTECH'")
            logger.info(f"기존 REGTECH 데이터 {cur.rowcount}개 정리")

            # 새 데이터 일괄 삽입
            saved_count = 0
            batch_data = []

            for ip_data in collected_ips:
                ip = ip_data.get("ip")
                if not ip:
                    continue

                # 데이터 준비
                country = ip_data.get("country", "Unknown")
                attack_type = ip_data.get("attack_type", "blacklist")
                detection_date = ip_data.get("detection_date")
                threat_level = ip_data.get("threat_level", "MEDIUM")

                # 날짜 형식 변환
                if isinstance(detection_date, str):
                    try:
                        if len(detection_date) == 8:  # YYYYMMDD
                            detection_date = datetime.strptime(
                                detection_date, "%Y%m%d"
                            ).date()
                        else:  # YYYY-MM-DD
                            detection_date = datetime.strptime(
                                detection_date, "%Y-%m-%d"
                            ).date()
                    except:
                        detection_date = datetime.now().date()
                elif not detection_date:
                    detection_date = datetime.now().date()

                batch_data.append(
                    (
                        ip,  # ip_address
                        "REGTECH",  # source
                        detection_date,  # detection_date
                        threat_level,  # threat_level
                        country,  # country
                        attack_type,  # attack_type or reason
                        datetime.now(),  # created_at
                        datetime.now(),  # updated_at
                    )
                )

            # 일괄 삽입
            if batch_data:
                cur.executemany(
                    """
                    INSERT INTO blacklist_ips 
                    (ip_address, source, detection_date, threat_level, country, notes, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                    batch_data,
                )

                saved_count = cur.rowcount
                conn.commit()

                logger.info(f"✅ PostgreSQL에 {saved_count}개 IP 저장 완료")

            conn.close()
            return saved_count

        except Exception as e:
            logger.error(f"❌ 데이터베이스 저장 실패: {e}")
            if "conn" in locals():
                try:
                    conn.rollback()
                    conn.close()
                except:
                    pass
            return 0

    def collect_from_web(
        self, start_date: str = None, end_date: str = None
    ) -> Dict[str, Any]:
        """
        웹 수집 인터페이스 메서드 (동기 래퍼)
        collection_service.py에서 호출하는 인터페이스
        """
        import asyncio

        try:
            # 날짜 범위 설정
            if not start_date or not end_date:
                end_date = datetime.now().strftime("%Y-%m-%d")
                start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

            # 비동기 수집 실행
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                collected_data = loop.run_until_complete(self._collect_data())
                return {
                    "success": True,
                    "data": collected_data,
                    "count": len(collected_data),
                    "message": f"REGTECH에서 {len(collected_data)}개 IP 수집 완료",
                }
            finally:
                loop.close()

        except Exception as e:
            logger.error(f"REGTECH 웹 수집 실패: {e}")
            return {
                "success": False,
                "data": [],
                "count": 0,
                "error": str(e),
                "message": f"REGTECH 수집 중 오류: {e}",
            }

    # Test compatibility methods
    def get_config(self) -> Dict[str, Any]:
        """Get configuration for test compatibility"""
        return {
            "base_url": self.base_url,
            "username": self.username,
            "enabled": self.config.enabled,
            **self.config_data,
        }

    def set_config(self, config: Dict[str, Any]):
        """Set configuration for test compatibility"""
        self.config_data.update(config)

    def _create_session(self) -> requests.Session:
        """Create session for test compatibility"""
        return self.auth_module.create_session()

    def _validate_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate data for test compatibility"""
        return self.data_module.validate_data(data)

    def _handle_error(self, message: str, error: Exception):
        """Handle error for test compatibility"""
        self.logger.error(f"{message}: {error}")

    def _transform_data(self, raw_data: dict) -> dict:
        """데이터 변환 - 헬퍼 모듈 위임"""
        return self.data_module.transform_data(raw_data)
