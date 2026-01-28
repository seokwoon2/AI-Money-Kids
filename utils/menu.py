"""공통 메뉴 유틸리티"""
import streamlit as st
from database.db_manager import DatabaseManager

def render_sidebar_menu(user_id: int, user_name: str, user_type: str):
    """사이드바 메뉴 렌더링 - 아이 친화적 파스텔 카드 스타일"""
    
    # CSS 주입: 파스텔 톤 & 카드형 UI
    st.sidebar.markdown("""
    <style>
    /* 기본 네비게이션 제거 */
    [data-testid="stSidebarNav"] {display: none !important;}
    
    /* 사이드바 배경색 (연한 파스텔 블루) */
    .stSidebar {
        background-color: #f0f7ff !important;
    }
    
    /* 전체 컨테이너 여백 */
    [data-testid="stSidebarContent"] {
        padding: 20px 15px !important;
    }

    /* 프로필 카드 (파스텔 그라데이션) */
    .child-profile-card {
        background: linear-gradient(135deg, #ffcfdf 0%, #b0f3f1 100%);
        padding: 25px 20px;
        border-radius: 24px;
        margin-bottom: 20px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.05);
        text-align: center;
        border: 3px solid white;
    }
    .child-profile-card .user-type {
        background: white;
        color: #ff7eb3;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 800;
        display: inline-block;
        margin-bottom: 10px;
    }
    .child-profile-card .user-name {
        color: #4a4a4a;
        font-size: 22px;
        font-weight: 800;
    }

    /* 섹션 타이틀 */
    .child-section-title {
        color: #7a869a;
        font-size: 15px;
        font-weight: 700;
        padding: 15px 0 10px 10px;
    }

    /* 버튼 스타일 (카드형 UI) */
    .stButton > button {
        width: 100% !important;
        border: 2px solid white !important;
        background-color: white !important;
        color: #4a4a4a !important;
        padding: 15px 20px !important;
        text-align: left !important;
        font-size: 18px !important;
        font-weight: 700 !important;
        border-radius: 20px !important;
        margin-bottom: 12px !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.03) !important;
        transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        display: flex !important;
        align-items: center !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-5px) scale(1.02) !important;
        box-shadow: 0 12px 20px rgba(0,0,0,0.08) !important;
        border-color: #ffcfdf !important;
        color: #ff7eb3 !important;
    }

    /* 로그아웃 버튼 (파스텔 레드) */
    div[data-testid="stSidebar"] .stButton:last-child > button {
        background-color: #ffe3e3 !important;
        color: #ff6b6b !important;
        margin-top: 30px !important;
    }

    /* 애니메이션 효과 */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .stButton {
        animation: fadeIn 0.5s ease backwards;
    }
    </style>
    """, unsafe_allow_html=True)

    # 1. 프로필 섹션 (귀여운 카드)
    user_type_kr = "👑 부모님" if user_type == 'parent' else "⭐ 어린이"
    st.sidebar.markdown(f"""
    <div class="child-profile-card">
        <div class="user-type">{user_type_kr}</div>
        <div class="user-name">{user_name}님</div>
    </div>
    """, unsafe_allow_html=True)

    # 2. 내 정보 관리 (귀여운 버튼)
    if st.sidebar.button("👤 나의 정보 관리", key="child_user_info"):
        st.switch_page("pages/4_👤_내정보.py")

    # 3. 서비스 섹션
    st.sidebar.markdown('<div class="child-section-title">🎈 재미있는 서비스</div>', unsafe_allow_html=True)
    
    if st.sidebar.button("🏠 처음으로 (홈)", key="child_home"):
        st.switch_page("app.py")

    if user_type == 'parent':
        menu_items = [
            ("💼", "부모 상담실", "pages/3_💼_부모_상담실.py"),
            ("📊", "부모 대시보드", "pages/2_📊_부모_대시보드.py"),
            ("💰", "용돈 추천", "pages/5_💰_용돈_추천.py"),
            ("📚", "금융 교육 가이드", "pages/6_📚_금융_교육_가이드.py"),
            ("📝", "대화 기록", "pages/10_📝_대화_기록.py")
        ]
    else:
        menu_items = [
            ("💬", "AI 친구와 채팅", "pages/1_💬_아이_채팅.py"),
            ("🎯", "금융 미션", "pages/7_🎯_금융_미션.py"),
            ("📖", "금융 스토리", "pages/8_📖_금융_스토리.py"),
            ("💵", "용돈 관리", "pages/9_💵_용돈_관리.py"),
            ("📝", "대화 기록", "pages/10_📝_대화_기록.py")
        ]

    for icon, name, path in menu_items:
        if st.sidebar.button(f"{icon} {name}", key=f"child_{path}"):
            st.switch_page(path)

    # 4. 하단 설정
    st.sidebar.markdown('<div class="child-section-title">⚙️ 설정</div>', unsafe_allow_html=True)
    
    if st.sidebar.button("🔄 화면 새로고침", key="child_refresh"):
        st.rerun()
        
    if st.sidebar.button("🚪 로그아웃", key="child_logout"):
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.user_name = None
        st.session_state.messages = []
        st.session_state.conversation_id = None
        st.session_state.show_login_success = False
        st.switch_page("app.py")

def hide_sidebar_navigation():
    """기본 네비게이션 숨기기"""
    st.markdown("<style>[data-testid='stSidebarNav'] {display: none !important;}</style>", unsafe_allow_html=True)
