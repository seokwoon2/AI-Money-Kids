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

# 사이드바 메뉴 렌더링 (가장 먼저 실행하여 메뉴 유실 방지)
render_sidebar_menu(user_id, user_name, user_type)

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
st.markdown(f"""
<div style='display: flex; align-items: center; gap: 15px; margin-bottom: 20px;'>
    <div style='font-size: 40px;'>💼</div>
    <h1 style='margin: 0;'>{user_name}님의 부모 상담실</h1>
</div>
<div style='background-color: #f8faff; padding: 20px; border-radius: 15px; border-left: 5px solid #6366f1; margin-bottom: 30px;'>
    <p style='margin: 0; color: #4a5568; font-weight: 600;'>
        자녀의 올바른 경제 습관 형성을 위해 AI 전문가와 상담해보세요. 
        아이의 대화 기록과 행동 데이터를 바탕으로 맞춤형 조언을 드립니다.
    </p>
</div>
""", unsafe_allow_html=True)

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
if prompt := st.chat_input("자녀 금융 교육에 대해 궁금한 것을 물어보세요!"):
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
            response_text = None
            error_occurred = False
            
            # 스피너와 중단 버튼을 함께 표시
            spinner_container = st.container()
            with spinner_container:
                col_spinner, col_cancel = st.columns([3, 1])
                with col_spinner:
                    spinner_placeholder = st.empty()
                with col_cancel:
                    cancel_button = st.button("⏹️ 중단", key="cancel_button", use_container_width=True)
                
                if cancel_button:
                    st.session_state.cancel_generation = True
                    st.warning("⚠️ 응답 생성을 중단했습니다.")
                    st.rerun()
                
                with spinner_placeholder:
                    with st.spinner("💭 AI가 답변을 준비하고 있어요..."):
                        # 직접 API 호출
                        try:
                            if not st.session_state.get('cancel_generation', False):
                                # conversation_service를 직접 호출
                                response_text = conversation_service.chat(
                                    user_id=user_id,
                                    user_message=prompt,
                                    user_name=user_name,
                                    user_age=None,
                                    user_type='parent'
                                )
                                
                                # 응답이 None이거나 비어있는지 확인
                                if not response_text or response_text.strip() == "":
                                    response_text = "죄송해요, 응답을 받지 못했어요. 다시 시도해주세요."
                                    error_occurred = True
                            else:
                                response_text = None
                                    
                        except Exception as api_error:
                            if not st.session_state.get('cancel_generation', False):
                                error_msg = str(api_error)
                                # 에러 메시지가 너무 길면 자르기
                                if len(error_msg) > 500:
                                    error_msg = error_msg[:500] + "..."
                                
                                # 이미 에러 메시지 형식인지 확인
                                if error_msg.startswith("죄송해요"):
                                    response_text = error_msg
                                else:
                                    response_text = f"죄송해요, 오류가 발생했어요: {error_msg}"
                                error_occurred = True
                                
                                # 항상 상세 에러 정보 표시 (디버깅용)
                                import traceback
                                import json
                                
                                # 전체 에러 정보를 하나의 텍스트로 구성
                                full_error_text = f"""오류 메시지:
{error_msg}

상세 오류 정보:
{traceback.format_exc()}

발생 시간: {time.strftime('%Y-%m-%d %H:%M:%S')}
사용자: {user_name} (ID: {user_id})
질문: {prompt}
"""
                                
                                with st.expander("🔍 상세 오류 정보 (문제 해결용)", expanded=True):
                                    st.error(f"**오류 메시지:** {error_msg}")
                                    
                                    # 에러 정보를 텍스트 영역에 표시 (복사 가능)
                                    st.text_area(
                                        "📋 전체 오류 정보 (아래 텍스트를 복사하여 개발자에게 전달해주세요)",
                                        value=full_error_text,
                                        height=300,
                                        key=f"error_text_{time.time()}",
                                        help="이 텍스트를 모두 선택(Ctrl+A)하고 복사(Ctrl+C)하여 개발자에게 전달해주세요."
                                    )
                                    
                                    # 복사 버튼 (JavaScript 사용)
                                    st.markdown("""
                                    <button onclick="copyErrorText()" style="
                                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                        color: white;
                                        border: none;
                                        padding: 10px 20px;
                                        border-radius: 5px;
                                        cursor: pointer;
                                        font-weight: bold;
                                        margin-top: 10px;
                                    ">📋 에러 정보 복사하기</button>
                                    
                                    <script>
                                    function copyErrorText() {
                                        // 가장 최근 에러 텍스트 영역 찾기
                                        const textAreas = document.querySelectorAll('textarea[data-testid*="error_text"]');
                                        if (textAreas.length > 0) {
                                            const latestTextArea = textAreas[textAreas.length - 1];
                                            latestTextArea.select();
                                            latestTextArea.setSelectionRange(0, 99999); // 모바일 지원
                                            try {
                                                document.execCommand('copy');
                                                alert('✅ 에러 정보가 클립보드에 복사되었습니다!');
                                            } catch(err) {
                                                alert('❌ 복사에 실패했습니다. 텍스트를 수동으로 선택하여 복사해주세요.');
                                            }
                                        }
                                    }
                                    </script>
                                    """, unsafe_allow_html=True)
                                    
                                    st.info("💡 위의 '에러 정보 복사하기' 버튼을 클릭하거나, 텍스트 영역의 내용을 직접 복사하여 개발자에게 전달해주세요.")
                                    st.warning("⚠️ API 키가 올바른지, 네트워크 연결이 정상인지 확인해주세요.")
            
            # 중단되었는지 확인
            if st.session_state.get('cancel_generation', False):
                st.info("💡 응답 생성이 중단되었습니다. 새로운 질문을 입력해주세요.")
                st.session_state.cancel_generation = False
            elif response_text:
                elapsed_time = time.time() - start_time
                
                # 응답이 오류 메시지인지 확인
                if response_text.startswith("죄송해요") or error_occurred:
                    st.error(response_text)
                    if not error_occurred:
                        st.info("💡 네트워크 연결을 확인하거나 잠시 후 다시 시도해주세요.")
                else:
                    st.write(response_text)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
                    
                    # 응답 시간 표시
                    if elapsed_time > 5:
                        st.caption(f"⏱️ 응답 시간: {elapsed_time:.1f}초")
            else:
                if not st.session_state.get('cancel_generation', False):
                    st.error("죄송해요, 응답을 받지 못했어요. 다시 시도해주세요.")
                
        except Exception as e:
            if not st.session_state.get('cancel_generation', False):
                error_msg = str(e)
                st.error(f"죄송해요, 예상치 못한 오류가 발생했어요: {error_msg[:200]}")
                st.info("💡 페이지를 새로고침하거나 잠시 후 다시 시도해주세요.")
                
                # 개발 모드에서만 상세 에러 표시
                import os
                if os.getenv("DEBUG", "false").lower() == "true":
                    import traceback
                    with st.expander("🔍 상세 오류 정보 (개발 모드)"):
                        st.code(traceback.format_exc(), language=None)

# 사이드바 메뉴 렌더링
# render_sidebar_menu(user_id, user_name, user_type) # 위로 이동됨

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
