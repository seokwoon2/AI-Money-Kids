import os
from dotenv import load_dotenv

# .env 파일 로드 (로컬 환경에서만 작동)
load_dotenv()

def get_gemini_api_key():
    """Gemini API 키를 가져오는 함수 (로컬 .env 또는 Streamlit Cloud Secrets)"""
    # Streamlit Cloud Secrets 확인 (런타임에만 가능)
    try:
        import streamlit as st
        if hasattr(st, 'secrets'):
            try:
                # Streamlit Cloud Secrets에서 가져오기
                if hasattr(st.secrets, 'GEMINI_API_KEY'):
                    return st.secrets.GEMINI_API_KEY
                elif 'GEMINI_API_KEY' in st.secrets:
                    return st.secrets['GEMINI_API_KEY']
            except (AttributeError, KeyError, TypeError):
                pass
    except (ImportError, RuntimeError):
        pass
    
    # 환경 변수에서 가져오기 (.env 파일 또는 시스템 환경 변수)
    return os.getenv("GEMINI_API_KEY", "")

class Config:
    """애플리케이션 설정"""
    
    @staticmethod
    def get_gemini_api_key():
        """Gemini API 키를 동적으로 가져오기"""
        return get_gemini_api_key()
    
    @property
    def GEMINI_API_KEY(self):
        """Gemini API 키 속성 (동적 읽기)"""
        return get_gemini_api_key()
    
    DATABASE_PATH = "data/money_kids.db"
    MODEL = "models/gemini-2.5-flash"  # Gemini 2.5 Flash 모델 (사용자가 요청한 모델)
    
    # 데이터 디렉토리 생성
    DATA_DIR = "data"
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
