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
    
    /* 상단 유틸리티 아이콘 행 */
    .top-utility-row {
        display: flex;
        justify-content: space-around;
        padding: 10px 5px;
        margin-bottom: 20px;
        border-bottom: 1px solid #f2f4f6;
    }
    .utility-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 5px;
        cursor: pointer;
        text-decoration: none;
        color: #4e5968;
    }
    .utility-item:hover {
        color: #191f28;
    }
    .utility-icon {
        font-size: 1.5em;
    }
    .utility-label {
        font-size: 0.75em;
        font-weight: 500;
    }
    
    /* 사용자 프로필 영역 */
    .user-profile-section {
        padding: 10px 15px;
        margin-bottom: 15px;
    }
    .user-profile-section p {
        color: #8b95a1;
        font-size: 0.85em;
        margin: 0;
    }
    .user-profile-section h3 {
        color: #191f28;
        font-size: 1.3em;
        font-weight: 700;
        margin: 4px 0 0 0;
    }
    
    /* 섹션 타이틀 */
    .section-title {
        font-size: 0.85em;
        font-weight: 600;
        color: #8b95a1;
        margin: 25px 0 10px 15px;
    }
    
    /* 메뉴 버튼 스타일 (토스 스타일: 아이콘 + 텍스트 + 화살표) */
    .stButton > button {
        width: 100%;
        border: none !important;
        background-color: transparent !important;
        color: #333d4b !important;
        padding: 14px 15px !important;
        text-align: left !important;
        font-size: 1.05em !important;
        font-weight: 500 !important;
        border-radius: 0 !important;
        transition: background-color 0.15s ease !important;
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
        margin-bottom: 0 !important;
    }
    
    .stButton > button:hover {
        background-color: #f9fafb !important;
    }
    
    /* 버튼 내부 텍스트와 아이콘 정렬 */
    .button-content {
        display: flex;
        align-items: center;
        gap: 15px;
    }
    .arrow-icon {
        color: #cccfd8;
        font-size: 0.9em;
    }
    
    /* 구분선 */
    .divider {
        height: 8px;
        background-color: #f2f4f6;
        margin: 10px 0;
    }

    /* 사이드바 내부 여백 제거 */
    [data-testid="stSidebarContent"] {
        padding-top: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 상단 유틸리티 행 (알림, 설정, 고객센터 느낌)
    st.sidebar.markdown(f"""
    <div class="top-utility-row">
        <div class="utility-item" onclick="window.location.reload();">
            <span class="utility-icon">🔔</span>
            <span class="utility-label">알림</span>
        </div>
        <div class="utility-item" onclick="document.querySelector('button[key=user_info_button]').click();">
            <span class="utility-icon">⚙️</span>
            <span class="utility-label">설정</span>
        </div>
        <div class="utility-item" onclick="alert('고객센터 준비 중입니다.');">
            <span class="utility-icon">🎧</span>
            <span class="utility-label">고객센터</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 사용자 프로필
    user_type_kr = "부모님" if user_type == 'parent' else "어린이"
    st.sidebar.markdown(f"""
    <div class="user-profile-section">
        <p>{user_type_kr} 회원</p>
        <h3>{user_name}님</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # 내 정보 관리 버튼 (숨겨진 트리거용 및 실제 버튼)
    if st.sidebar.button("👤 내 정보 관리", key="user_info_button", use_container_width=True):
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
    
    # 메뉴 버튼 렌더링 (토스 스타일: 우측 화살표 추가)
    for icon, name, page_path in menu_items:
        # Streamlit 버튼은 내부 HTML 수정이 어려우므로 CSS로 화살표 느낌을 흉내내거나 
        # 버튼 텍스트에 화살표를 포함시킵니다.
        if st.sidebar.button(
            f"{icon} {name} 〉", # 〉 문자로 토스 스타일 화살표 재현
            key=f"menu_{page_path}",
            use_container_width=True
        ):
            st.switch_page(page_path)
    
    st.sidebar.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # 로그아웃 및 기타
    if st.sidebar.button("🚪 로그아웃 〉", use_container_width=True):
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
