import os
import streamlit as st
import requests
from urllib.parse import urlencode

class OAuthService:
    def __init__(self):
        # 환경 감지 (로컬 .env 또는 Streamlit Cloud secrets)
        try:
            if hasattr(st, 'secrets') and st.secrets:
                # Streamlit Cloud - 여러 구조 시도
                try:
                    if 'oauth' in st.secrets:
                        # 구조 1: st.secrets['oauth']['kakao_client_id']
                        self.kakao_key = st.secrets.get('oauth', {}).get('kakao_client_id') or st.secrets.get('KAKAO_CLIENT_ID')
                        self.kakao_redirect = st.secrets.get('oauth', {}).get('kakao_redirect_uri') or st.secrets.get('KAKAO_REDIRECT_URI', 'http://localhost:8501')
                        
                        self.naver_client_id = st.secrets.get('oauth', {}).get('naver_client_id') or st.secrets.get('NAVER_CLIENT_ID')
                        self.naver_client_secret = st.secrets.get('oauth', {}).get('naver_client_secret') or st.secrets.get('NAVER_CLIENT_SECRET')
                        self.naver_redirect = st.secrets.get('oauth', {}).get('naver_redirect_uri') or st.secrets.get('NAVER_REDIRECT_URI', 'http://localhost:8501')
                        
                        self.google_client_id = st.secrets.get('oauth', {}).get('google_client_id') or st.secrets.get('GOOGLE_CLIENT_ID')
                        self.google_client_secret = st.secrets.get('oauth', {}).get('google_client_secret') or st.secrets.get('GOOGLE_CLIENT_SECRET')
                        self.google_redirect = st.secrets.get('oauth', {}).get('google_redirect_uri') or st.secrets.get('GOOGLE_REDIRECT_URI', 'http://localhost:8501')
                    else:
                        # 구조 2: st.secrets['KAKAO_CLIENT_ID'] (직접 접근)
                        self.kakao_key = st.secrets.get('KAKAO_CLIENT_ID')
                        self.kakao_redirect = st.secrets.get('KAKAO_REDIRECT_URI', 'http://localhost:8501')
                        
                        self.naver_client_id = st.secrets.get('NAVER_CLIENT_ID')
                        self.naver_client_secret = st.secrets.get('NAVER_CLIENT_SECRET')
                        self.naver_redirect = st.secrets.get('NAVER_REDIRECT_URI', 'http://localhost:8501')
                        
                        self.google_client_id = st.secrets.get('GOOGLE_CLIENT_ID')
                        self.google_client_secret = st.secrets.get('GOOGLE_CLIENT_SECRET')
                        self.google_redirect = st.secrets.get('GOOGLE_REDIRECT_URI', 'http://localhost:8501')
                except Exception:
                    # Secrets 접근 실패 시 환경 변수로 폴백
                    self.kakao_key = os.getenv('KAKAO_CLIENT_ID')
                    self.kakao_redirect = os.getenv('KAKAO_REDIRECT_URI', 'http://localhost:8501')
                    
                    self.naver_client_id = os.getenv('NAVER_CLIENT_ID')
                    self.naver_client_secret = os.getenv('NAVER_CLIENT_SECRET')
                    self.naver_redirect = os.getenv('NAVER_REDIRECT_URI', 'http://localhost:8501')
                    
                    self.google_client_id = os.getenv('GOOGLE_CLIENT_ID')
                    self.google_client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
                    self.google_redirect = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:8501')
            else:
                # 로컬 .env
                self.kakao_key = os.getenv('KAKAO_CLIENT_ID')
                self.kakao_redirect = os.getenv('KAKAO_REDIRECT_URI', 'http://localhost:8501')
                
                self.naver_client_id = os.getenv('NAVER_CLIENT_ID')
                self.naver_client_secret = os.getenv('NAVER_CLIENT_SECRET')
                self.naver_redirect = os.getenv('NAVER_REDIRECT_URI', 'http://localhost:8501')
                
                self.google_client_id = os.getenv('GOOGLE_CLIENT_ID')
                self.google_client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
                self.google_redirect = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:8501')
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
    def get_kakao_login_url(self) -> str:
        """카카오 로그인 URL 생성"""
        if not self.kakao_key:
            raise ValueError("카카오 클라이언트 ID가 설정되지 않았습니다. Streamlit Secrets 또는 .env 파일을 확인해주세요.")
        
        if not self.kakao_redirect:
            raise ValueError("카카오 리다이렉트 URI가 설정되지 않았습니다.")
        
        base_url = "https://kauth.kakao.com/oauth/authorize"
        params = {
            'client_id': self.kakao_key,
            'redirect_uri': self.kakao_redirect,
            'response_type': 'code'
        }
        return f"{base_url}?{urlencode(params)}"
    
    def get_kakao_token(self, code: str) -> dict:
        """카카오 액세스 토큰 발급"""
        token_url = "https://kauth.kakao.com/oauth/token"
        data = {
            'grant_type': 'authorization_code',
            'client_id': self.kakao_key,
            'redirect_uri': self.kakao_redirect,
            'code': code
        }
        try:
            response = requests.post(token_url, data=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"카카오 토큰 발급 실패: {e}")
            return {}
    
    def get_kakao_user_info(self, access_token: str) -> dict:
        """카카오 사용자 정보 조회"""
        user_info_url = "https://kapi.kakao.com/v2/user/me"
        headers = {'Authorization': f'Bearer {access_token}'}
        try:
            response = requests.get(user_info_url, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"카카오 사용자 정보 조회 실패: {e}")
            return {}
    
    # =====================
    # 네이버 로그인
    # =====================
    def get_naver_login_url(self) -> str:
        """네이버 로그인 URL 생성"""
        if not self.naver_client_id:
            raise ValueError("네이버 클라이언트 ID가 설정되지 않았습니다.")
        
        if not self.naver_redirect:
            raise ValueError("네이버 리다이렉트 URI가 설정되지 않았습니다.")
        
        import secrets
        state = secrets.token_urlsafe(16)
        st.session_state['naver_state'] = state
        
        base_url = "https://nid.naver.com/oauth2.0/authorize"
        params = {
            'response_type': 'code',
            'client_id': self.naver_client_id,
            'redirect_uri': self.naver_redirect,
            'state': state
        }
        return f"{base_url}?{urlencode(params)}"
    
    def get_naver_token(self, code: str, state: str) -> dict:
        """네이버 액세스 토큰 발급"""
        token_url = "https://nid.naver.com/oauth2.0/token"
        params = {
            'grant_type': 'authorization_code',
            'client_id': self.naver_client_id,
            'client_secret': self.naver_client_secret,
            'code': code,
            'state': state
        }
        try:
            response = requests.get(token_url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"네이버 토큰 발급 실패: {e}")
            return {}
    
    def get_naver_user_info(self, access_token: str) -> dict:
        """네이버 사용자 정보 조회"""
        user_info_url = "https://openapi.naver.com/v1/nid/me"
        headers = {'Authorization': f'Bearer {access_token}'}
        try:
            response = requests.get(user_info_url, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"네이버 사용자 정보 조회 실패: {e}")
            return {}
    
    # =====================
    # 구글 로그인
    # =====================
    def get_google_login_url(self) -> str:
        """구글 로그인 URL 생성"""
        if not self.google_client_id:
            raise ValueError("구글 클라이언트 ID가 설정되지 않았습니다.")
        
        if not self.google_redirect:
            raise ValueError("구글 리다이렉트 URI가 설정되지 않았습니다.")
        
        base_url = "https://accounts.google.com/o/oauth2/v2/auth"
        params = {
            'client_id': self.google_client_id,
            'redirect_uri': self.google_redirect,
            'response_type': 'code',
            'scope': 'openid email profile',
            'access_type': 'online'
        }
        return f"{base_url}?{urlencode(params)}"
    
    def get_google_token(self, code: str) -> dict:
        """구글 액세스 토큰 발급"""
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            'code': code,
            'client_id': self.google_client_id,
            'client_secret': self.google_client_secret,
            'redirect_uri': self.google_redirect,
            'grant_type': 'authorization_code'
        }
        try:
            response = requests.post(token_url, data=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"구글 토큰 발급 실패: {e}")
            return {}
    
    def get_google_user_info(self, access_token: str) -> dict:
        """구글 사용자 정보 조회"""
        user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {'Authorization': f'Bearer {access_token}'}
        try:
            response = requests.get(user_info_url, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"구글 사용자 정보 조회 실패: {e}")
            return {}
