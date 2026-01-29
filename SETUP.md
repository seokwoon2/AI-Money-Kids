# 설정 가이드 (Setup Guide)

이 문서는 AI Money Friends 앱을 설정하는 방법을 단계별로 안내합니다.

## 목차

1. [카카오 개발자 등록](#카카오-개발자-등록)
2. [네이버 개발자 등록](#네이버-개발자-등록)
3. [구글 개발자 등록](#구글-개발자-등록)
4. [Streamlit Cloud Secrets 설정](#streamlit-cloud-secrets-설정)
5. [자주 하는 실수 및 해결 방법](#자주-하는-실수-및-해결-방법)

---

## 카카오 개발자 등록

### 1단계: 카카오 개발자 계정 생성

1. [카카오 개발자 사이트](https://developers.kakao.com/)에 접속
2. "내 애플리케이션" 메뉴 클릭
3. "애플리케이션 추가하기" 클릭
4. 앱 이름 입력 (예: "AI Money Friends")
5. "저장" 클릭

### 2단계: REST API 키 확인

1. 생성된 앱 선택
2. "앱 키" 탭에서 **REST API 키** 복사
3. 이 키를 `.env` 파일의 `KAKAO_CLIENT_ID`에 입력

### 3단계: 플랫폼 설정

1. "플랫폼" 탭 클릭
2. "Web 플랫폼 등록" 클릭
3. 사이트 도메인 입력:
   - 로컬: `http://localhost:8501`
   - 배포: `https://your-app.streamlit.app`

### 4단계: Redirect URI 설정

1. "제품 설정" → "카카오 로그인" 활성화
2. "Redirect URI" 설정:
   - 로컬: `http://localhost:8501`
   - 배포: `https://your-app.streamlit.app`
3. "저장" 클릭

### 5단계: 동의 항목 설정 (선택)

1. "제품 설정" → "카카오 로그인" → "동의항목"
2. 필요한 정보 동의 항목 활성화 (닉네임, 프로필 사진 등)

---

## 네이버 개발자 등록

### 1단계: 네이버 개발자 계정 생성

1. [네이버 개발자 센터](https://developers.naver.com/)에 접속
2. "Application" → "애플리케이션 등록" 클릭
3. 애플리케이션 정보 입력:
   - 애플리케이션 이름: "AI Money Friends"
   - 사용 API: "네이버 로그인"
   - 로그인 오픈 API 서비스 환경: "PC 웹"
   - 서비스 URL: `http://localhost:8501` (로컬) 또는 배포 URL
   - Callback URL: `http://localhost:8501` (로컬) 또는 배포 URL

### 2단계: Client ID와 Client Secret 확인

1. 등록 완료 후 애플리케이션 선택
2. "Client ID"와 "Client Secret" 복사
3. `.env` 파일에 입력:
   ```
   NAVER_CLIENT_ID=your_client_id
   NAVER_CLIENT_SECRET=your_client_secret
   ```

---

## 구글 개발자 등록

### 1단계: Google Cloud Console 접속

1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택

### 2단계: OAuth 동의 화면 설정

1. "API 및 서비스" → "OAuth 동의 화면"
2. 사용자 유형 선택: "외부" (개인 개발자)
3. 앱 정보 입력:
   - 앱 이름: "AI Money Friends"
   - 사용자 지원 이메일: 본인 이메일
   - 개발자 연락처 정보: 본인 이메일

### 3단계: OAuth 2.0 클라이언트 ID 생성

1. "API 및 서비스" → "사용자 인증 정보"
2. "사용자 인증 정보 만들기" → "OAuth 클라이언트 ID"
3. 애플리케이션 유형: "웹 애플리케이션"
4. 이름: "AI Money Friends Web Client"
5. 승인된 리디렉션 URI 추가:
   - 로컬: `http://localhost:8501`
   - 배포: `https://your-app.streamlit.app`
6. "만들기" 클릭
7. **Client ID**와 **Client Secret** 복사
8. `.env` 파일에 입력:
   ```
   GOOGLE_CLIENT_ID=your_client_id
   GOOGLE_CLIENT_SECRET=your_client_secret
   ```

### 4단계: OAuth 2.0 API 활성화

1. "API 및 서비스" → "라이브러리"
2. "Google+ API" 또는 "Identity Toolkit API" 검색 및 활성화

---

## Streamlit Cloud Secrets 설정

### 1단계: Streamlit Cloud 접속

1. [Streamlit Cloud](https://streamlit.io/cloud) 접속
2. GitHub 계정으로 로그인
3. 앱 선택 또는 새 앱 생성

### 2단계: Secrets 설정

1. 앱 대시보드에서 "Settings" → "Secrets" 클릭
2. 다음 형식으로 입력:

```toml
[oauth]
kakao_client_id = "your_kakao_rest_api_key"
kakao_redirect_uri = "https://your-app.streamlit.app"

naver_client_id = "your_naver_client_id"
naver_client_secret = "your_naver_client_secret"
naver_redirect_uri = "https://your-app.streamlit.app"

google_client_id = "your_google_client_id"
google_client_secret = "your_google_client_secret"
google_redirect_uri = "https://your-app.streamlit.app"
```

3. "Save" 클릭

### 3단계: 앱 재시작

1. "Manage app" → "⋮" (메뉴) → "Restart app"
2. 변경사항이 적용됩니다

---

## 자주 하는 실수 및 해결 방법

### ❌ 오류 1: "연결을 거부했습니다"

**원인**: OAuth 클라이언트 ID가 잘못되었거나 Redirect URI가 일치하지 않음

**해결 방법**:
1. `.env` 파일 또는 Streamlit Secrets에 올바른 키가 입력되었는지 확인
2. 각 개발자 콘솔에서 Redirect URI가 정확히 일치하는지 확인
3. 로컬: `http://localhost:8501`
4. 배포: `https://your-app.streamlit.app` (정확한 URL)

### ❌ 오류 2: "KOE101 앱 관리자 설정 오류"

**원인**: Streamlit Secrets에 접근하는 시점이 잘못됨

**해결 방법**:
1. `services/oauth_service.py`가 지연 초기화를 사용하는지 확인
2. 앱을 재시작
3. Secrets 형식이 올바른지 확인 (TOML 형식)

### ❌ 오류 3: "토큰 발급 실패"

**원인**: 
- 인가 코드가 만료됨
- Client Secret이 잘못됨
- Redirect URI 불일치

**해결 방법**:
1. 다시 로그인 시도
2. Client Secret이 올바른지 확인
3. Redirect URI가 개발자 콘솔과 일치하는지 확인

### ❌ 오류 4: 네이버 "state 검증 실패"

**원인**: CSRF 보호를 위한 state 값이 일치하지 않음

**해결 방법**:
1. 세션이 유지되는지 확인
2. 브라우저 쿠키 설정 확인
3. 다시 로그인 시도

### ❌ 오류 5: ".env 파일이 로드되지 않음"

**원인**: 
- `.env` 파일 위치가 잘못됨
- `python-dotenv`가 설치되지 않음

**해결 방법**:
1. `.env` 파일이 프로젝트 루트에 있는지 확인
2. `pip install python-dotenv` 실행
3. 앱 재시작

---

## 체크리스트

설정 완료 후 다음 항목을 확인하세요:

- [ ] 카카오 REST API 키 발급 완료
- [ ] 네이버 Client ID/Secret 발급 완료
- [ ] 구글 Client ID/Secret 발급 완료
- [ ] 모든 Redirect URI가 개발자 콘솔에 등록됨
- [ ] `.env` 파일에 모든 키가 입력됨 (로컬)
- [ ] Streamlit Cloud Secrets에 모든 키가 입력됨 (배포)
- [ ] 앱이 정상적으로 실행됨
- [ ] 소셜 로그인이 작동함

---

## 추가 도움말

문제가 계속되면:
1. 브라우저 개발자 도구(F12)에서 콘솔 오류 확인
2. Streamlit Cloud 로그 확인 ("Manage app" → "Logs")
3. GitHub Issues에 문제 보고
