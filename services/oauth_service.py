"""
OAuth 서비스 모듈
카카오, 네이버, 구글 소셜 로그인을 지원합니다.
로컬 환경(.env)과 Streamlit Cloud(secrets) 모두 지원합니다.
"""
import os
import streamlit as st
import requests
from urllib.parse import urlencode
from typing import Optional, Dict

# .env 파일 로드 (로컬 환경용)
try:
    from dotenv import load_dotenv
    # 프로젝트 루트에서 .env 파일 찾기
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    load_dotenv(dotenv_path=env_path, override=True)
    # 현재 디렉토리에서도 시도
    load_dotenv(override=True)
except ImportError:
    # dotenv가 설치되지 않은 경우 무시
    pass
except Exception:
    # .env 파일이 없어도 계속 진행
    pass


class OAuthService:
    """
    OAuth 서비스 클래스
    카카오, 네이버, 구글 소셜 로그인을 처리합니다.
    """
    
    def __init__(self):
        """
        OAuth 서비스 초기화
        환경 변수 로드 순서: .env 파일 우선 → 없으면 Streamlit Secrets
        """
        try:
            # 먼저 .env 파일에서 로드 (로컬 환경)
            self.kakao_key = os.getenv('KAKAO_CLIENT_ID') or None
            self.kakao_redirect = os.getenv('KAKAO_REDIRECT_URI') or 'http://localhost:8501'
            
            self.naver_client_id = os.getenv('NAVER_CLIENT_ID') or None
            self.naver_client_secret = os.getenv('NAVER_CLIENT_SECRET') or None
            self.naver_redirect = os.getenv('NAVER_REDIRECT_URI') or 'http://localhost:8501'
            
            self.google_client_id = os.getenv('GOOGLE_CLIENT_ID') or None
            self.google_client_secret = os.getenv('GOOGLE_CLIENT_SECRET') or None
            self.google_redirect = os.getenv('GOOGLE_REDIRECT_URI') or 'http://localhost:8501'
            
            # .env에 값이 없으면 Streamlit Secrets에서 로드 (Cloud 환경)
            if hasattr(st, 'secrets') and st.secrets:
                try:
                    # 구조 1: st.secrets['oauth']['kakao_client_id']
                    if 'oauth' in st.secrets:
                        # .env에 값이 없을 때만 Secrets 사용
                        if not self.kakao_key and st.secrets.get('oauth', {}).get('kakao_client_id'):
                            self.kakao_key = st.secrets['oauth']['kakao_client_id']
                        if not self.kakao_redirect or self.kakao_redirect == 'http://localhost:8501':
                            if st.secrets.get('oauth', {}).get('kakao_redirect_uri'):
                                self.kakao_redirect = st.secrets['oauth']['kakao_redirect_uri']
                        
                        if not self.naver_client_id and st.secrets.get('oauth', {}).get('naver_client_id'):
                            self.naver_client_id = st.secrets['oauth']['naver_client_id']
                        if not self.naver_client_secret and st.secrets.get('oauth', {}).get('naver_client_secret'):
                            self.naver_client_secret = st.secrets['oauth']['naver_client_secret']
                        if not self.naver_redirect or self.naver_redirect == 'http://localhost:8501':
                            if st.secrets.get('oauth', {}).get('naver_redirect_uri'):
                                self.naver_redirect = st.secrets['oauth']['naver_redirect_uri']
                        
                        if not self.google_client_id and st.secrets.get('oauth', {}).get('google_client_id'):
                            self.google_client_id = st.secrets['oauth']['google_client_id']
                        if not self.google_client_secret and st.secrets.get('oauth', {}).get('google_client_secret'):
                            self.google_client_secret = st.secrets['oauth']['google_client_secret']
                        if not self.google_redirect or self.google_redirect == 'http://localhost:8501':
                            if st.secrets.get('oauth', {}).get('google_redirect_uri'):
                                self.google_redirect = st.secrets['oauth']['google_redirect_uri']
                    # 구조 2: st.secrets['KAKAO_CLIENT_ID'] (직접 접근)
                    else:
                        # .env에 값이 없을 때만 Secrets 사용
                        if not self.kakao_key and st.secrets.get('KAKAO_CLIENT_ID'):
                            self.kakao_key = st.secrets['KAKAO_CLIENT_ID']
                        if not self.kakao_redirect or self.kakao_redirect == 'http://localhost:8501':
                            if st.secrets.get('KAKAO_REDIRECT_URI'):
                                self.kakao_redirect = st.secrets['KAKAO_REDIRECT_URI']
                        
                        if not self.naver_client_id and st.secrets.get('NAVER_CLIENT_ID'):
                            self.naver_client_id = st.secrets['NAVER_CLIENT_ID']
                        if not self.naver_client_secret and st.secrets.get('NAVER_CLIENT_SECRET'):
                            self.naver_client_secret = st.secrets['NAVER_CLIENT_SECRET']
                        if not self.naver_redirect or self.naver_redirect == 'http://localhost:8501':
                            if st.secrets.get('NAVER_REDIRECT_URI'):
                                self.naver_redirect = st.secrets['NAVER_REDIRECT_URI']
                        
                        if not self.google_client_id and st.secrets.get('GOOGLE_CLIENT_ID'):
                            self.google_client_id = st.secrets['GOOGLE_CLIENT_ID']
                        if not self.google_client_secret and st.secrets.get('GOOGLE_CLIENT_SECRET'):
                            self.google_client_secret = st.secrets['GOOGLE_CLIENT_SECRET']
                        if not self.google_redirect or self.google_redirect == 'http://localhost:8501':
                            if st.secrets.get('GOOGLE_REDIRECT_URI'):
                                self.google_redirect = st.secrets['GOOGLE_REDIRECT_URI']
                except Exception as e:
                    # Secrets 접근 실패 시 기존 .env 값 유지
                    pass
            
            # 빈 문자열을 None으로 변환
            if self.kakao_key == '' or (self.kakao_key and self.kakao_key.strip() == ''):
                self.kakao_key = None
            if self.naver_client_id == '' or (self.naver_client_id and self.naver_client_id.strip() == ''):
                self.naver_client_id = None
            if self.google_client_id == '' or (self.google_client_id and self.google_client_id.strip() == ''):
                self.google_client_id = None
            
            # 값이 있으면 공백 제거
            if self.kakao_key:
                self.kakao_key = self.kakao_key.strip()
            if self.naver_client_id:
                self.naver_client_id = self.naver_client_id.strip()
            if self.naver_client_secret:
                self.naver_client_secret = self.naver_client_secret.strip()
            if self.google_client_id:
                self.google_client_id = self.google_client_id.strip()
            if self.google_client_secret:
                self.google_client_secret = self.google_client_secret.strip()
                
        except Exception as e:
            # 모든 초기화 실패 시 기본값
            self.kakao_key = None
            self.kakao_redirect = 'http://localhost:8501'
            self.naver_client_id = None
            self.naver_client_secret = None
            self.naver_redirect = 'http://localhost:8501'
            self.google_client_id = None
            self.google_client_secret = None
            self.google_redirect = 'http://localhost:8501'
    
    # =====================
    # 카카오 로그인
    # =====================
    def get_kakao_login_url(self) -> Optional[str]:
        """
        카카오 로그인 URL 생성
        
        Returns:
            Optional[str]: 카카오 로그인 인가 URL (설정되지 않은 경우 None)
        """
        if not self.kakao_key:
            return None
        
        if not self.kakao_redirect:
            return None
        
        base_url = "https://kauth.kakao.com/oauth/authorize"
        params = {
            'client_id': self.kakao_key,
            'redirect_uri': self.kakao_redirect,
            'response_type': 'code'
        }
        return f"{base_url}?{urlencode(params)}"
    
    def get_kakao_token(self, code: str) -> Dict:
        """
        카카오 액세스 토큰 발급
        
        Args:
            code: 인가 코드
            
        Returns:
            dict: 토큰 정보 (access_token, refresh_token 등)
        """
        if not self.kakao_key:
            return {}
            
        token_url = "https://kauth.kakao.com/oauth/token"
        data = {
            'grant_type': 'authorization_code',
            'client_id': self.kakao_key,
            'redirect_uri': self.kakao_redirect,
            'code': code
        }
        try:
            response = requests.post(token_url, data=data, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            if hasattr(st, 'error'):
                st.error("카카오 토큰 발급 시간 초과: 서버 응답이 지연되었습니다.")
            return {}
        except requests.exceptions.RequestException as e:
            if hasattr(st, 'error'):
                st.error(f"카카오 토큰 발급 실패: {str(e)}")
            return {}
        except Exception as e:
            if hasattr(st, 'error'):
                st.error(f"카카오 토큰 발급 중 오류 발생: {str(e)}")
            return {}
    
    def get_kakao_user_info(self, access_token: str) -> Dict:
        """
        카카오 사용자 정보 조회
        
        Args:
            access_token: 액세스 토큰
            
        Returns:
            dict: 사용자 정보
        """
        if not access_token:
            return {}
            
        user_info_url = "https://kapi.kakao.com/v2/user/me"
        headers = {'Authorization': f'Bearer {access_token}'}
        try:
            response = requests.get(user_info_url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            if hasattr(st, 'error'):
                st.error("카카오 사용자 정보 조회 시간 초과: 서버 응답이 지연되었습니다.")
            return {}
        except requests.exceptions.RequestException as e:
            if hasattr(st, 'error'):
                st.error(f"카카오 사용자 정보 조회 실패: {str(e)}")
            return {}
        except Exception as e:
            if hasattr(st, 'error'):
                st.error(f"카카오 사용자 정보 조회 중 오류 발생: {str(e)}")
            return {}
    
    # =====================
    # 네이버 로그인
    # =====================
    def get_naver_login_url(self) -> Optional[str]:
        """
        네이버 로그인 URL 생성
        
        Returns:
            Optional[str]: 네이버 로그인 인가 URL (설정되지 않은 경우 None)
        """
        if not self.naver_client_id:
            return None
        
        if not self.naver_redirect:
            return None
        
        import secrets
        state = secrets.token_urlsafe(16)
        if hasattr(st, 'session_state'):
            st.session_state['naver_state'] = state
        
        base_url = "https://nid.naver.com/oauth2.0/authorize"
        params = {
            'response_type': 'code',
            'client_id': self.naver_client_id,
            'redirect_uri': self.naver_redirect,
            'state': state
        }
        return f"{base_url}?{urlencode(params)}"
    
    def get_naver_token(self, code: str, state: str) -> Dict:
        """
        네이버 액세스 토큰 발급
        
        Args:
            code: 인가 코드
            state: 상태 값 (CSRF 방지용)
            
        Returns:
            dict: 토큰 정보
        """
        if not self.naver_client_id or not self.naver_client_secret:
            return {}
            
        token_url = "https://nid.naver.com/oauth2.0/token"
        params = {
            'grant_type': 'authorization_code',
            'client_id': self.naver_client_id,
            'client_secret': self.naver_client_secret,
            'code': code,
            'state': state
        }
        try:
            response = requests.get(token_url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            if hasattr(st, 'error'):
                st.error("네이버 토큰 발급 시간 초과: 서버 응답이 지연되었습니다.")
            return {}
        except requests.exceptions.RequestException as e:
            if hasattr(st, 'error'):
                st.error(f"네이버 토큰 발급 실패: {str(e)}")
            return {}
        except Exception as e:
            if hasattr(st, 'error'):
                st.error(f"네이버 토큰 발급 중 오류 발생: {str(e)}")
            return {}
    
    def get_naver_user_info(self, access_token: str) -> Dict:
        """
        네이버 사용자 정보 조회
        
        Args:
            access_token: 액세스 토큰
            
        Returns:
            dict: 사용자 정보
        """
        if not access_token:
            return {}
            
        user_info_url = "https://openapi.naver.com/v1/nid/me"
        headers = {'Authorization': f'Bearer {access_token}'}
        try:
            response = requests.get(user_info_url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            if hasattr(st, 'error'):
                st.error("네이버 사용자 정보 조회 시간 초과: 서버 응답이 지연되었습니다.")
            return {}
        except requests.exceptions.RequestException as e:
            if hasattr(st, 'error'):
                st.error(f"네이버 사용자 정보 조회 실패: {str(e)}")
            return {}
        except Exception as e:
            if hasattr(st, 'error'):
                st.error(f"네이버 사용자 정보 조회 중 오류 발생: {str(e)}")
            return {}
    
    # =====================
    # 구글 로그인
    # =====================
    def get_google_login_url(self) -> Optional[str]:
        """
        구글 로그인 URL 생성
        
        Returns:
            Optional[str]: 구글 로그인 인가 URL (설정되지 않은 경우 None)
        """
        if not self.google_client_id:
            return None
        
        if not self.google_redirect:
            return None
        
        base_url = "https://accounts.google.com/o/oauth2/v2/auth"
        params = {
            'client_id': self.google_client_id,
            'redirect_uri': self.google_redirect,
            'response_type': 'code',
            'scope': 'openid email profile',
            'access_type': 'online'
        }
        return f"{base_url}?{urlencode(params)}"
    
    def get_google_token(self, code: str) -> Dict:
        """
        구글 액세스 토큰 발급
        
        Args:
            code: 인가 코드
            
        Returns:
            dict: 토큰 정보
        """
        if not self.google_client_id or not self.google_client_secret:
            return {}
            
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            'code': code,
            'client_id': self.google_client_id,
            'client_secret': self.google_client_secret,
            'redirect_uri': self.google_redirect,
            'grant_type': 'authorization_code'
        }
        try:
            response = requests.post(token_url, data=data, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            if hasattr(st, 'error'):
                st.error("구글 토큰 발급 시간 초과: 서버 응답이 지연되었습니다.")
            return {}
        except requests.exceptions.RequestException as e:
            if hasattr(st, 'error'):
                st.error(f"구글 토큰 발급 실패: {str(e)}")
            return {}
        except Exception as e:
            if hasattr(st, 'error'):
                st.error(f"구글 토큰 발급 중 오류 발생: {str(e)}")
            return {}
    
    def get_google_user_info(self, access_token: str) -> Dict:
        """
        구글 사용자 정보 조회
        
        Args:
            access_token: 액세스 토큰
            
        Returns:
            dict: 사용자 정보
        """
        if not access_token:
            return {}
            
        user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {'Authorization': f'Bearer {access_token}'}
        try:
            response = requests.get(user_info_url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            if hasattr(st, 'error'):
                st.error("구글 사용자 정보 조회 시간 초과: 서버 응답이 지연되었습니다.")
            return {}
        except requests.exceptions.RequestException as e:
            if hasattr(st, 'error'):
                st.error(f"구글 사용자 정보 조회 실패: {str(e)}")
            return {}
        except Exception as e:
            if hasattr(st, 'error'):
                st.error(f"구글 사용자 정보 조회 중 오류 발생: {str(e)}")
            return {}
