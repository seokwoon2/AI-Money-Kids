"""네트워크 연결 및 API 키 진단 스크립트"""
import os
import socket
from dotenv import load_dotenv
from config import Config

load_dotenv()

print("=" * 50)
print("[진단] 연결 진단 시작")
print("=" * 50)

# 1. API 키 확인
print("\n[1] API 키 확인:")
api_key = Config.GROQ_API_KEY
if api_key:
    print(f"   [OK] API 키 존재: {api_key[:10]}...{api_key[-5:]}")
    if api_key.startswith("gsk_"):
        print("   [OK] API 키 형식 올바름 (gsk_로 시작)")
    else:
        print("   [WARN] API 키 형식 확인 필요 (gsk_로 시작해야 함)")
else:
    print("   [ERROR] API 키가 없습니다!")

# 2. 인터넷 연결 확인
print("\n[2] 인터넷 연결 확인:")
try:
    socket.create_connection(("8.8.8.8", 53), timeout=3)
    print("   [OK] 인터넷 연결 정상")
except OSError:
    print("   [ERROR] 인터넷 연결 실패")

# 3. Groq API 서버 연결 확인
print("\n[3] Groq API 서버 연결 확인:")
try:
    socket.create_connection(("api.groq.com", 443), timeout=5)
    print("   [OK] Groq API 서버 접근 가능")
except OSError as e:
    print(f"   [ERROR] Groq API 서버 접근 실패: {e}")

# 4. Groq SDK 테스트
print("\n[4] Groq SDK 테스트:")
try:
    from groq import Groq
    print("   [OK] Groq SDK 설치됨")
    
    if api_key:
        try:
            client = Groq(api_key=api_key)
            print("   [OK] Groq 클라이언트 생성 성공")
            
            # 간단한 API 호출 테스트
            print("   [TEST] API 호출 테스트 중...")
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": "안녕"}],
                timeout=10.0
            )
            print(f"   [SUCCESS] API 호출 성공!")
            print(f"   [RESPONSE] 응답: {response.choices[0].message.content[:50]}...")
        except Exception as e:
            print(f"   [ERROR] API 호출 실패: {type(e).__name__}")
            print(f"   [DETAIL] 오류 내용: {str(e)[:200]}")
    else:
        print("   [WARN] API 키가 없어서 테스트 불가")
        
except ImportError:
    print("   [ERROR] Groq SDK가 설치되지 않음")
    print("   [TIP] 설치 명령: pip install groq")

print("\n" + "=" * 50)
print("진단 완료")
print("=" * 50)
