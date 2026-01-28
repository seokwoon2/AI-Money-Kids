# 📱 모바일 웹 배포 가이드

현재 애플리케이션을 모바일 웹에서 다른 사람도 볼 수 있게 하는 방법입니다.

## 방법 1: ngrok 사용 (빠른 테스트용) ⚡

### 장점
- 빠르게 설정 가능 (5분 이내)
- 무료
- 즉시 외부 접근 가능

### 단점
- 무료 버전은 URL이 매번 변경됨
- 세션이 끊기면 URL이 변경됨

### 설정 방법

1. **ngrok 다운로드 및 설치**
   - https://ngrok.com/download 에서 다운로드
   - 또는 Chocolatey 사용: `choco install ngrok`
   - 또는 winget 사용: `winget install ngrok`

2. **ngrok 계정 생성 (무료)**
   - https://dashboard.ngrok.com/signup 에서 가입
   - 인증 토큰 받기

3. **ngrok 인증**
   ```bash
   ngrok config add-authtoken YOUR_AUTH_TOKEN
   ```

4. **Streamlit 앱 실행**
   ```bash
   python -m streamlit run app.py
   ```

5. **새 터미널에서 ngrok 실행**
   ```bash
   ngrok http 8501
   ```

6. **공유 URL 확인**
   - ngrok 터미널에 표시된 `Forwarding` URL 사용
   - 예: `https://abc123.ngrok-free.app`
   - 이 URL을 모바일에서 접속하면 됩니다!

### 주의사항
- ngrok 무료 버전은 브라우저 경고 화면이 나타날 수 있습니다
- "Visit Site" 버튼을 눌러야 접속 가능합니다

---

## 방법 2: Streamlit Cloud 배포 (영구적) 🌐

### 장점
- 완전 무료
- 영구적인 URL 제공
- 자동 HTTPS
- GitHub 연동으로 자동 업데이트

### 단점
- GitHub 계정 필요
- 초기 설정 시간 소요 (15-20분)

### 설정 방법

1. **GitHub에 코드 업로드**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin YOUR_GITHUB_REPO_URL
   git push -u origin main
   ```

2. **Streamlit Cloud 가입**
   - https://streamlit.io/cloud 에서 가입
   - GitHub 계정으로 로그인

3. **앱 배포**
   - "New app" 클릭
   - Repository 선택
   - Main file path: `app.py`
   - Python version: 3.8 이상
   - "Deploy" 클릭

4. **환경 변수 설정**
   - 앱 설정에서 "Secrets" 탭 클릭
   - `.env` 파일 내용 추가:
     ```
     GEMINI_API_KEY=your_gemini_api_key_here
     ```
   - 또는 TOML 형식:
     ```toml
     [secrets]
     GEMINI_API_KEY = "your_gemini_api_key_here"
     ```

5. **배포 완료**
   - 몇 분 후 자동으로 배포됨
   - `https://YOUR_APP_NAME.streamlit.app` URL로 접속 가능
   - 이 URL을 모바일에서 접속하면 됩니다!

---

## 방법 3: 로컬 네트워크 접근 (같은 WiFi) 📶

같은 WiFi에 연결된 기기에서만 접근하려면:

1. **Streamlit 설정 확인**
   - `.streamlit/config.toml`에 `address = "0.0.0.0"` 설정 확인

2. **앱 실행**
   ```bash
   python -m streamlit run app.py
   ```

3. **네트워크 URL 확인**
   - 터미널에 표시된 `Network URL` 사용
   - 예: `http://192.168.1.100:8501`
   - 같은 WiFi에 연결된 모바일에서 이 URL로 접속

### 주의사항
- PC와 모바일이 같은 WiFi에 연결되어 있어야 함
- 방화벽 설정 확인 필요할 수 있음

---

## 추천 방법

- **빠른 테스트**: ngrok 사용
- **영구적 배포**: Streamlit Cloud 사용
- **로컬 테스트**: 같은 WiFi 네트워크 사용

---

## 문제 해결

### 포트가 열리지 않는 경우
```bash
# Windows 방화벽에서 포트 열기
netsh advfirewall firewall add rule name="Streamlit" dir=in action=allow protocol=TCP localport=8501
```

### ngrok 연결 오류
- ngrok 인증 토큰 확인
- 방화벽 설정 확인
- 다른 포트 사용 시: `ngrok http 8502`

### Streamlit Cloud 배포 오류
- `requirements.txt` 파일 확인
- 환경 변수 설정 확인
- 로그 확인: Streamlit Cloud 대시보드에서 "Logs" 탭 확인
