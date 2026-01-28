import streamlit as st
from services.conversation_service import ConversationService
from database.db_manager import DatabaseManager
from utils.menu import render_sidebar_menu, hide_sidebar_navigation

st.set_page_config(
    page_title="💬 아이 채팅",
    page_icon="💬",
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
    st.warning("로그인이 필요합니다. 메인 페이지에서 로그인해주세요.")
    st.stop()

user_id = st.session_state.user_id
user_name = st.session_state.user_name

# 사용자 정보 가져오기
db = DatabaseManager()
user = db.get_user_by_id(user_id)
user_age = user.get('age') if user else None
user_type = user.get('user_type', 'child') if user else 'child'

# 아이 전용 페이지 확인
if user_type != 'child':
    st.warning("이 페이지는 아이 전용입니다. 부모님은 '부모 상담실' 페이지를 이용해주세요.")
    st.stop()

# 서비스 초기화
conversation_service = ConversationService()

# 세션 상태 초기화
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'conversation_id' not in st.session_state:
    st.session_state.conversation_id = conversation_service.get_or_create_conversation(user_id)

# 페이지 제목
st.title(f"💬 {user_name}님의 금융 상담실")
st.markdown("---")

# 대화 히스토리 로드
if not st.session_state.messages:
    conversation_id = st.session_state.conversation_id
    history = conversation_service.get_all_messages(conversation_id)
    
    for msg in history:
        st.session_state.messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })

# 채팅 메시지 표시
chat_container = st.container()
with chat_container:
    for message in st.session_state.messages:
        if message["role"] == "user":
            with st.chat_message("user"):
                st.write(message["content"])
        else:
            with st.chat_message("assistant"):
                st.write(message["content"])

# 사용자 입력
if prompt := st.chat_input("돈에 대해 궁금한 것을 물어보세요!"):
    # 사용자 메시지 추가
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    
    # AI 응답 생성
    with st.chat_message("assistant"):
        with st.spinner("생각 중..."):
            response = conversation_service.chat(
                user_id=user_id,
                user_message=prompt,
                user_name=user_name,
                user_age=user_age,
                user_type=user_type
            )
            st.write(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

# 사이드바 메뉴 렌더링
render_sidebar_menu(user_id, user_name, user_type)

# 사이드바 추가 정보
with st.sidebar:
    st.markdown("---")
    st.markdown("### 💡 팁")
    st.info("""
    돈에 대해 궁금한 것을 자유롭게 물어보세요!
    
    **예시 질문:**
    - 저축이 왜 중요한가요?
    - 용돈을 어떻게 관리하면 좋을까요?
    - 비싼 장난감을 사고 싶어요
    - 돈을 모으는 방법이 뭐예요?
    """)
    
    st.markdown("---")
    
    # 행동 기록 보기
    if st.button("📊 내 금융습관 보기", use_container_width=True):
        behaviors = db.get_user_behaviors(user_id, limit=10)
        if behaviors:
            st.subheader("최근 활동")
            for behavior in behaviors[:5]:
                behavior_type_kr = {
                    "saving": "💰 저축",
                    "planned_spending": "📝 계획적 소비",
                    "impulse_buying": "⚡ 충동구매",
                    "delayed_gratification": "⏰ 인내심",
                    "comparing_prices": "🔍 가격 비교"
                }.get(behavior['behavior_type'], behavior['behavior_type'])
                
                amount_str = f" - {behavior['amount']:,.0f}원" if behavior['amount'] else ""
                st.caption(f"{behavior_type_kr}{amount_str}")
        else:
            st.info("아직 기록된 활동이 없습니다.")
