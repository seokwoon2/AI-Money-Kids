"""공통 메뉴 유틸리티 - 카카오뱅크 스타일 UI 개편"""
import streamlit as st
from database.db_manager import DatabaseManager

def render_sidebar_menu(user_id: int, user_name: str, user_type: str):
    """사이드바 메뉴 렌더링 - 카카오뱅크 스타일 (노란색 액센트, 라운드 스타일)"""
    
    # CSS 주입: 카카오뱅크 스타일 및 메뉴 하이라이트
    st.markdown("""
    <style>
    /* 1. 기본 네비게이션 제거 */
    [data-testid="stSidebarNav"] {display: none !important;}
    
    /* 2. 사이드바 전체 배경 및 스타일 */
    .stSidebar {
        background-color: #ffffff !important;
        border-right: 1px solid #f0f2f6;
    }
    [data-testid="stSidebarContent"] {
        padding-top: 0 !important;
    }

    /* 3. 섹션 구분선 */
    .sb-divider {
        margin: 10px 20px;
        border-top: 1px solid #f0f2f6;
    }

    /* 4. 섹션 타이틀 */
    .sb-section-title {
        color: #a0aec0;
        font-size: 11px;
        font-weight: 700;
        padding: 15px 25px 5px 25px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* 5. 사용자 프로필 영역 */
    .sb-profile {
        padding: 40px 25px 15px 25px;
        background-color: #ffffff;
    }
    .sb-mode-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        background-color: #fef3c7; /* 카카오 노란색 연한 버전 */
        color: #92400e;
        font-size: 12px;
        font-weight: 700;
        margin-bottom: 8px;
    }
    .sb-user-name {
        font-size: 18px;
        font-weight: 800;
        color: #1a202c;
    }

    /* 6. 페이지 링크 커스텀 (카카오뱅크 스타일) */
    div[data-testid="stSidebar"] a {
        padding: 10px 20px !important;
        margin: 2px 15px !important;
        border-radius: 12px !important;
        color: #4a5568 !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        transition: all 0.2s ease !important;
        border: none !important;
        text-decoration: none !important;
        display: flex !important;
        align-items: center !important;
    }

    /* 호버 효과 */
    div[data-testid="stSidebar"] a:hover {
        background-color: #f7fafc !important;
        color: #1a202c !important;
        transform: translateX(4px);
    }

    /* 현재 페이지 하이라이트 (카카오 노랑) */
    div[data-testid="stSidebar"] a[aria-current="page"] {
        background-color: #ffeb00 !important;
        color: #1a202c !important;
        box-shadow: 0 2px 8px rgba(255, 235, 0, 0.2);
    }

    /* 아이콘 크기 조절 */
    div[data-testid="stSidebar"] a span[data-testid="stWidgetLabel"] {
        font-size: 22px !important;
        margin-right: 10px !important;
    }
    
    /* 로그아웃 버튼 특수 스타일 */
    .logout-btn-container {
        padding: 0 15px;
        margin-top: 10px;
    }
    .stSidebar .stButton > button {
        width: 100% !important;
        background-color: transparent !important;
        color: #a0aec0 !important;
        border: 1px solid #f0f2f6 !important;
        border-radius: 12px !important;
        font-size: 13px !important;
        padding: 6px !important;
        transition: all 0.2s ease !important;
    }
    .stSidebar .stButton > button:hover {
        background-color: #fff5f5 !important;
        color: #e53e3e !important;
        border-color: #feb2b2 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # --- 사이드바 콘텐츠 시작 ---
    with st.sidebar:
        # 1. 사용자 정보 섹션
        st.markdown('<div class="sb-section-title">━━━ 사용자 ━━━</div>', unsafe_allow_html=True)
        user_type_kr = "부모 모드" if user_type == 'parent' else "아이 모드"
        st.markdown(f"""
        <div class="sb-profile">
            <div class="sb-mode-badge">📁 {user_type_kr}</div>
            <div class="sb-user-name">👤 {user_name}님</div>
        </div>
        """, unsafe_allow_html=True)
        
        # 내 정보 버튼 추가
        if st.button("내 정보", key="side_info_top", use_container_width=False):
            st.switch_page("pages/4_👤_내정보.py")
        
        st.markdown('<div class="sb-divider"></div>', unsafe_allow_html=True)

        # 2. 주요 메뉴 섹션
        st.markdown('<div class="sb-section-title">━━━ 메뉴 ━━━</div>', unsafe_allow_html=True)
        
        if user_type == 'parent':
            st.page_link("app.py", label="홈", icon="🏠")
            st.page_link("pages/2_📊_부모_대시보드.py", label="대시보드", icon="📊")
            st.page_link("pages/3_💼_부모_상담실.py", label="부모 상담실", icon="💼")
            st.page_link("pages/9_💵_용돈_관리.py", label="거래 내역", icon="📈")
            st.page_link("pages/5_💰_용돈_추천.py", label="용돈 관리", icon="🔥")
            st.page_link("pages/6_📚_금융_교육_가이드.py", label="목표 가이드", icon="📚")
        else:
            st.page_link("app.py", label="홈", icon="🏠")
            st.page_link("pages/1_💬_아이_채팅.py", label="AI 선생님", icon="💬")
            st.page_link("pages/7_🎯_금융_미션.py", label="오늘의 퀴즈", icon="🎯")
            st.page_link("pages/8_📖_금융_스토리.py", label="금융 스토리", icon="📖")
            st.page_link("pages/9_💵_용돈_관리.py", label="거래 내역", icon="💵")
        
        st.markdown('<div class="sb-divider"></div>', unsafe_allow_html=True)

        # 3. 기타 섹션
        st.markdown('<div class="sb-section-title">━━━ 기타 ━━━</div>', unsafe_allow_html=True)
        
        # 로그아웃 버튼
        st.markdown('<div class="logout-btn-container">', unsafe_allow_html=True)
        if st.button("🚪 로그아웃", key="side_logout"):
            st.session_state.logged_in = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

def hide_sidebar_navigation():
    st.markdown("<style>[data-testid='stSidebarNav'] {display: none !important;}</style>", unsafe_allow_html=True)
