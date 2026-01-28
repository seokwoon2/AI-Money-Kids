# 🔐 Streamlit Cloud Secrets 설정 가이드

## 문제 해결: API 키 설정

Streamlit Cloud에서는 `.env` 파일을 사용할 수 없습니다. 대신 **Secrets**를 사용해야 합니다.

---

## Secrets 설정 방법

### 1단계: Streamlit Cloud 대시보드 접속

터미널에서:
```powershell
start https://share.streamlit.io
```

또는 브라우저에서 직접: https://share.streamlit.io

### 2단계: 앱 설정으로 이동

1. **앱 목록에서 배포한 앱 클릭**
2. **오른쪽 상단의 "⚙️" 아이콘 클릭**
   - 또는 "Manage app" → "Settings"

### 3단계: Secrets 탭 선택

- 왼쪽 메뉴에서 **"Secrets"** 클릭
- 또는 "Secrets" 탭 클릭

### 4단계: 환경 변수 입력

**다음 내용을 정확히 입력하세요:**

```toml
[secrets]
GEMINI_API_KEY = "AIzaSyAFTERBd0vyHCKWckgeXbubZ6tm9sjr-i8"
```

**중요:**
- `[secrets]`는 반드시 포함해야 합니다
- `GEMINI_API_KEY`는 대문자로 정확히 입력
- API 키는 따옴표로 감싸야 합니다
- `.env` 파일의 실제 API 키 값을 사용하세요

### 5단계: 저장

- **"Save"** 또는 **"저장"** 버튼 클릭
- 앱이 자동으로 재시작됩니다
- 몇 초 후 앱이 정상 작동합니다

---

## 입력 형식 확인

### ✅ 올바른 형식:
```toml
[secrets]
GEMINI_API_KEY = "AIzaSyAFTERBd0vyHCKWckgeXbubZ6tm9sjr-i8"
```

### ❌ 잘못된 형식들:
```toml
# 따옴표 없음
GEMINI_API_KEY = AIzaSyAFTERBd0vyHCKWckgeXbubZ6tm9sjr-i8

# [secrets] 없음
GEMINI_API_KEY = "AIzaSyAFTERBd0vyHCKWckgeXbubZ6tm9sjr-i8"

# 소문자
gemini_api_key = "AIzaSyAFTERBd0vyHCKWckgeXbubZ6tm9sjr-i8"

# 다른 형식
GEMINI_API_KEY: "AIzaSyAFTERBd0vyHCKWckgeXbubZ6tm9sjr-i8"
```

---

## API 키 확인 방법

로컬 `.env` 파일에서 확인:
```powershell
type .env
```

또는 파일을 열어서 `GEMINI_API_KEY=` 뒤의 값을 복사하세요.

---

## 설정 후 확인

1. **Secrets 저장 후**
   - 앱이 자동으로 재시작됩니다
   - "App restarted" 메시지 확인

2. **앱 접속 테스트**
   ```powershell
   start https://your-app-name.streamlit.app
   ```

3. **정상 작동 확인**
   - 로그인 페이지가 보이면 성공!
   - 회원가입 및 로그인 테스트

---

## 문제 해결

### Secrets 저장 후에도 오류가 나는 경우

1. **형식 확인**
   - `[secrets]` 포함했는지 확인
   - 따옴표로 감쌌는지 확인
   - 대문자 `GEMINI_API_KEY` 확인

2. **앱 재시작**
   - Settings → "Reboot app" 클릭
   - 또는 코드를 다시 push하면 자동 재배포

3. **로그 확인**
   - Settings → "Logs" 탭 확인
   - 오류 메시지 확인

### API 키가 보이지 않는 경우

- Secrets 탭에서 입력 필드가 비어있는지 확인
- 저장 버튼을 눌렀는지 확인
- 페이지를 새로고침하고 다시 확인

---

## 완료 체크리스트 ✅

- [ ] Streamlit Cloud 대시보드 접속
- [ ] 앱 설정으로 이동
- [ ] Secrets 탭 선택
- [ ] 올바른 형식으로 입력
- [ ] 저장 완료
- [ ] 앱 재시작 확인
- [ ] 앱 접속 테스트 완료

---

## 빠른 참조

**Secrets 입력 형식:**
```toml
[secrets]
GEMINI_API_KEY = "여기에_API_키_입력"
```

**앱 URL 열기:**
```powershell
start https://your-app-name.streamlit.app
```

**대시보드 열기:**
```powershell
start https://share.streamlit.io
```
