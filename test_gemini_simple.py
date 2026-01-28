"""Gemini API 간단 테스트"""
import os
from dotenv import load_dotenv
from config import Config

load_dotenv()

print("[테스트] Gemini API 연결 테스트 시작...")
print(f"[API 키] {Config.GEMINI_API_KEY[:20] if Config.GEMINI_API_KEY else '없음'}...")

if not Config.GEMINI_API_KEY:
    print("[ERROR] API 키가 없습니다!")
    exit(1)

try:
    import google.generativeai as genai
    print("[OK] google.generativeai 모듈 로드 성공")
except ImportError as e:
    print(f"[ERROR] 모듈 로드 실패: {e}")
    print("[TIP] pip install google-generativeai 실행 필요")
    exit(1)

try:
    genai.configure(api_key=Config.GEMINI_API_KEY)
    print("[OK] API 설정 성공")
    
    model = genai.GenerativeModel("gemini-1.5-flash")
    print("[OK] 모델 생성 성공")
    
    print("[TEST] API 호출 중...")
    response = model.generate_content("저축은 왜 중요해? 초등학생도 이해할 수 있는 자연스러운 한국어로 설명해줘.")
    
    if hasattr(response, 'text') and response.text:
        print("\n[SUCCESS] 응답 받음:")
        print("-" * 50)
        print(response.text)
        print("-" * 50)
    else:
        print("[ERROR] 응답이 비어있음")
        print(f"Response type: {type(response)}")
        print(f"Response attributes: {[x for x in dir(response) if not x.startswith('_')][:10]}")
        
except Exception as e:
    print(f"\n[ERROR] {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()
