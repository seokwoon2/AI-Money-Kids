# 🔐 Streamlit Cloud Secrets 설정 완벽 가이드

## 📋 목차
1. Streamlit Cloud 접속
2. 앱 찾기
3. Settings(설정) 열기
4. Secrets 탭 찾기
5. API 키 입력
6. 저장 및 확인

---

## 1단계: Streamlit Cloud 접속

### 방법 1: 브라우저에서 직접 접속
1. 브라우저를 엽니다 (Chrome, Edge 등)
2. 주소창에 다음을 입력:
   ```
   https://share.streamlit.io
   ```
3. Enter 키를 누릅니다

### 방법 2: 터미널에서 열기
터미널에 입력:
```powershell
start https://share.streamlit.io
```

---

## 2단계: 로그인

1. **GitHub로 로그인** 버튼 클릭
   - 또는 이미 로그인되어 있으면 자동으로 대시보드로 이동

---

## 3단계: 배포된 앱 찾기

### 화면 구성:
- 왼쪽: 앱 목록
- 오른쪽: 앱 상세 정보

### 앱 찾는 방법:
1. **앱 목록에서 찾기**
   - 왼쪽 사이드바에 배포한 앱들이 나열됩니다
   - 앱 이름을 클릭합니다
   - 예: "ai-money-kids" 또는 "AI-Money-Kids"

2. **앱이 안 보이면:**
   - 오른쪽 상단의 "Apps" 메뉴 클릭
   - 또는 "My apps" 클릭

---

## 4단계: 앱 설정(Settings) 열기

앱을 클릭한 후:

### 방법 1: 설정 아이콘 사용
1. 앱 페이지 오른쪽 **상단**을 봅니다
2. **⚙️ (톱니바퀴) 아이콘**을 찾습니다
3. 클릭합니다

### 방법 2: 메뉴에서 찾기
1. 앱 페이지에서 **"Manage app"** 또는 **"앱 관리"** 버튼 찾기
2. 클릭
3. **"Settings"** 또는 **"설정"** 메뉴 클릭

### 방법 3: 직접 URL 사용
앱 URL이 `https://your-app-name.streamlit.app`라면:
```
https://share.streamlit.io/app/your-app-name/settings
```

---

## 5단계: Secrets 탭 찾기

Settings 페이지에 들어가면:

### 왼쪽 메뉴 확인:
- **"General"** (일반)
- **"Secrets"** ← 이걸 클릭!
- **"Advanced"** (고급)
- **"Logs"** (로그)

**"Secrets"** 탭을 클릭합니다.

---

## 6단계: API 키 입력

### Secrets 페이지 구성:
- 큰 텍스트 입력 상자가 있습니다
- 여기에 TOML 형식으로 입력합니다

### 입력할 내용:

**.env 파일에서 API 키 확인:**
`.env` 파일을 열어서 `GOOGLE_API_KEY=` 뒤의 값을 복사하세요.

예시:
```
GOOGLE_API_KEY=AIzaSyAFTERBd0vyHCKWckgeXbubZ6tm9sjr-i8
```

### Secrets 입력 상자에 정확히 입력:

```toml
[secrets]
GOOGLE_API_KEY = "AIzaSyAFTERBd0vyHCKWckgeXbubZ6tm9sjr-i8"
```

**⚠️ 중요 사항:**
1. `[secrets]`는 반드시 첫 줄에 있어야 합니다
2. `GOOGLE_API_KEY`는 대문자로 정확히 입력
3. 등호(`=`) 양쪽에 공백이 있어야 합니다
4. API 키는 **따옴표(`"`)로 감싸야** 합니다
5. 마지막에 세미콜론(`;`)이나 쉼표(`,`) 없습니다

### ✅ 올바른 예시:
```toml
[secrets]
GOOGLE_API_KEY = "AIzaSyAFTERBd0vyHCKWckgeXbubZ6tm9sjr-i8"
```

### ❌ 잘못된 예시들:

```toml
# 따옴표 없음
GOOGLE_API_KEY = AIzaSyAFTERBd0vyHCKWckgeXbubZ6tm9sjr-i8

# [secrets] 없음
GOOGLE_API_KEY = "AIzaSyAFTERBd0vyHCKWckgeXbubZ6tm9sjr-i8"

# 소문자
google_api_key = "AIzaSyAFTERBd0vyHCKWckgeXbubZ6tm9sjr-i8"

# 등호 양쪽 공백 없음
GOOGLE_API_KEY="AIzaSyAFTERBd0vyHCKWckgeXbubZ6tm9sjr-i8"

# 세미콜론 있음
GOOGLE_API_KEY = "AIzaSyAFTERBd0vyHCKWckgeXbubZ6tm9sjr-i8";
```

---

## 7단계: 저장

1. 입력 상자 아래에 **"Save"** 또는 **"저장"** 버튼이 있습니다
2. 클릭합니다
3. "Saved!" 또는 "저장되었습니다!" 메시지가 나타납니다
4. 앱이 자동으로 재시작됩니다 (몇 초 소요)

---

## 8단계: 확인

### 앱이 재시작되었는지 확인:
1. 페이지 상단에 **"App restarted"** 또는 **"앱이 재시작되었습니다"** 메시지 확인
2. 또는 앱 URL로 직접 접속:
   ```
   https://your-app-name.streamlit.app
   ```

### 테스트:
1. 앱에 로그인
2. "부모 상담실" 또는 "아이 채팅" 페이지로 이동
3. "저축은 왜 중요할까?" 질문 입력
4. AI가 답변하는지 확인

---

## 🔧 문제 해결

### Secrets 저장 후에도 오류가 나는 경우:

#### 1. 형식 확인
- `[secrets]` 포함했는지 확인
- 따옴표로 감쌌는지 확인
- 대문자 `GOOGLE_API_KEY` 확인
- 등호 양쪽 공백 확인

#### 2. 앱 재시작
- Settings → "Reboot app" 또는 "앱 재시작" 클릭
- 또는 코드를 다시 push하면 자동 재배포

#### 3. 로그 확인
- Settings → "Logs" 탭 클릭
- 오류 메시지 확인
- "API key" 관련 오류가 있는지 확인

#### 4. API 키 확인
- `.env` 파일에서 API 키가 올바른지 확인
- API 키가 `AIza...`로 시작하는지 확인

---

## 📝 체크리스트

배포 전 확인:
- [ ] Streamlit Cloud 대시보드 접속 완료
- [ ] 앱 찾기 완료
- [ ] Settings 열기 완료
- [ ] Secrets 탭 찾기 완료
- [ ] API 키 입력 완료 (형식 확인)
- [ ] 저장 완료
- [ ] 앱 재시작 확인
- [ ] 테스트 완료

---

## 💡 빠른 참조

**Secrets 입력 형식:**
```toml
[secrets]
GOOGLE_API_KEY = "여기에_API_키_입력"
```

**Streamlit Cloud 대시보드:**
```
https://share.streamlit.io
```

**앱 URL 형식:**
```
https://your-app-name.streamlit.app
```

---

## 🆘 도움이 필요하면

1. **로그 확인**: Settings → Logs 탭
2. **앱 재시작**: Settings → Reboot app
3. **코드 확인**: GitHub 저장소에서 최신 코드 확인
