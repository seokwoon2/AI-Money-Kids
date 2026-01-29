import requests
import streamlit as st
import os
from dotenv import load_dotenv
from typing import Optional, Dict

# 환경변수 로드
load_dotenv()

class OAuthService:
    """카카오 OAuth 로그인 서비스"""
    
    def __init__(self):
        # 로컬 .env 또는 Streamlit Secrets에서 키 가져오기
        try:
            # Streamlit Secrets 확인 (런타임에만 가능)
            if hasattr(st, 'secrets'):
                try:
                    if "KAKAO_REST_API_KEY" in st.secrets:
                        self.client_id = st.secrets["KAKAO_REST_API_KEY"]
                        self.redirect_uri = st.secrets.get("KAKAO_REDIRECT_URI", "http://localhost:8501")
                    else:
                        # Secrets에 없으면 환경 변수에서 가져오기
                        self.client_id = os.getenv("KAKAO_REST_API_KEY")
                        self.redirect_uri = os.getenv("KAKAO_REDIRECT_URI", "http://localhost:8501")
                except (AttributeError, KeyError, RuntimeError):
                    # Secrets 접근 실패 시 환경 변수 사용
                    self.client_id = os.getenv("KAKAO_REST_API_KEY")
                    self.redirect_uri = os.getenv("KAKAO_REDIRECT_URI", "http://localhost:8501")
            else:
                # Streamlit이 초기화되지 않았으면 환경 변수만 사용
                self.client_id = os.getenv("KAKAO_REST_API_KEY")
                self.redirect_uri = os.getenv("KAKAO_REDIRECT_URI", "http://localhost:8501")
        except Exception:
            # 모든 초기화 실패 시 기본값 설정
            self.client_id = os.getenv("KAKAO_REST_API_KEY")
            self.redirect_uri = os.getenv("KAKAO_REDIRECT_URI", "http://localhost:8501")

    def get_kakao_login_url(self) -> str:
        """카카오 로그인 인가 코드 요청 URL 생성"""
        return f"https://kauth.kakao.com/oauth/authorize?client_id={self.client_id}&redirect_uri={self.redirect_uri}&response_type=code"

    def get_kakao_token(self, code: str) -> Optional[str]:
        """인가 코드로 액세스 토큰 발급"""
        token_url = "https://kauth.kakao.com/oauth/token"
        headers = {"Content-type": "application/x-www-form-urlencoded;charset=utf-8"}
        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "code": code,
        }
        
        try:
            response = requests.post(token_url, headers=headers, data=data)
            response.raise_for_status()
            tokens = response.json()
            return tokens.get("access_token")
        except Exception as e:
            st.error(f"토큰 발급 실패: {str(e)}")
            return None

    def get_kakao_user_info(self, access_token: str) -> Optional[Dict]:
        """액세스 토큰으로 사용자 정보 가져오기"""
        user_info_url = "https://kapi.kakao.com/v2/user/me"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-type": "application/x-www-form-urlencoded;charset=utf-8",
        }
        
        try:
            response = requests.get(user_info_url, headers=headers)
            response.raise_for_status()
            user_info = response.json()
            
            # 기존 코드와의 호환성을 위해 원본 형식도 반환
            # 하지만 정제된 형식도 함께 제공
            return {
                "id": str(user_info.get("id")),
                "name": user_info.get("properties", {}).get("nickname", "사용자"),
                "profile_image": user_info.get("properties", {}).get("profile_image"),
                "email": user_info.get("kakao_account", {}).get("email"),
                "provider": "kakao",
                # 기존 코드 호환성
                "properties": user_info.get("properties", {}),
                "kakao_account": user_info.get("kakao_account", {})
            }
        except Exception as e:
            st.error(f"사용자 정보 가져오기 실패: {str(e)}")
            return None

    def kakao_logout(self, access_token: str) -> bool:
        """카카오 로그아웃"""
        logout_url = "https://kapi.kakao.com/v1/user/logout"
        headers = {"Authorization": f"Bearer {access_token}"}
        
        try:
            response = requests.post(logout_url, headers=headers)
            response.raise_for_status()
            return True
        except Exception:
            return False
