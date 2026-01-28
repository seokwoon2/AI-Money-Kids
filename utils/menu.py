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
    
    /* 트렌디한 CSS 스타일 */
    /* 사용자 프로필 카드 */
    .user-profile-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 24px;
        border-radius: 16px 16px 0 0;
        color: white;
        margin-bottom: 0;
        box-shadow: 0 8px 16px rgba(102, 126, 234, 0.3);
        position: relative;
        overflow: hidden;
    }
    .user-profile-card::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
        animation: pulse 3s ease-in-out infinite;
    }
    @keyframes pulse {
        0%, 100% { transform: scale(1); opacity: 0.5; }
        50% { transform: scale(1.1); opacity: 0.3; }
    }
    .user-profile-card h3 {
        margin: 0;
        font-size: 1.4em;
        font-weight: 600;
        color: white;
        position: relative;
        z-index: 1;
    }
    .user-profile-card p {
        margin: 8px 0 0 0;
        opacity: 0.95;
        font-size: 0.95em;
        position: relative;
        z-index: 1;
    }
    
    /* 내정보 버튼 컨테이너 */
    .profile-button-wrapper {
        margin-top: 0;
        margin-bottom: 24px;
    }
    .profile-button-wrapper button {
        border-radius: 0 0 16px 16px !important;
        border-top: none !important;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        font-weight: 500 !important;
        padding: 12px !important;
        transition: all 0.3s ease !important;
    }
    .profile-button-wrapper button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4) !important;
    }
    
    /* 섹션 제목 */
    .section-title {
        font-size: 0.85em;
        font-weight: 600;
        color: #667eea;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin: 24px 0 12px 0;
        padding-left: 4px;
    }
    
    /* 메뉴 버튼 스타일 개선 */
    .stButton > button {
        border-radius: 12px !important;
        padding: 12px 20px !important;
        font-weight: 500 !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        border: 1px solid #e9ecef !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2) !important;
        border-color: #667eea !important;
    }
    .stButton > button[kind="secondary"] {
        background: white !important;
        color: #262730 !important;
    }
    .stButton > button[kind="secondary"]:hover {
        background: #f8f9fa !important;
        color: #667eea !important;
    }
    
    /* 설정 섹션 */
    .settings-section {
        margin-top: 24px;
        padding-top: 24px;
        border-top: 1px solid #e9ecef;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 사용자 프로필 카드
    user_type_kr = "부모 계정" if user_type == 'parent' else "아이 계정"
    user_type_icon = "👨‍👩‍👧" if user_type == 'parent' else "👶"
    
    st.sidebar.markdown(f"""
    <div class="user-profile-card">
        <h3>{user_type_icon} {user_name}님</h3>
        <p>{user_type_kr}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 내정보 버튼
    st.sidebar.markdown('<div class="profile-button-wrapper">', unsafe_allow_html=True)
    if st.sidebar.button("👤 내 정보", key="user_info_button", use_container_width=True):
        st.switch_page("pages/4_👤_내정보.py")
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    
    # 메뉴 섹션
    st.sidebar.markdown('<div class="section-title">📋 서비스</div>', unsafe_allow_html=True)
    
    # 홈 메뉴 추가 (다른 메뉴와 동일한 형태)
    if st.sidebar.button("🏠 홈", key="menu_home", use_container_width=True, type="secondary"):
        st.switch_page("app.py")
    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    
    if user_type == 'parent':
        # 부모 메뉴
        menu_items = [
            ("💼", "부모 상담실", "pages/3_💼_부모_상담실.py"),
            ("📊", "부모 대시보드", "pages/2_📊_부모_대시보드.py"),
            ("💰", "용돈 추천", "pages/5_💰_용돈_추천.py"),
            ("📚", "금융 교육 가이드", "pages/6_📚_금융_교육_가이드.py")
        ]
    else:
        # 아이 메뉴
        menu_items = [
            ("💬", "아이 채팅", "pages/1_💬_아이_채팅.py"),
            ("🎯", "금융 미션", "pages/7_🎯_금융_미션.py"),
            ("📖", "금융 스토리", "pages/8_📖_금융_스토리.py"),
            ("💵", "용돈 관리", "pages/9_💵_용돈_관리.py")
        ]
    
    # 메뉴 버튼 렌더링 (모두 동일한 형태)
    for icon, name, page_path in menu_items:
        if st.sidebar.button(
            f"{icon} {name}",
            key=f"menu_{page_path}",
            use_container_width=True,
            type="secondary"
        ):
            st.switch_page(page_path)
        st.sidebar.markdown("<br>", unsafe_allow_html=True)
    
    # 설정 섹션
    st.sidebar.markdown('<div class="settings-section">', unsafe_allow_html=True)
    st.sidebar.markdown('<div class="section-title">⚙️ 계정</div>', unsafe_allow_html=True)
    
    # 새로고침 버튼
    if st.sidebar.button("🔄 새로고침", use_container_width=True, key="refresh_button"):
        st.rerun()
    
    # 새 탭에서 열기 링크
    st.sidebar.markdown("""
    <a href="#" onclick="window.open(window.location.href, '_blank'); return false;" 
       style="display: block; text-align: center; padding: 10px; background: #f0f2f6; 
              border-radius: 8px; text-decoration: none; color: #262730; margin: 10px 0;">
       🪟 새 탭에서 열기
    </a>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    
    if st.sidebar.button("🚪 로그아웃", use_container_width=True, type="primary"):
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.user_name = None
        st.session_state.messages = []
        st.session_state.conversation_id = None
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
