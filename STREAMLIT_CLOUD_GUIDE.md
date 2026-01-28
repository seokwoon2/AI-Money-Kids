# 🚀 Streamlit Cloud 배포 상세 가이드

## Streamlit Cloud 접속 및 앱 생성

### 1단계: Streamlit Cloud 접속

1. **브라우저에서 접속**
   ```
   https://streamlit.io/cloud
   ```
   또는
   ```
   https://share.streamlit.io
   ```

2. **로그인**
   - "Sign up" 또는 "Log in" 클릭
   - "Continue with GitHub" 클릭 (GitHub 계정으로 로그인)
   - GitHub 인증 완료

### 2단계: 대시보드에서 앱 생성

**방법 1: 메인 화면에서**

1. **로그인 후 메인 화면 확인**
   - 화면 상단에 "New app" 또는 "Create app" 버튼이 있을 수 있습니다
   - 또는 왼쪽 사이드바에 "Apps" 메뉴가 있습니다

2. **"New app" 버튼 찾기**
   - 화면 오른쪽 상단에 "+" 아이콘 또는 "New app" 버튼
   - 또는 화면 중앙에 "Deploy an app" 버튼
   - 또는 왼쪽 메뉴에서 "Apps" → "New app"

**방법 2: Apps 메뉴에서**

1. **왼쪽 사이드바 확인**
   - "Apps" 또는 "My apps" 메뉴 클릭
   - 화면 오른쪽 상단에 "New app" 버튼 클릭

**방법 3: 직접 URL 접속**

만약 버튼이 안 보이면:
```
https://share.streamlit.io/deploy
```

### 3단계: 앱 설정 상세 설명

"New app" 버튼을 클릭하면 다음 화면이 나타납니다:

#### 화면 구성:

```
┌─────────────────────────────────────────┐
│  Deploy an app                          │
├─────────────────────────────────────────┤
│                                         │
│  Repository: [드롭다운 선택 ▼]          │
│  └─ your-username/your-repo-name       │
│                                         │
│  Branch: [main ▼]                      │
│                                         │
│  Main file path: [app.py]               │
│                                         │
│  Python version: [3.11 ▼]              │
│                                         │
│  [Advanced settings ▼]                 │
│                                         │
│  [Deploy!] 버튼                        │
└─────────────────────────────────────────┘
```

#### 각 항목 설명:

**1. Repository (저장소)**
- **설명**: GitHub에 업로드한 저장소를 선택합니다
- **작업**: 드롭다운 메뉴 클릭 → 저장소 선택
- **예시**: `your-username/ai-money-kids`
- **주의**: 저장소가 안 보이면 GitHub에서 저장소를 먼저 생성해야 합니다

**2. Branch (브랜치)**
- **설명**: 사용할 Git 브랜치를 선택합니다
- **기본값**: `main` (대부분의 경우 이대로 두면 됩니다)
- **변경 필요 없음**: 그대로 `main` 사용

**3. Main file path (메인 파일 경로)**
- **설명**: Streamlit 앱의 시작 파일을 지정합니다
- **입력**: `app.py`
- **주의**: 
  - 프로젝트 루트에 `app.py`가 있어야 합니다
  - 다른 이름이면 그 이름으로 변경 (예: `main.py`)

**4. Python version (Python 버전)**
- **설명**: 사용할 Python 버전을 선택합니다
- **권장**: `3.11` 또는 `3.10` (3.8 이상이면 됩니다)
- **기본값**: 최신 버전이 자동 선택됩니다

**5. Advanced settings (고급 설정)**
- **설명**: 추가 설정이 필요할 때 사용
- **일반적으로**: 클릭하지 않아도 됩니다
- **필요시**: 
  - Secrets (환경 변수) 설정
  - 추가 패키지 설치 등

### 4단계: Deploy 버튼 클릭

1. **모든 설정 확인**
   - Repository: 선택됨 ✓
   - Branch: `main` ✓
   - Main file path: `app.py` ✓
   - Python version: 3.8 이상 ✓

2. **"Deploy!" 버튼 클릭**
   - 또는 "Deploy app" 버튼

3. **배포 진행 확인**
   - "Building..." 메시지 표시
   - 몇 분 정도 소요됩니다

### 5단계: 배포 완료 및 URL 확인

배포가 완료되면:

1. **앱 URL 확인**
   ```
   https://your-app-name.streamlit.app
   ```
   또는
   ```
   https://your-username-your-repo-name.streamlit.app
   ```

2. **앱 접속 테스트**
   - 브라우저에서 URL 접속
   - 앱이 정상적으로 보이면 성공!

### 6단계: 환경 변수 설정 (중요!)

앱이 실행되지만 API 키가 필요합니다:

1. **앱 설정으로 이동**
   - 앱 목록에서 앱 클릭
   - 또는 앱 페이지에서 "Settings" 또는 "⚙️" 아이콘 클릭

2. **Secrets 탭 선택**
   - 왼쪽 메뉴에서 "Secrets" 클릭

3. **환경 변수 입력**
   ```toml
   [secrets]
   GEMINI_API_KEY = "여기에_실제_API_키_입력"
   ```

4. **저장**
   - "Save" 버튼 클릭
   - 앱이 자동으로 재시작됩니다

---

## 문제 해결

### "New app" 버튼이 안 보일 때

1. **GitHub 연동 확인**
   - Streamlit Cloud에 GitHub로 로그인했는지 확인
   - GitHub 계정이 연결되어 있는지 확인

2. **다른 위치 확인**
   - 화면 오른쪽 상단의 "+" 아이콘
   - 왼쪽 사이드바의 "Apps" 메뉴
   - 화면 중앙의 "Deploy an app" 버튼

3. **직접 URL 접속**
   ```
   https://share.streamlit.io/deploy
   ```

### Repository가 안 보일 때

1. **GitHub 저장소 확인**
   - GitHub에 저장소가 생성되어 있는지 확인
   - 저장소가 Public인지 확인 (Private도 가능하지만 설정 필요)

2. **GitHub 연동 확인**
   - Streamlit Cloud에서 GitHub 권한이 허용되어 있는지 확인

3. **저장소 이름 확인**
   - 정확한 저장소 이름을 입력했는지 확인

### 배포 실패 시

1. **로그 확인**
   - 앱 페이지에서 "Logs" 탭 확인
   - 오류 메시지 확인

2. **requirements.txt 확인**
   - 프로젝트에 `requirements.txt` 파일이 있는지 확인
   - 모든 패키지가 올바르게 나열되어 있는지 확인

3. **파일 경로 확인**
   - `app.py` 파일이 프로젝트 루트에 있는지 확인

---

## 체크리스트 ✅

배포 전 확인사항:

- [ ] GitHub 계정 생성 및 로그인 완료
- [ ] GitHub에 저장소 생성 완료
- [ ] 코드 업로드 완료 (`git push`)
- [ ] Streamlit Cloud 로그인 완료
- [ ] "New app" 버튼 클릭
- [ ] Repository 선택 완료
- [ ] Main file path: `app.py` 입력
- [ ] "Deploy!" 버튼 클릭
- [ ] 배포 완료 대기
- [ ] 환경 변수 설정 완료

---

## 완료 후

배포가 완료되면:
- ✅ 영구적인 URL 받기
- ✅ 모바일에서 접속 가능
- ✅ 인터넷 어디서나 접속 가능
- ✅ 코드 업데이트 시 자동 재배포
