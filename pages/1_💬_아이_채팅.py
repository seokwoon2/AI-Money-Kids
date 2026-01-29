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
try:
    conversation_service = ConversationService()
except Exception as e:
    st.error("⚠️ AI 서비스 초기화 중 오류가 발생했습니다.")
    st.info("관리자에게 문의해주세요.")
    st.stop()

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

# 중단 플래그 초기화
if 'cancel_generation' not in st.session_state:
    st.session_state.cancel_generation = False

# 사용자 입력
if prompt := st.chat_input("돈에 대해 궁금한 것을 물어보세요!"):
    # 중단 플래그 초기화
    st.session_state.cancel_generation = False
    
    # 사용자 메시지 추가
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    
    # AI 응답 생성
    with st.chat_message("assistant"):
        try:
            import time
            from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
            
            start_time = time.time()
            response = None
            
            # 스피너와 중단 버튼을 함께 표시
            spinner_container = st.container()
            with spinner_container:
                col_spinner, col_cancel = st.columns([3, 1])
                with col_spinner:
                    spinner_placeholder = st.empty()
                with col_cancel:
                    cancel_button = st.button("⏹️ 중단", key="cancel_button_child", use_container_width=True)
                
                if cancel_button:
                    st.session_state.cancel_generation = True
                    st.warning("⚠️ 응답 생성을 중단했습니다.")
                    st.rerun()
                
                with spinner_placeholder:
                    with st.spinner("💭 생각 중이에요..."):
                        def call_chat_service():
                            # 중단 플래그 확인
                            if st.session_state.get('cancel_generation', False):
                                return None
                            return conversation_service.chat(
                                user_id=user_id,
                                user_message=prompt,
                                user_name=user_name,
                                user_age=user_age,
                                user_type=user_type
                            )
                        
                        # 직접 API 호출 (타임아웃은 API 레벨에서 처리)
                        try:
                            if not st.session_state.get('cancel_generation', False):
                                response = call_chat_service()
                            else:
                                response = None
                        except Exception as api_error:
                            if not st.session_state.get('cancel_generation', False):
                                error_msg = str(api_error)
                                if len(error_msg) > 200:
                                    error_msg = error_msg[:200] + "..."
                                response = f"죄송해요, 오류가 발생했어요: {error_msg}"
                                
                                # 상세 에러 정보 표시
                                import traceback
                                with st.expander("🔍 상세 오류 정보", expanded=True):
                                    st.error(f"**오류 메시지:** {error_msg}")
                                    st.code(traceback.format_exc(), language="python")
                                    st.info("💡 이 정보를 개발자에게 전달해주시면 문제 해결에 도움이 됩니다.")
            
            # 중단되었는지 확인
            if st.session_state.get('cancel_generation', False):
                st.info("💡 응답 생성이 중단되었습니다. 새로운 질문을 입력해주세요.")
                st.session_state.cancel_generation = False
            elif response:
                elapsed_time = time.time() - start_time
                
                # 응답이 오류 메시지인지 확인
                if response.startswith("죄송해요"):
                    st.error(response)
                else:
                    st.write(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                    # 응답 시간이 너무 오래 걸렸으면 경고
                    if elapsed_time > 10:
                        st.caption(f"⏱️ 응답 시간: {elapsed_time:.1f}초")
            else:
                if not st.session_state.get('cancel_generation', False):
                    st.error("죄송해요, 응답을 받지 못했어요. 다시 시도해주세요.")
                    
        except Exception as e:
            if not st.session_state.get('cancel_generation', False):
                error_msg = str(e)
                st.error(f"죄송해요, 오류가 발생했어요: {error_msg}")
                st.info("페이지를 새로고침하거나 잠시 후 다시 시도해주세요.")

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
