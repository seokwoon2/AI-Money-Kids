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
        padding: 20px;
        border-radius: 16px;
        color: white;
        margin-bottom: 10px;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
        position: relative;
        overflow: hidden;
    }
    .user-profile-card h3 {
        margin: 0;
        font-size: 1.2em;
        font-weight: 600;
        color: white;
    }
    .user-profile-card p {
        margin: 4px 0 0 0;
        opacity: 0.8;
        font-size: 0.85em;
    }
    
    /* 메뉴 섹션 스타일 */
    .section-title {
        font-size: 0.75em;
        font-weight: 700;
        color: #adb5bd;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        margin: 20px 0 8px 5px;
    }
    
    /* 버튼 스타일 전면 개편 */
    .stButton > button {
        width: 100%;
        border: none !important;
        background-color: transparent !important;
        color: #495057 !important;
        padding: 10px 15px !important;
        text-align: left !important;
        font-size: 0.95em !important;
        border-radius: 10px !important;
        transition: all 0.2s ease !important;
        display: flex !important;
        align-items: center !important;
        gap: 10px !important;
        margin-bottom: 2px !important;
    }
    
    .stButton > button:hover {
        background-color: #f1f3f5 !important;
        color: #667eea !important;
        transform: translateX(5px);
    }
    
    /* 활성화된 메뉴 느낌 (Streamlit 한계상 hover와 유사하게) */
    .stButton > button:active {
        background-color: #e7f5ff !important;
        color: #667eea !important;
    }

    /* 로그아웃 버튼 (별도 스타일) */
    div[data-testid="stSidebar"] .stButton:last-child > button {
        margin-top: 20px !important;
        background-color: #fff5f5 !important;
        color: #fa5252 !important;
    }
    div[data-testid="stSidebar"] .stButton:last-child > button:hover {
        background-color: #ffe3e3 !important;
        transform: none !important;
    }

    /* 사이드바 너비 조절 및 패딩 */
    [data-testid="stSidebar"] .block-container {
        padding-top: 2rem !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 사용자 프로필 카드
    user_type_kr = "부모님 회원" if user_type == 'parent' else "어린이 회원"
    user_type_icon = "✨"
    
    st.sidebar.markdown(f"""
    <div class="user-profile-card">
        <p>{user_type_kr}</p>
        <h3>{user_name}님, 반가워요!</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # 내정보 버튼 (프로필 카드 바로 아래)
    if st.sidebar.button("👤 내 정보 관리", key="user_info_button", use_container_width=True):
        st.switch_page("pages/4_👤_내정보.py")
    
    # 메뉴 섹션
    st.sidebar.markdown('<div class="section-title">주요 서비스</div>', unsafe_allow_html=True)
    
    # 홈 메뉴
    if st.sidebar.button("🏠 홈으로 돌아가기", key="menu_home", use_container_width=True):
        st.switch_page("app.py")
    
    if user_type == 'parent':
        # 부모 메뉴
        menu_items = [
            ("💼", "부모 상담실", "pages/3_💼_부모_상담실.py"),
            ("📊", "부모 대시보드", "pages/2_📊_부모_대시보드.py"),
            ("💰", "용돈 추천 서비스", "pages/5_💰_용돈_추천.py"),
            ("📚", "금융 교육 가이드", "pages/6_📚_금융_교육_가이드.py"),
            ("📝", "전체 대화 기록", "pages/10_📝_대화_기록.py")
        ]
    else:
        # 아이 메뉴
        menu_items = [
            ("💬", "AI 친구와 채팅", "pages/1_💬_아이_채팅.py"),
            ("🎯", "오늘의 금융 미션", "pages/7_🎯_금융_미션.py"),
            ("📖", "재미있는 금융 스토리", "pages/8_📖_금융_스토리.py"),
            ("💵", "나의 용돈 관리", "pages/9_💵_용돈_관리.py"),
            ("📝", "채팅 기록 보기", "pages/10_📝_대화_기록.py")
        ]
    
    # 메뉴 버튼 렌더링
    for icon, name, page_path in menu_items:
        if st.sidebar.button(
            f"{icon} {name}",
            key=f"menu_{page_path}",
            use_container_width=True
        ):
            st.switch_page(page_path)
    
    # 기타 도구 섹션
    st.sidebar.markdown('<div class="section-title">기타 도구</div>', unsafe_allow_html=True)
    
    # 새로고침 버튼
    if st.sidebar.button("🔄 화면 새로고침", use_container_width=True, key="refresh_button"):
        st.rerun()
    
    # 새 탭에서 열기
    st.sidebar.markdown(f"""
    <a href="javascript:window.open(window.location.href, '_blank');" 
       style="display: block; text-align: left; padding: 10px 15px; color: #495057; 
              text-decoration: none; font-size: 0.95em; border-radius: 10px; margin-bottom: 2px;
              transition: all 0.2s ease;"
       onmouseover="this.style.backgroundColor='#f1f3f5'; this.style.color='#667eea'; this.style.paddingLeft='20px';"
       onmouseout="this.style.backgroundColor='transparent'; this.style.color='#495057'; this.style.paddingLeft='15px';">
       🪟 새 창으로 열기
    </a>
    """, unsafe_allow_html=True)
    
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
