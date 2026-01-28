"""공통 메뉴 유틸리티"""
import streamlit as st
from database.db_manager import DatabaseManager

def render_sidebar_menu(user_id: int, user_name: str, user_type: str):
    """사이드바 메뉴 렌더링 - 깔끔한 앱 스타일"""
    
    # CSS 주입: 정렬 및 간격 최적화
    st.sidebar.markdown("""
    <style>
    /* 기본 네비게이션 제거 */
    [data-testid="stSidebarNav"] {display: none !important;}
    
    /* 사이드바 배경색 */
    .stSidebar {
        background-color: #ffffff !important;
        border-right: 1px solid #f0f2f6;
    }
    
    /* 전체 컨테이너 여백 조정 */
    [data-testid="stSidebarContent"] {
        padding: 0 !important;
    }

    /* 상단 로고/프로필 영역 */
    .sidebar-header {
        padding: 30px 20px 20px 20px;
        background-color: #f8faff;
        border-bottom: 1px solid #edf2f7;
    }
    .user-badge {
        background-color: #eef2ff;
        color: #6366f1;
        padding: 4px 10px;
        border-radius: 8px;
        font-size: 12px;
        font-weight: 700;
        display: inline-block;
        margin-bottom: 8px;
    }
    .user-name-title {
        color: #1a202c;
        font-size: 20px;
        font-weight: 700;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* 메뉴 섹션 타이틀 */
    .menu-group-title {
        color: #a0aec0;
        font-size: 12px;
        font-weight: 700;
        padding: 25px 20px 10px 20px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* 버튼 스타일 최적화 */
    .stButton > button {
        width: 100% !important;
        border: none !important;
        background-color: transparent !important;
        color: #4a5568 !important;
        padding: 10px 20px !important;
        text-align: left !important;
        font-size: 15px !important;
        font-weight: 500 !important;
        border-radius: 12px !important;
        margin: 2px 0 !important;
        display: flex !important;
        align-items: center !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton > button:hover {
        background-color: #f7fafc !important;
        color: #6366f1 !important;
        transform: translateX(4px);
    }

    /* 아이콘과 텍스트 정렬 */
    .stButton > button div[data-testid="stMarkdownContainer"] p {
        margin: 0 !important;
        display: flex !important;
        align-items: center !important;
        gap: 12px !important;
    }

    /* 하단 로그아웃 영역 */
    .sidebar-footer {
        position: absolute;
        bottom: 0;
        width: 100%;
        padding: 20px;
        background-color: #ffffff;
        border-top: 1px solid #edf2f7;
    }
    </style>
    """, unsafe_allow_html=True)

    # 1. 상단 프로필 헤더
    user_type_kr = "부모님 모드" if user_type == 'parent' else "어린이 모드"
    user_icon = "👨‍👩‍👧" if user_type == 'parent' else "🐣"
    
    st.sidebar.markdown(f"""
    <div class="sidebar-header">
        <div class="user-badge">{user_type_kr}</div>
        <h3 class="user-name-title">{user_icon} {user_name}님</h3>
    </div>
    """, unsafe_allow_html=True)

    # 2. 계정 관리 섹션
    st.sidebar.markdown('<div class="menu-group-title">계정 관리</div>', unsafe_allow_html=True)
    if st.sidebar.button("👤 내 정보 수정", key="side_user_info"):
        st.switch_page("pages/4_👤_내정보.py")

    # 3. 서비스 메뉴 섹션
    st.sidebar.markdown('<div class="menu-group-title">금융 교육 서비스</div>', unsafe_allow_html=True)
    
    if st.sidebar.button("🏠 홈으로 가기", key="side_home"):
        st.switch_page("app.py")

    if user_type == 'parent':
        menu_items = [
            ("💼", "부모 상담실", "pages/3_💼_부모_상담실.py"),
            ("📊", "자녀 대시보드", "pages/2_📊_부모_대시보드.py"),
            ("💰", "용돈 추천기", "pages/5_💰_용돈_추천.py"),
            ("📚", "교육 가이드", "pages/6_📚_금융_교육_가이드.py"),
            ("📝", "대화 히스토리", "pages/10_📝_대화_기록.py")
        ]
    else:
        menu_items = [
            ("💬", "AI 친구와 채팅", "pages/1_💬_아이_채팅.py"),
            ("🎯", "오늘의 미션", "pages/7_🎯_금융_미션.py"),
            ("📖", "금융 스토리", "pages/8_📖_금융_스토리.py"),
            ("💵", "용돈 기입장", "pages/9_💵_용돈_관리.py"),
            ("📝", "나의 대화 기록", "pages/10_📝_대화_기록.py")
        ]

    for icon, name, path in menu_items:
        if st.sidebar.button(f"{icon} {name}", key=f"side_{path}"):
            st.switch_page(path)

    # 4. 하단 설정 섹션
    st.sidebar.markdown('<div class="menu-group-title">시스템</div>', unsafe_allow_html=True)
    
    if st.sidebar.button("🔄 화면 새로고침", key="side_refresh"):
        st.rerun()
        
    if st.sidebar.button("🚪 로그아웃", key="side_logout"):
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
