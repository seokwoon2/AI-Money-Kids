"""공통 메뉴 유틸리티"""
import streamlit as st
from database.db_manager import DatabaseManager

def render_sidebar_menu(user_id: int, user_name: str, user_type: str):
    """사이드바 메뉴 렌더링 - 트렌디한 디자인"""
    # Streamlit 기본 네비게이션만 숨기기 (우리 메뉴는 보이게)
    st.sidebar.markdown("""
    <style>
    /* Streamlit 기본 네비게이션만 숨기기 */
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
    nav[data-testid="stSidebarNav"] {
        display: none !important;
    }
    ul[data-testid="stSidebarNav"] {
        display: none !important;
    }
    
    /* 토스 스타일 CSS */
    .stSidebar {
        background-color: #ffffff !important;
    }
    
    /* 사용자 프로필 영역 */
    .user-profile-section {
        padding: 20px 10px;
        margin-bottom: 10px;
    }
    .user-profile-section p {
        color: #8b95a1;
        font-size: 0.85em;
        margin: 0;
    }
    .user-profile-section h3 {
        color: #191f28;
        font-size: 1.25em;
        font-weight: 700;
        margin: 4px 0 0 0;
    }
    
    /* 섹션 타이틀 */
    .section-title {
        font-size: 0.8em;
        font-weight: 600;
        color: #8b95a1;
        margin: 25px 0 10px 10px;
    }
    
    /* 버튼 스타일 (토스 스타일) */
    .stButton > button {
        width: 100%;
        border: none !important;
        background-color: transparent !important;
        color: #4e5968 !important;
        padding: 12px 15px !important;
        text-align: left !important;
        font-size: 1em !important;
        font-weight: 500 !important;
        border-radius: 12px !important;
        transition: background-color 0.2s ease !important;
        display: flex !important;
        align-items: center !important;
        gap: 12px !important;
        margin-bottom: 4px !important;
    }
    
    .stButton > button:hover {
        background-color: #f2f4f6 !important;
        color: #191f28 !important;
    }
    
    /* 강조 버튼 (내 정보 등) */
    .stButton > button[kind="primary"] {
        background-color: #f2f4f6 !important;
        color: #3182f6 !important;
        font-weight: 600 !important;
    }
    
    /* 로그아웃 버튼 전용 */
    div[data-testid="stSidebar"] .stButton:last-child > button {
        margin-top: 30px !important;
        color: #f04452 !important;
        opacity: 0.8;
    }
    
    /* 구분선 */
    .divider {
        height: 1px;
        background-color: #f2f4f6;
        margin: 15px 10px;
    }

    /* 사이드바 내부 여백 조절 */
    [data-testid="stSidebarContent"] {
        padding-top: 1rem !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 사용자 프로필 (토스 스타일: 깔끔한 텍스트 중심)
    user_type_kr = "부모님" if user_type == 'parent' else "어린이"
    
    st.sidebar.markdown(f"""
    <div class="user-profile-section">
        <p>{user_type_kr} 회원</p>
        <h3>{user_name}님</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # 내 정보 버튼 (토스 스타일의 연한 회색 버튼)
    if st.sidebar.button("👤 내 정보 관리", key="user_info_button", use_container_width=True, type="primary"):
        st.switch_page("pages/4_👤_내정보.py")
    
    st.sidebar.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # 메뉴 섹션
    st.sidebar.markdown('<div class="section-title">서비스</div>', unsafe_allow_html=True)
    
    # 홈 메뉴
    if st.sidebar.button("🏠 홈", key="menu_home", use_container_width=True):
        st.switch_page("app.py")
    
    if user_type == 'parent':
        # 부모 메뉴
        menu_items = [
            ("💼", "부모 상담실", "pages/3_💼_부모_상담실.py"),
            ("📊", "부모 대시보드", "pages/2_📊_부모_대시보드.py"),
            ("💰", "용돈 추천", "pages/5_💰_용돈_추천.py"),
            ("📚", "금융 교육 가이드", "pages/6_📚_금융_교육_가이드.py"),
            ("📝", "대화 기록", "pages/10_📝_대화_기록.py")
        ]
    else:
        # 아이 메뉴
        menu_items = [
            ("💬", "아이 채팅", "pages/1_💬_아이_채팅.py"),
            ("🎯", "금융 미션", "pages/7_🎯_금융_미션.py"),
            ("📖", "금융 스토리", "pages/8_📖_금융_스토리.py"),
            ("💵", "용돈 관리", "pages/9_💵_용돈_관리.py"),
            ("📝", "대화 기록", "pages/10_📝_대화_기록.py")
        ]
    
    # 메뉴 버튼 렌더링
    for icon, name, page_path in menu_items:
        if st.sidebar.button(
            f"{icon} {name}",
            key=f"menu_{page_path}",
            use_container_width=True
        ):
            st.switch_page(page_path)
    
    st.sidebar.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.sidebar.markdown('<div class="section-title">설정 및 도구</div>', unsafe_allow_html=True)
    
    # 새로고침 버튼
    if st.sidebar.button("🔄 화면 새로고침", use_container_width=True, key="refresh_button"):
        st.rerun()
    
    # 로그아웃 버튼
    if st.sidebar.button("🚪 로그아웃", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.user_name = None
        st.session_state.messages = []
        st.session_state.conversation_id = None
        st.session_state.show_login_success = False
        st.switch_page("app.py")
    
    st.sidebar.markdown('</div>', unsafe_allow_html=True)

def hide_sidebar_navigation():
    """사이드바 네비게이션 숨기기 (로그인하지 않았을 때)"""
    st.markdown("""
    <style>
    /* Streamlit 기본 네비게이션만 숨기기 */
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
    nav[data-testid="stSidebarNav"] {
        display: none !important;
    }
    ul[data-testid="stSidebarNav"] {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)
