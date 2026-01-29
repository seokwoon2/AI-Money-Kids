# ✅ Streamlit Cloud Secrets 올바른 입력 형식

## ❌ 잘못된 형식 (사용자가 제시한 형식)

```toml
[GEMINI]
API_KEY="복사한키"

[KAKAO]
REST_API_KEY="복사한키"
REDIRECT_URI="https://..."
```

**이 형식은 작동하지 않습니다!** Streamlit Cloud Secrets는 섹션을 여러 개 사용할 수 없습니다.

---

## ✅ 올바른 형식

Streamlit Cloud Secrets에는 **반드시 `[secrets]` 섹션 하나만** 사용하고, 모든 키를 평면적으로 나열해야 합니다:

```toml
[secrets]
GOOGLE_API_KEY = "AIzaSy여기에_복사한_Gemini_API_키"
KAKAO_REST_API_KEY = "여기에_복사한_카카오_REST_API_키"
KAKAO_REDIRECT_URI = "https://ai-money-kidsmainapppyurlai-money-kids-3fcwykyatx72lvd4znnjapp.streamlit.app/"
```

---

## 📝 상세 설명

### 1. 필수 요소

- **`[secrets]`** - 반드시 포함해야 합니다
- **모든 키는 `[secrets]` 섹션 안에** 나열합니다
- **섹션은 하나만** 사용합니다

### 2. 키 이름

코드에서 사용하는 키 이름:
- `GOOGLE_API_KEY` 또는 `GEMINI_API_KEY` (Gemini API용)
- `KAKAO_REST_API_KEY` (카카오 로그인용)
- `KAKAO_REDIRECT_URI` (카카오 리다이렉트 URI)

### 3. 값 형식

- **따옴표로 감싸야 합니다** (`"값"`)
- **등호 앞뒤 공백** 있어도 됩니다 (`=` 또는 ` = `)

---

## 🔍 실제 예시

### 예시 1: Gemini API만 사용하는 경우

```toml
[secrets]
GOOGLE_API_KEY = "AIzaSyAbc123def456ghi789jkl012mno345pqr678"
```

### 예시 2: Gemini API + 카카오 로그인 사용하는 경우

```toml
[secrets]
GOOGLE_API_KEY = "AIzaSyAbc123def456ghi789jkl012mno345pqr678"
KAKAO_REST_API_KEY = "abc123def456ghi789jkl012mno345pqr678"
KAKAO_REDIRECT_URI = "https://ai-money-kidsmainapppyurlai-money-kids-3fcwykyatx72lvd4znnjapp.streamlit.app/"
```

### 예시 3: GEMINI_API_KEY 사용 (호환성)

```toml
[secrets]
GEMINI_API_KEY = "AIzaSyAbc123def456ghi789jkl012mno345pqr678"
KAKAO_REST_API_KEY = "abc123def456ghi789jkl012mno345pqr678"
KAKAO_REDIRECT_URI = "https://ai-money-kidsmainapppyurlai-money-kids-3fcwykyatx72lvd4znnjapp.streamlit.app/"
```

---

## ⚠️ 주의사항

### 1. 섹션은 하나만!

```toml
# ❌ 잘못됨 - 섹션이 여러 개
[GEMINI]
API_KEY = "..."

[KAKAO]
REST_API_KEY = "..."

# ✅ 올바름 - 섹션 하나에 모든 키
[secrets]
GOOGLE_API_KEY = "..."
KAKAO_REST_API_KEY = "..."
```

### 2. 키 이름은 정확히!

```toml
# ❌ 잘못됨
[secrets]
gemini_api_key = "..."  # 소문자
GEMINI.API_KEY = "..."  # 점 사용
GEMINI_API_KEY = "..."  # GEMINI 대신 GOOGLE 사용 권장

# ✅ 올바름
[secrets]
GOOGLE_API_KEY = "..."  # 또는 GEMINI_API_KEY
KAKAO_REST_API_KEY = "..."
```

### 3. 따옴표 필수!

```toml
# ❌ 잘못됨
[secrets]
GOOGLE_API_KEY = AIzaSy...  # 따옴표 없음

# ✅ 올바름
[secrets]
GOOGLE_API_KEY = "AIzaSy..."
```

---

## 📋 체크리스트

입력 전 확인:
- [ ] `[secrets]` 섹션이 맨 위에 있나요?
- [ ] 섹션이 하나만 있나요?
- [ ] 모든 키가 `[secrets]` 안에 있나요?
- [ ] 키 이름이 정확한가요? (대문자, 언더스코어)
- [ ] 값이 따옴표로 감싸져 있나요?
- [ ] 카카오 REDIRECT_URI에 실제 앱 URL이 들어갔나요?

---

## 🆘 문제 해결

### Secrets 저장 후에도 오류가 나는 경우

1. **형식 확인**
   - `[secrets]` 포함했는지 확인
   - 섹션이 하나만 있는지 확인
   - 모든 키가 `[secrets]` 안에 있는지 확인

2. **키 이름 확인**
   - `GOOGLE_API_KEY` 또는 `GEMINI_API_KEY`
   - `KAKAO_REST_API_KEY`
   - `KAKAO_REDIRECT_URI`
   - 대소문자 정확히 입력

3. **앱 재시작**
   - Settings → "Reboot app" 클릭
   - 또는 코드를 다시 push

---

## 💡 팁

### 카카오 REDIRECT_URI 확인

카카오 개발자 콘솔에 등록한 Redirect URI와 정확히 일치해야 합니다:

1. 카카오 개발자 콘솔 접속: https://developers.kakao.com/
2. 내 애플리케이션 선택
3. 플랫폼 설정 → Web 플랫폼 등록
4. 사이트 도메인: `https://ai-money-kidsmainapppyurlai-money-kids-3fcwykyatx72lvd4znnjapp.streamlit.app`
5. Redirect URI: `https://ai-money-kidsmainapppyurlai-money-kids-3fcwykyatx72lvd4znnjapp.streamlit.app/`

**중요:** 마지막에 `/`가 있어야 합니다!
