import streamlit as st
from services.conversation_service import ConversationService
from database.db_manager import DatabaseManager
from utils.menu import render_sidebar_menu, hide_sidebar_navigation

st.set_page_config(
    page_title="💼 부모 상담실",
    page_icon="💼",
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
user_type = user.get('user_type', 'child') if user else 'child'

# 부모 전용 페이지 확인
if user_type != 'parent':
    st.warning("이 페이지는 부모 전용입니다. 아이는 '아이 채팅' 페이지를 이용해주세요.")
    st.stop()

# 서비스 초기화
conversation_service = ConversationService()

# 세션 상태 초기화
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'conversation_id' not in st.session_state:
    st.session_state.conversation_id = conversation_service.get_or_create_conversation(user_id)

# 페이지 제목
st.title(f"💼 {user_name}님의 부모 상담실")
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
if prompt := st.chat_input("자녀 금융 교육에 대해 궁금한 것을 물어보세요!"):
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
                user_age=None,
                user_type='parent'
            )
            st.write(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

# 사이드바 메뉴 렌더링
render_sidebar_menu(user_id, user_name, user_type)

# 사이드바 추가 정보
with st.sidebar:
    st.markdown("---")
    st.markdown("### 💡 부모 상담실")
    st.info("""
    자녀의 금융 교육에 대해 전문적인 조언을 받을 수 있습니다!
    
    **예시 질문:**
    - 자녀에게 저축 습관을 어떻게 기르면 좋을까요?
    - 용돈을 얼마나 주는 것이 적당할까요?
    - 아이가 충동구매를 자주 하는데 어떻게 도와야 할까요?
    - 금융 교육을 시작하기 좋은 나이는 언제인가요?
    - 자녀와 돈에 대해 어떻게 대화하면 좋을까요?
    """)
    
    st.markdown("---")
    
    # 자녀 목록 보기
    parent_code = user.get('parent_code')
    if parent_code:
        children = db.get_users_by_parent_code(parent_code)
        if children:
            st.markdown("### 👨‍👩‍👧 자녀 목록")
            for child in children:
                st.caption(f"• {child['name']} ({child.get('age', '?')}세)")
        else:
            st.info("아직 등록된 자녀가 없습니다.")
