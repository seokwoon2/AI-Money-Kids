# 🌐 모바일 접근 대안 방법

ngrok이 작동하지 않을 때 사용할 수 있는 다른 방법들입니다.

## 방법 1: 로컬 네트워크 접근 (가장 간단) 📶

같은 WiFi에 연결된 기기에서만 접근 가능합니다.

### 설정 방법

1. **Streamlit 실행**
   ```powershell
   python -m streamlit run app.py
   ```

2. **Network URL 확인**
   터미널에 다음과 같이 표시됩니다:
   ```
   Network URL: http://192.168.1.100:8501
   ```
   (IP 주소는 다를 수 있습니다)

3. **모바일에서 접속**
   - 모바일이 **같은 WiFi**에 연결되어 있어야 합니다
   - 모바일 브라우저에서 Network URL 입력
   - 예: `http://192.168.1.100:8501`

### 장점
- ✅ 추가 프로그램 설치 불필요
- ✅ 즉시 사용 가능
- ✅ 무료

### 단점
- ❌ 같은 WiFi에 연결되어 있어야 함
- ❌ 인터넷을 통한 원격 접근 불가

---

## 방법 2: localtunnel 사용 (ngrok 대안) 🚇

ngrok과 비슷하지만 더 간단합니다.

### 설치 및 실행

1. **npm 설치 (없다면)**
   - Node.js 다운로드: https://nodejs.org/
   - 설치 후 터미널 재시작

2. **localtunnel 설치**
   ```powershell
   npm install -g localtunnel
   ```

3. **Streamlit 실행** (다른 터미널)
   ```powershell
   python -m streamlit run app.py
   ```

4. **localtunnel 실행**
   ```powershell
   lt --port 8501
   ```

5. **공개 URL 확인**
   ```
   your url is: https://abc123.loca.lt
   ```
   이 URL을 모바일에서 접속하세요!

### 장점
- ✅ ngrok보다 간단
- ✅ 추가 인증 불필요
- ✅ 무료

---

## 방법 3: Streamlit Cloud 배포 (영구적, 추천) ☁️

가장 안정적이고 영구적인 방법입니다.

### 빠른 배포 가이드

1. **GitHub에 코드 업로드**
   - GitHub 계정 필요 (없으면 https://github.com 가입)
   - 새 저장소 생성
   - 코드 업로드

2. **Streamlit Cloud 배포**
   - https://streamlit.io/cloud 접속
   - GitHub로 로그인
   - "New app" 클릭
   - Repository 선택
   - Main file: `app.py`
   - "Deploy" 클릭

3. **환경 변수 설정**
   - 앱 설정 → Secrets
   - 다음 내용 추가:
     ```toml
     [secrets]
     GEMINI_API_KEY = "your_api_key_here"
     ```

4. **완료!**
   - `https://YOUR_APP_NAME.streamlit.app` URL로 접속 가능
   - 이 URL을 모바일에서 접속하세요!

### 장점
- ✅ 완전 무료
- ✅ 영구적인 URL
- ✅ 자동 HTTPS
- ✅ 인터넷 어디서나 접근 가능

---

## 방법 4: Python http.server 사용 (간단한 테스트용)

Streamlit이 아닌 정적 파일만 공유할 때 사용합니다.

```powershell
# 프로젝트 폴더에서
python -m http.server 8000
```

하지만 Streamlit 앱에는 적합하지 않습니다.

---

## 추천 순서

1. **빠른 테스트**: 로컬 네트워크 접근 (방법 1)
2. **외부 접근 필요**: localtunnel (방법 2)
3. **영구적 배포**: Streamlit Cloud (방법 3)

---

## 문제 해결

### 로컬 네트워크 접근이 안 될 때
- PC와 모바일이 같은 WiFi에 연결되어 있는지 확인
- 방화벽 설정 확인:
  ```powershell
  netsh advfirewall firewall add rule name="Streamlit" dir=in action=allow protocol=TCP localport=8501
  ```

### localtunnel이 안 될 때
- Node.js가 설치되어 있는지 확인: `node --version`
- 포트 번호 확인: `lt --port 8501`
