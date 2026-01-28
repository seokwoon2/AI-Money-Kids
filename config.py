import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """애플리케이션 설정"""
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    DATABASE_PATH = "data/money_kids.db"
    MODEL = "models/gemini-2.5-flash"  # Gemini 2.5 Flash 모델 (사용자가 요청한 모델)
    
    # 데이터 디렉토리 생성
    DATA_DIR = "data"
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
