import streamlit as st
from services.conversation_service import ConversationService
from database.db_manager import DatabaseManager
from utils.menu import render_sidebar_menu, hide_sidebar_navigation
from datetime import datetime

st.set_page_config(
    page_title="📝 대화 기록",
    page_icon="📝",
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

# 서비스 초기화
conversation_service = ConversationService()

# 페이지 제목
st.title(f"📝 {user_name}님의 대화 기록")
st.markdown("---")

# 날짜별 대화 목록 가져오기
conversations = conversation_service.get_user_conversations_by_date(user_id)

if not conversations:
    st.info("아직 대화 기록이 없습니다. 채팅을 시작해보세요! 💬")
else:
    # 날짜별로 그룹화
    conversations_by_date = {}
    for conv in conversations:
        date_str = conv.get('date', '')
        if date_str not in conversations_by_date:
            conversations_by_date[date_str] = []
        conversations_by_date[date_str].append(conv)
    
    # 날짜 선택
    dates = sorted(conversations_by_date.keys(), reverse=True)
    selected_date = st.selectbox(
        "📅 날짜 선택",
        dates,
        key="date_selector"
    )
    
    if selected_date:
        st.markdown("---")
        
        # 선택한 날짜의 대화들
        date_conversations = conversations_by_date[selected_date]
        
        for idx, conv in enumerate(date_conversations):
            conversation_id = conv['conversation_id']
            message_count = conv.get('message_count', 0)
            first_time = conv.get('first_message_time', '')
            last_time = conv.get('last_message_time', '')
            
            # 시간 포맷팅
            try:
                if first_time:
                    first_dt = datetime.fromisoformat(first_time.replace('Z', '+00:00'))
                    first_time_str = first_dt.strftime("%H:%M")
                else:
                    first_time_str = ""
                
                if last_time:
                    last_dt = datetime.fromisoformat(last_time.replace('Z', '+00:00'))
                    last_time_str = last_dt.strftime("%H:%M")
                else:
                    last_time_str = ""
            except:
                first_time_str = first_time[:5] if first_time else ""
                last_time_str = last_time[:5] if last_time else ""
            
            # 대화 카드
            with st.expander(f"💬 대화 {idx + 1} ({first_time_str} ~ {last_time_str}, {message_count}개 메시지)", expanded=False):
                # 대화 내용 가져오기
                messages = conversation_service.get_all_messages(conversation_id)
                
                if messages:
                    # 요약 생성 (캐시 사용)
                    summary_key = f"summary_{conversation_id}"
                    if summary_key not in st.session_state:
                        with st.spinner("📝 요약 생성 중..."):
                            summary = conversation_service.summarize_conversation(conversation_id)
                            st.session_state[summary_key] = summary
                    else:
                        summary = st.session_state[summary_key]
                    
                    # 요약 표시
                    st.markdown("""
                    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                padding: 15px; border-radius: 10px; color: white; margin-bottom: 15px;'>
                        <h4 style='color: white; margin: 0 0 10px 0;'>📋 대화 요약</h4>
                        <p style='color: white; margin: 0; opacity: 0.95;'>{}</p>
                    </div>
                    """.format(summary), unsafe_allow_html=True)
                    
                    st.markdown("---")
                    st.markdown("### 💬 전체 대화 내용")
                    
                    # 대화 내용 표시
                    for msg in messages:
                        role = msg.get('role', '')
                        content = msg.get('content', '')
                        timestamp = msg.get('timestamp', '')
                        
                        # 시간 포맷팅
                        try:
                            if timestamp:
                                msg_dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                                time_str = msg_dt.strftime("%H:%M:%S")
                            else:
                                time_str = ""
                        except:
                            time_str = timestamp[:8] if timestamp else ""
                        
                        if role == 'user':
                            st.markdown(f"""
                            <div style='background: #f0f2f6; padding: 12px; border-radius: 8px; 
                                        margin-bottom: 10px; border-left: 4px solid #667eea;'>
                                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;'>
                                    <strong style='color: #667eea;'>👤 {user_name}</strong>
                                    <span style='color: #868e96; font-size: 0.85em;'>{time_str}</span>
                                </div>
                                <p style='margin: 0; color: #262730;'>{content}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                            <div style='background: #e8f4f8; padding: 12px; border-radius: 8px; 
                                        margin-bottom: 10px; border-left: 4px solid #48a9c5;'>
                                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;'>
                                    <strong style='color: #48a9c5;'>🤖 AI 어시스턴트</strong>
                                    <span style='color: #868e96; font-size: 0.85em;'>{time_str}</span>
                                </div>
                                <p style='margin: 0; color: #262730;'>{content}</p>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    # 요약 다시 생성 버튼
                    col1, col2 = st.columns([3, 1])
                    with col2:
                        if st.button("🔄 요약 다시 생성", key=f"refresh_summary_{conversation_id}", use_container_width=True):
                            if summary_key in st.session_state:
                                del st.session_state[summary_key]
                            st.rerun()
                else:
                    st.info("이 대화에는 메시지가 없습니다.")

# 사이드바 메뉴 렌더링
# render_sidebar_menu(user_id, user_name, user_type) # 위로 이동됨

# 사이드바 추가 정보
with st.sidebar:
    st.markdown("---")
    st.markdown("### 💡 대화 기록")
    st.info("""
    날짜별로 나눠진 대화 기록을 확인할 수 있습니다!
    
    **기능:**
    - 날짜별 대화 목록 확인
    - 대화 요약 자동 생성
    - 전체 대화 내용 보기
    """)
