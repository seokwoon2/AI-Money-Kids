import requests
import streamlit as st
import os
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

class OAuthService:
    """카카오 OAuth 로그인 서비스"""
    
    def __init__(self):
        # 로컬 .env 또는 Streamlit Secrets에서 키 가져오기
        if hasattr(st, 'secrets') and "KAKAO_REST_API_KEY" in st.secrets:
            self.client_id = st.secrets["KAKAO_REST_API_KEY"]
            self.redirect_uri = st.secrets["KAKAO_REDIRECT_URI"]
        else:
            self.client_id = os.getenv("KAKAO_REST_API_KEY")
            self.redirect_uri = os.getenv("KAKAO_REDIRECT_URI", "http://localhost:8501")

    def get_kakao_login_url(self):
        """카카오 로그인 인가 코드 요청 URL 생성"""
        return f"https://kauth.kakao.com/oauth/authorize?client_id={self.client_id}&redirect_uri={self.redirect_uri}&response_type=code"

    def get_kakao_token(self, code):
        """인가 코드로 액세스 토큰 발급"""
        url = "https://kauth.kakao.com/oauth/token"
        headers = {"Content-type": "application/x-www-form-urlencoded;charset=utf-8"}
        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "code": code,
        }
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"토큰 발급 실패: {response.json()}")
            return None

    def get_kakao_user_info(self, access_token):
        """액세스 토큰으로 사용자 정보 가져오기"""
        url = "https://kapi.kakao.com/v2/user/me"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-type": "application/x-www-form-urlencoded;charset=utf-8",
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"사용자 정보 요청 실패: {response.json()}")
            return None

    def kakao_logout(self, access_token):
        """카카오 로그아웃"""
        url = "https://kapi.kakao.com/v1/user/logout"
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.post(url, headers=headers)
        return response.status_code == 200
