# 🔑 Google Gemini API 키 발급 가이드

## Google Gemini API 키 발급 방법

### 1단계: Google AI Studio 접속

1. 브라우저에서 다음 주소로 이동:
   ```
   https://aistudio.google.com/apikey
   ```
   
   또는 Google AI Studio 메인 페이지:
   ```
   https://aistudio.google.com/
   ```

### 2단계: Google 계정으로 로그인

- Google 계정이 필요합니다
- Gmail 계정으로 로그인하면 됩니다

### 3단계: API 키 생성

1. **"Get API key"** 또는 **"API 키 만들기"** 버튼 클릭
2. **"Create API key in new project"** 선택
   - 또는 기존 프로젝트 선택 가능
3. **"Create API key"** 클릭

### 4단계: API 키 복사

- 생성된 API 키가 화면에 표시됩니다
- 형식: `AIzaSy...` (약 39자 길이)
- **즉시 복사하세요!** (나중에 다시 볼 수 없습니다)

### 5단계: Streamlit Cloud Secrets에 입력

1. Streamlit Cloud 대시보드 접속: https://share.streamlit.io
2. 앱 설정 → **Secrets** 탭
3. 다음 형식으로 입력:

```toml
[secrets]
GOOGLE_API_KEY = "AIzaSy여기에_복사한_API_키_붙여넣기"
```

또는

```toml
[secrets]
GEMINI_API_KEY = "AIzaSy여기에_복사한_API_키_붙여넣기"
```

4. **"Save"** 버튼 클릭

---

## 📝 API 키 예시 형식

API 키는 다음과 같은 형식입니다:

```
AIzaSyAbc123def456ghi789jkl012mno345pqr678stu901vwx234yz
```

- `AIzaSy`로 시작합니다
- 약 39자 정도의 길이입니다
- 대문자와 소문자, 숫자가 섞여 있습니다

---

## ⚠️ 주의사항

### API 키 보안

1. **절대 공개하지 마세요!**
   - GitHub에 올리지 마세요
   - 다른 사람과 공유하지 마세요
   - `.env` 파일은 `.gitignore`에 포함되어 있어야 합니다

2. **API 키가 노출되면:**
   - Google AI Studio에서 즉시 삭제하세요
   - 새로운 API 키를 발급받으세요

3. **사용량 제한:**
   - 무료 티어는 월 60회 요청 제한이 있을 수 있습니다
   - 과도한 사용 시 요금이 발생할 수 있습니다

---

## 🔍 API 키 확인 방법

### Google AI Studio에서 확인

1. https://aistudio.google.com/apikey 접속
2. 생성한 API 키 목록 확인
3. 필요시 삭제 또는 새로 생성 가능

### 로컬 .env 파일에서 확인

프로젝트 폴더에서:
```powershell
type .env
```

또는 파일을 열어서 확인:
```
GOOGLE_API_KEY=AIzaSy...
```

---

## ✅ 완료 체크리스트

- [ ] Google AI Studio 접속 완료
- [ ] Google 계정으로 로그인 완료
- [ ] API 키 생성 완료
- [ ] API 키 복사 완료
- [ ] Streamlit Cloud Secrets에 입력 완료
- [ ] 저장 완료
- [ ] 앱에서 AI 채팅 기능 테스트 완료

---

## 🆘 문제 해결

### API 키를 찾을 수 없어요

- Google AI Studio에서 새로 생성하세요
- https://aistudio.google.com/apikey

### "API 키가 유효하지 않습니다" 오류

1. API 키를 다시 복사했는지 확인
2. 따옴표로 감쌌는지 확인
3. `[secrets]` 섹션을 포함했는지 확인
4. Streamlit Cloud에서 앱 재시작

### API 사용량 초과 오류

- 무료 티어 제한에 도달했을 수 있습니다
- 다음 달까지 기다리거나 유료 플랜 고려

---

## 📚 추가 정보

- **Google AI Studio**: https://aistudio.google.com/
- **Gemini API 문서**: https://ai.google.dev/docs
- **가격 정보**: https://ai.google.dev/pricing

---

## 💡 팁

1. **로컬 테스트:**
   - `.env` 파일에 API 키를 저장하면 로컬에서 테스트 가능
   - `.env` 파일은 절대 Git에 커밋하지 마세요!

2. **여러 환경:**
   - 로컬: `.env` 파일 사용
   - Streamlit Cloud: Secrets 사용

3. **API 키 백업:**
   - 안전한 곳에 별도로 저장해두세요
   - 하지만 공개된 곳에는 절대 저장하지 마세요!
