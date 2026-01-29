import streamlit as st
from database.db_manager import DatabaseManager
from services.gemini_service import GeminiService
from utils.menu import render_sidebar_menu, hide_sidebar_navigation

st.set_page_config(
    page_title="📖 금융 스토리",
    page_icon="📖",
    layout="wide",
    menu_items=None
)

# Streamlit 기본 네비게이션 숨기기
hide_sidebar_navigation()
st.markdown("""
<style>
[data-testid="stSidebarNav"] {
    display: none !important;
}
nav[data-testid="stSidebarNav"] {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

# 로그인 확인
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.switch_page("app.py")

user_id = st.session_state.user_id
user_name = st.session_state.user_name

db = DatabaseManager()
gemini_service = GeminiService()

user = db.get_user_by_id(user_id)
user_type = user.get('user_type', 'child') if user else 'child'
user_age = user.get('age', 10) if user else 10

# 아이 전용 페이지 확인
if user_type != 'child':
    st.warning("이 페이지는 아이 전용입니다.")
    st.stop()

# 사이드바 메뉴 렌더링
render_sidebar_menu(user_id, user_name, user_type)

# 페이지 제목
st.title(f"📖 {user_name}님의 금융 스토리")
st.markdown("---")

# 스토리 주제 선택
st.subheader("📚 읽고 싶은 스토리 선택")

story_topics = [
    "💰 저축의 중요성",
    "🛒 현명한 소비하기",
    "⏰ 기다림의 가치",
    "🎯 목표 설정하기",
    "💡 돈의 의미",
    "🔍 가격 비교하기"
]

selected_topic = st.selectbox("주제를 선택하세요", story_topics)

# 스토리 생성
if st.button("📖 스토리 읽기", type="primary", use_container_width=True):
    with st.spinner("나만의 금융 스토리를 만들고 있어요..."):
        prompt = f"""다음 주제에 대해 {user_age}세 아이가 이해하기 쉽고 재미있는 스토리를 만들어주세요.

주제: {selected_topic}

요구사항:
1. 주인공은 {user_name}와 비슷한 나이의 아이
2. 일상적인 상황에서 벌어지는 이야기
3. 금융 개념을 자연스럽게 전달
4. 긍정적이고 교육적인 메시지
5. 300-500자 정도의 적당한 길이
6. 아이가 공감할 수 있는 캐릭터와 상황

한국어로 친근하고 재미있게 작성해주세요."""

        try:
            story = gemini_service.chat_with_context(prompt, user_type='child', user_age=user_age)
            
            st.markdown("---")
            st.markdown("### 📖 스토리")
            st.markdown("""
            <div style='background: #f8f9fa; padding: 30px; border-radius: 12px; 
                        border-left: 4px solid #667eea; line-height: 1.8; font-size: 1.1em;'>
            """ + story + """
            </div>
            """, unsafe_allow_html=True)
            
            st.success("✅ 스토리를 읽었어요!")
            
            # 스토리에서 배운 점
            st.markdown("---")
            st.subheader("💡 이 스토리에서 배운 점")
            st.info("스토리를 읽고 어떤 것을 배웠는지 '아이 채팅'에서 이야기해보세요!")
            
        except Exception as e:
            st.error(f"스토리 생성 중 오류가 발생했습니다: {str(e)}")

# 인기 스토리
st.markdown("---")
st.subheader("⭐ 인기 스토리")

popular_stories = [
    {
        "title": "🐷 저금통의 마법",
        "description": "작은 저금통이 큰 꿈을 이루는 이야기",
        "age": "5-8세"
    },
    {
        "title": "🛍️ 현명한 쇼핑",
        "description": "계획적으로 쇼핑하는 방법을 배우는 이야기",
        "age": "9-12세"
    },
    {
        "title": "⏰ 기다림의 선물",
        "description": "참고 기다렸을 때 얻는 특별한 선물",
        "age": "7-10세"
    }
]

for story in popular_stories:
    with st.expander(f"{story['title']} ({story['age']})"):
        st.markdown(story['description'])
        if st.button(f"📖 읽기", key=f"read_{story['title']}"):
            st.info("스토리를 생성하고 있어요...")

# 사이드바 추가 정보
with st.sidebar:
    st.markdown("---")
    st.markdown("### 💡 스토리 안내")
    st.info("""
    금융 스토리를 읽으면 돈에 대해 더 잘 이해할 수 있어요!
    
    **스토리 활용법:**
    1. 주제를 선택하고 읽기
    2. 스토리에서 배운 점 생각하기
    3. 실제 생활에 적용해보기
    """)
