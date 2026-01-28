# 🚀 Streamlit Cloud 배포 완벽 가이드 (처음부터 끝까지)

## 전체 과정 개요

1. GitHub 저장소 생성
2. 코드를 GitHub에 업로드
3. Streamlit Cloud에서 배포
4. 환경 변수 설정
5. 완료!

---

## 1단계: GitHub 저장소 생성 📦

### 1-1. GitHub 접속

터미널에서:
```powershell
start https://github.com
```

또는 브라우저에서 직접: https://github.com

### 1-2. 로그인 또는 가입

- **이미 계정이 있으면**: "Sign in" 클릭
- **계정이 없으면**: "Sign up" 클릭하여 가입

### 1-3. 새 저장소 생성

1. **오른쪽 상단의 "+" 아이콘 클릭**
   - 또는 https://github.com/new 직접 접속

2. **저장소 정보 입력**
   ```
   Repository name: AI-Money-Kids
   Description: AI 금융교육 서비스 (선택사항)
   Public / Private: Public 선택 (무료)
   ```

3. **"Create repository" 클릭**
   - ⚠️ README, .gitignore, license는 체크하지 마세요!
   - 빈 저장소로 생성해야 합니다

4. **저장소 URL 확인**
   - 예: `https://github.com/seokwoon2/AI-Money-Kids`
   - 이 URL을 기억해두세요!

---

## 2단계: 코드를 GitHub에 업로드 📤

### 2-1. Git 설치 확인

터미널에서:
```powershell
git --version
```

- 버전이 나오면 설치됨
- 오류가 나면 Git 설치 필요: https://git-scm.com/download/win

### 2-2. 프로젝트 폴더로 이동

터미널에서:
```powershell
cd "C:\Users\JBB\Documents\JB AI Money Kids"
```

### 2-3. Git 초기화

```powershell
git init
```

성공 메시지:
```
Initialized empty Git repository in C:/Users/JBB/Documents/JB AI Money Kids/.git/
```

### 2-4. 파일 추가

```powershell
git add .
```

이 명령어는 모든 파일을 추가합니다.

### 2-5. 첫 커밋

```powershell
git commit -m "Initial commit: AI 금융교육 서비스"
```

**오류가 나면 (이름/이메일 설정 필요):**
```powershell
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

그 다음 다시:
```powershell
git commit -m "Initial commit: AI 금융교육 서비스"
```

### 2-6. GitHub 저장소 연결

**YOUR_USERNAME과 YOUR_REPO_NAME을 실제 값으로 변경하세요!**

```powershell
git remote add origin https://github.com/seokwoon2/AI-Money-Kids.git
```

**예시 (실제 사용자명과 저장소명으로 변경):**
```powershell
git remote add origin https://github.com/seokwoon2/AI-Money-Kids.git
```

### 2-7. 브랜치 이름 설정

```powershell
git branch -M main
```

### 2-8. 코드 업로드

```powershell
git push -u origin main
```

**GitHub 로그인 창이 뜨면:**
- 사용자명과 비밀번호 입력
- 또는 Personal Access Token 사용 (비밀번호 대신)

**Personal Access Token이 필요하면:**
1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. "Generate new token" 클릭
3. 권한 선택: `repo` 체크
4. 생성된 토큰 복사
5. 비밀번호 대신 이 토큰 사용

### 2-9. 업로드 확인

GitHub 웹사이트에서 확인:
```powershell
start https://github.com/seokwoon2/AI-Money-Kids
```

- 파일들이 보이면 성공!

---

## 3단계: Streamlit Cloud에서 배포 ☁️

### 3-1. Streamlit Cloud 접속

터미널에서:
```powershell
start https://share.streamlit.io
```

또는 브라우저에서: https://share.streamlit.io

### 3-2. 로그인

1. **"Sign up" 또는 "Log in" 클릭**
2. **"Continue with GitHub" 클릭**
3. **GitHub 인증 완료**

### 3-3. 앱 생성

**방법 1: 메인 화면에서**
- "New app" 버튼 클릭
- 또는 오른쪽 상단의 "+" 아이콘 클릭

**방법 2: 직접 URL 접속**
```powershell
start https://share.streamlit.io/deploy
```

### 3-4. 앱 설정 입력

**Repository:**
- 드롭다운에서 선택
- 또는 직접 입력: `seokwoon2/AI-Money-Kids`
- ⚠️ 전체 URL이 아니라 `사용자명/저장소이름` 형식만!

**Branch:**
- `main` 선택 (기본값)

**Main file path:**
- `app.py` 입력

**Python version:**
- `3.11` 또는 `3.10` 선택 (3.8 이상)

### 3-5. 배포 시작

**"Deploy!" 버튼 클릭**

### 3-6. 배포 진행 확인

- "Building..." 메시지 표시
- 몇 분 정도 소요됩니다
- 진행 상황이 화면에 표시됩니다

### 3-7. 배포 완료

- "Your app is live!" 메시지 확인
- 앱 URL 확인:
  ```
  https://ai-money-kids.streamlit.app
  ```
  (실제 URL은 다를 수 있습니다)

---

## 4단계: 환경 변수 설정 🔐

### 4-1. 앱 설정으로 이동

1. **앱 목록에서 앱 클릭**
2. **또는 앱 페이지에서 "⚙️" 아이콘 클릭**
3. **"Settings" 메뉴 클릭**

### 4-2. Secrets 탭 선택

- 왼쪽 메뉴에서 **"Secrets"** 클릭

### 4-3. 환경 변수 입력

다음 내용을 입력:

```toml
[secrets]
GEMINI_API_KEY = "여기에_실제_API_키_입력"
```

**예시:**
```toml
[secrets]
GEMINI_API_KEY = "AIzaSyAbc123def456ghi789jkl012mno345pqr678"
```

### 4-4. 저장

- **"Save" 버튼 클릭**
- 앱이 자동으로 재시작됩니다

### 4-5. API 키 확인

`.env` 파일에서 API 키 확인:
```powershell
type .env
```

또는 파일을 열어서 확인하세요.

---

## 5단계: 완료 확인 ✅

### 5-1. 앱 접속

앱 URL로 접속:
```powershell
start https://your-app-name.streamlit.app
```

### 5-2. 테스트

- 로그인 페이지가 보이는지 확인
- 회원가입 테스트
- 기능이 정상 작동하는지 확인

---

## 문제 해결 🔧

### Git 업로드 오류

**오류: "remote origin already exists"**
```powershell
git remote remove origin
git remote add origin https://github.com/seokwoon2/AI-Money-Kids.git
```

**오류: "failed to push"**
- GitHub 로그인 확인
- Personal Access Token 사용

### Streamlit Cloud 배포 오류

**오류: "Repository not found"**
- Repository 이름 확인: `사용자명/저장소이름` 형식
- GitHub에 코드가 업로드되었는지 확인

**오류: "Module not found"**
- `requirements.txt` 파일 확인
- 모든 패키지가 포함되어 있는지 확인

**오류: "API key not found"**
- Secrets에 환경 변수가 제대로 입력되었는지 확인
- 저장 후 앱이 재시작되었는지 확인

---

## 체크리스트 ✅

배포 전:
- [ ] GitHub 계정 생성/로그인 완료
- [ ] GitHub 저장소 생성 완료
- [ ] Git 설치 확인 완료
- [ ] `requirements.txt` 파일 확인 완료
- [ ] `.env` 파일이 `.gitignore`에 포함되어 있는지 확인

배포 중:
- [ ] `git init` 완료
- [ ] `git add .` 완료
- [ ] `git commit` 완료
- [ ] `git remote add origin` 완료
- [ ] `git push` 완료
- [ ] GitHub에서 파일 확인 완료
- [ ] Streamlit Cloud 로그인 완료
- [ ] 앱 생성 완료
- [ ] 배포 완료 대기

배포 후:
- [ ] 앱 URL 확인 완료
- [ ] Secrets에 API 키 설정 완료
- [ ] 앱 접속 테스트 완료
- [ ] 기능 테스트 완료

---

## 완료 후

배포가 완료되면:
- ✅ 영구적인 URL 받기
- ✅ 모바일에서 접속 가능
- ✅ 인터넷 어디서나 접속 가능
- ✅ 코드 업데이트 시 자동 재배포

**앱 URL 예시:**
```
https://ai-money-kids.streamlit.app
```

이 URL을 터미널에서 열려면:
```powershell
start https://ai-money-kids.streamlit.app
```

---

## 다음 업데이트 방법

코드를 수정한 후:

```powershell
git add .
git commit -m "업데이트 내용 설명"
git push
```

Streamlit Cloud가 자동으로 재배포합니다!
