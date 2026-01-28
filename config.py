import os
from dotenv import load_dotenv

# .env 파일 로드 (로컬 환경에서만 작동)
load_dotenv()

# Streamlit Cloud의 Secrets 지원
def get_gemini_api_key():
    """Gemini API 키를 가져오는 함수 (로컬 .env 또는 Streamlit Cloud Secrets)"""
    try:
        import streamlit as st
        # Streamlit이 실행 중이고 Secrets가 있는 경우
        if hasattr(st, 'secrets'):
            try:
                # Streamlit Cloud Secrets에서 가져오기
                if 'GEMINI_API_KEY' in st.secrets:
                    return st.secrets['GEMINI_API_KEY']
            except:
                pass
    except:
        pass
    
    # 환경 변수에서 가져오기 (.env 파일 또는 시스템 환경 변수)
    return os.getenv("GEMINI_API_KEY", "")

class Config:
    """애플리케이션 설정"""
    GEMINI_API_KEY = get_gemini_api_key()
    DATABASE_PATH = "data/money_kids.db"
    MODEL = "models/gemini-2.5-flash"  # Gemini 2.5 Flash 모델 (사용자가 요청한 모델)
    
    # 데이터 디렉토리 생성
    DATA_DIR = "data"
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
