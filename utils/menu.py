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
    
    /* 사이드바 전체 여백 조정 */
    [data-testid="stSidebarContent"] {
        padding: 0 !important;
    }

    /* 사용자 프로필 영역 */
    .user-profile-section {
        padding: 30px 20px 10px 20px;
    }
    .user-profile-section p {
        color: #8b95a1;
        font-size: 0.9em;
        margin: 0;
        font-weight: 500;
    }
    .user-profile-section h3 {
        color: #191f28;
        font-size: 1.5em;
        font-weight: 700;
        margin: 5px 0 0 0;
    }
    
    /* 섹션 타이틀 */
    .section-title {
        font-size: 0.85em;
        font-weight: 600;
        color: #8b95a1;
        margin: 30px 0 10px 20px;
    }
    
    /* 버튼 스타일 (토스 스타일: 왼쪽 정렬 강조) */
    .stButton > button {
        width: 100% !important;
        border: none !important;
        background-color: transparent !important;
        color: #333d4b !important;
        padding: 12px 20px !important;
        text-align: left !important;
        font-size: 1.1em !important;
        font-weight: 500 !important;
        border-radius: 0 !important;
        transition: all 0.1s ease !important;
        display: flex !important;
        justify-content: flex-start !important; /* 왼쪽 정렬 강제 */
        align-items: center !important;
        margin: 0 !important;
    }
    
    /* 버튼 내부 텍스트 정렬 */
    .stButton > button div[data-testid="stMarkdownContainer"] p {
        text-align: left !important;
        width: 100% !important;
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
    }
    
    .stButton > button:hover {
        background-color: #f9fafb !important;
        color: #3182f6 !important;
    }
    
    /* 구분선 (얇고 깔끔하게) */
    .divider {
        height: 1px;
        background-color: #f2f4f6;
        margin: 10px 20px;
    }
    
    /* 두꺼운 구분선 (섹션 분리용) */
    .thick-divider {
        height: 10px;
        background-color: #f2f4f6;
        margin: 20px 0;
    }

    /* 로그아웃 버튼 (하단 배치 및 색상 변경) */
    .logout-box {
        margin-top: 20px;
    }
    .logout-box button {
        color: #8b95a1 !important;
        font-size: 0.95em !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 사용자 프로필
    user_type_kr = "부모님" if user_type == 'parent' else "어린이"
    st.sidebar.markdown(f"""
    <div class="user-profile-section">
        <p>{user_type_kr} 회원</p>
        <h3>{user_name}님</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # 내 정보 관리 (프로필 바로 아래 배치)
    if st.sidebar.button("👤 내 정보 관리", key="user_info_button", use_container_width=True):
        st.switch_page("pages/4_👤_내정보.py")
    
    st.sidebar.markdown('<div class="thick-divider"></div>', unsafe_allow_html=True)
    
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
    
    # 메뉴 버튼 렌더링 (왼쪽 정렬 및 우측 화살표)
    for icon, name, page_path in menu_items:
        if st.sidebar.button(
            f"{icon} {name}                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   〉", 
            key=f"menu_{page_path}",
            use_container_width=True
        ):
            st.switch_page(page_path)
    
    st.sidebar.markdown('<div class="thick-divider"></div>', unsafe_allow_html=True)
    
    # 하단 도구 (새로고침, 로그아웃)
    if st.sidebar.button("🔄 화면 새로고침", use_container_width=True, key="refresh_button"):
        st.rerun()
    
    st.sidebar.markdown('<div class="logout-box">', unsafe_allow_html=True)
    if st.sidebar.button("🚪 로그아웃", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.user_name = None
        st.session_state.messages = []
        st.session_state.conversation_id = None
        st.session_state.show_login_success = False
        st.switch_page("app.py")
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    
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
