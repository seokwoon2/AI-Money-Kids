# 🚀 ngrok 설정 가이드 (상세)

## 3단계: ngrok 인증 🔑

### 3-1. ngrok 계정 생성

1. **웹 브라우저에서 접속**
   - https://dashboard.ngrok.com/signup
   - 또는 https://ngrok.com/ 에서 "Sign up" 클릭

2. **가입 방법 선택**
   - Google 계정으로 가입 (추천)
   - 또는 이메일로 가입

3. **가입 완료 후 대시보드 접속**
   - https://dashboard.ngrok.com/ 접속
   - 로그인 상태 확인

### 3-2. 인증 토큰(Auth Token) 확인

1. **대시보드에서 "Your Authtoken" 섹션 찾기**
   - 대시보드 메인 페이지 상단에 표시됨
   - 또는 왼쪽 메뉴에서 "Your Authtoken" 클릭

2. **토큰 복사**
   - 예시: `2abc123def456ghi789jkl012mno345pqr678stu901vwx234yz`
   - "Copy" 버튼 클릭하여 복사
   - ⚠️ 이 토큰은 비밀번호처럼 중요합니다!

### 3-3. 터미널에서 인증 실행

**방법 1: PowerShell 사용 (Windows)**

1. **PowerShell 열기**
   - Windows 키 누르기
   - "PowerShell" 검색
   - "Windows PowerShell" 실행 (관리자 권한 불필요)

2. **ngrok 설치 확인**
   ```powershell
   ngrok version
   ```
   - 버전이 표시되면 설치 완료
   - 오류가 나면 ngrok이 설치되지 않은 것

3. **인증 토큰 설정**
   ```powershell
   ngrok config add-authtoken YOUR_AUTH_TOKEN_HERE
   ```
   - `YOUR_AUTH_TOKEN_HERE` 부분을 복사한 토큰으로 교체
   - 예시:
     ```powershell
     ngrok config add-authtoken 2abc123def456ghi789jkl012mno345pqr678stu901vwx234yz
     ```

4. **성공 메시지 확인**
   - "Authtoken saved to configuration file" 메시지가 나오면 성공
   - 오류가 나면 토큰을 다시 확인하세요

**방법 2: 명령 프롬프트(CMD) 사용**

1. **CMD 열기**
   - Windows 키 + R
   - "cmd" 입력 후 Enter

2. **동일한 명령어 실행**
   ```cmd
   ngrok config add-authtoken YOUR_AUTH_TOKEN_HERE
   ```

### 3-4. 인증 확인

```powershell
ngrok config check
```

- "Valid" 또는 "Configuration is valid" 메시지가 나오면 성공!

---

## 4단계: Streamlit 앱 실행 🎬

### 4-1. 프로젝트 폴더로 이동

**PowerShell에서:**

1. **현재 위치 확인**
   ```powershell
   pwd
   ```
   - 또는 `Get-Location`

2. **프로젝트 폴더로 이동**
   ```powershell
   cd "C:\Users\JBB\Documents\JB AI Money Kids"
   ```
   - 경로는 실제 프로젝트 위치에 맞게 수정

3. **폴더 내용 확인**
   ```powershell
   ls
   ```
   - `app.py` 파일이 보여야 함

### 4-2. 가상 환경 활성화 (선택사항, 권장)

**가상 환경이 있다면:**

```powershell
# 가상 환경 활성화
.\venv\Scripts\Activate.ps1

# 또는
venv\Scripts\activate
```

**가상 환경이 없다면:**
- 이 단계는 건너뛰어도 됩니다
- 시스템 Python을 사용합니다

### 4-3. Streamlit 실행

**방법 1: python -m streamlit 사용 (권장)**

```powershell
python -m streamlit run app.py
```

**방법 2: streamlit 명령어 직접 사용**

```powershell
streamlit run app.py
```

### 4-4. 실행 확인

터미널에 다음과 같은 메시지가 나타나면 성공:

```
You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.1.100:8501
```

**중요:**
- ✅ 이 터미널 창은 계속 열어두세요!
- ✅ Streamlit이 실행 중이어야 합니다
- ✅ 브라우저가 자동으로 열릴 수 있습니다

### 4-5. 브라우저에서 확인

1. **브라우저 자동 열림 확인**
   - 자동으로 열리지 않으면 수동으로 열기

2. **수동 접속**
   - 브라우저 주소창에 입력: `http://localhost:8501`
   - 앱이 정상적으로 보이면 성공!

---

## 5단계: ngrok 실행 (새 터미널) 🌐

### 5-1. 새 터미널 열기

**중요:** Streamlit이 실행 중인 터미널은 그대로 두고, **새 터미널**을 엽니다!

1. **PowerShell 새 창 열기**
   - Windows 키 누르기
   - "PowerShell" 검색
   - 새 창 실행

### 5-2. ngrok 실행

```powershell
ngrok http 8501
```

**설명:**
- `8501`은 Streamlit의 기본 포트 번호
- 다른 포트를 사용한다면 해당 포트 번호로 변경

### 5-3. ngrok 화면 확인

다음과 같은 화면이 나타납니다:

```
ngrok

Session Status                online
Account                       Your Name (Plan: Free)
Version                       3.x.x
Region                        United States (us)
Latency                       -
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://abc123.ngrok-free.app -> http://localhost:8501

Connections                   ttl     opn     rt1     rt5     p50     p90
                              0       0       0.00    0.00    0.00    0.00
```

**중요한 정보:**
- ✅ **Forwarding** 줄의 `https://abc123.ngrok-free.app` 부분이 공개 URL입니다!
- ✅ 이 URL을 복사해서 다른 사람에게 공유하세요
- ✅ 이 터미널도 계속 열어두어야 합니다

### 5-4. 공개 URL 테스트

1. **모바일 브라우저에서 접속**
   - 복사한 URL 입력 (예: `https://abc123.ngrok-free.app`)
   - 또는 PC 브라우저에서도 테스트 가능

2. **ngrok 경고 화면 (무료 버전)**
   - "Visit Site" 버튼 클릭
   - 또는 "Continue to Site" 버튼 클릭

3. **앱 접속 확인**
   - Streamlit 앱이 정상적으로 보이면 성공!

---

## 전체 실행 순서 요약 📋

### 터미널 1 (Streamlit 실행)
```powershell
# 1. 프로젝트 폴더로 이동
cd "C:\Users\JBB\Documents\JB AI Money Kids"

# 2. Streamlit 실행
python -m streamlit run app.py

# ⚠️ 이 터미널은 계속 열어두세요!
```

### 터미널 2 (ngrok 실행)
```powershell
# 1. ngrok 실행
ngrok http 8501

# ⚠️ 이 터미널도 계속 열어두세요!
# Forwarding URL을 복사해서 공유하세요!
```

---

## 문제 해결 🔧

### ngrok 인증 오류
```
Error: authtoken from https://dashboard.ngrok.com/get-started/your-authtoken
```
- **해결:** 토큰을 다시 확인하고 정확히 복사했는지 확인

### 포트 8501이 이미 사용 중
```
Error: bind: address already in use
```
- **해결:** 다른 Streamlit 프로세스 종료
  ```powershell
  # 포트 사용 중인 프로세스 확인
  netstat -ano | findstr :8501
  
  # 프로세스 종료 (PID는 위 명령어 결과에서 확인)
  taskkill /PID [PID번호] /F
  ```

### ngrok 연결 실패
```
ERR_NGROK_108
```
- **해결:** 
  1. Streamlit이 실행 중인지 확인
  2. 포트 번호가 맞는지 확인 (8501)
  3. 인터넷 연결 확인

### 모바일에서 접속 안 됨
- **해결:**
  1. ngrok 터미널에서 Forwarding URL 확인
  2. URL에 오타가 없는지 확인
  3. "Visit Site" 버튼을 눌렀는지 확인

---

## 완료 체크리스트 ✅

- [ ] ngrok 계정 생성 완료
- [ ] 인증 토큰 설정 완료
- [ ] Streamlit 앱 실행 중
- [ ] ngrok 실행 중
- [ ] Forwarding URL 확인
- [ ] 모바일에서 접속 테스트 완료

---

## 다음 단계 🎯

공개 URL을 받았으면:
1. ✅ 모바일 브라우저에서 테스트
2. ✅ 다른 사람에게 URL 공유
3. ✅ 앱 사용 시작!

**참고:** ngrok 무료 버전은 세션이 끊기면 URL이 변경됩니다. 영구적인 URL이 필요하면 Streamlit Cloud 배포를 고려하세요!
