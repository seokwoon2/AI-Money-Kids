"""공통 메뉴 유틸리티 - 아이 친화적 스타일 A 컨셉"""
import streamlit as st
from database.db_manager import DatabaseManager

def render_sidebar_menu(user_id: int, user_name: str, user_type: str):
    """사이드바 메뉴 렌더링 - 파스텔 카드 & 귀여운 마스코트 스타일"""
    
    # CSS 주입: 이미지의 디자인 규격 적용
    st.sidebar.markdown("""
    <style>
    /* 기본 네비게이션 제거 */
    [data-testid="stSidebarNav"] {display: none !important;}
    
    /* 사이드바 토글 버튼 커스텀 (전체메뉴 명시) */
    [data-testid="stSidebarCollapseIcon"] {
        background-color: #6366f1 !important;
        color: white !important;
        border-radius: 8px !important;
        padding: 5px !important;
        width: 40px !important;
        height: 40px !important;
    }
    
    /* 사이드바가 닫혀있을 때 나타나는 열기 버튼 커스텀 */
    section[data-testid="stSidebar"] + div button {
        background-color: #6366f1 !important;
        color: white !important;
        border-radius: 0 10px 10px 0 !important;
        padding: 10px 15px !important;
        width: auto !important;
        height: auto !important;
        left: 0 !important;
        top: 20px !important;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1) !important;
    }
    
    /* 열기 버튼에 '메뉴' 텍스트 추가 효과 (가상 요소) */
    section[data-testid="stSidebar"] + div button::after {
        content: " 전체메뉴";
        font-size: 14px;
        font-weight: 700;
        margin-left: 5px;
    }
    
    /* 사이드바 배경 및 패딩 */
    .stSidebar {
        background-color: #f9f9fb !important;
        border-right: 1px solid #eee;
    }
    [data-testid="stSidebarContent"] {
        padding: 24px 16px !important; /* 상단 24px 패딩 적용 */
    }

    /* 사이드바 로고/마스코트 영역 */
    .sidebar-mascot {
        text-align: center;
        margin-bottom: 24px;
    }
    .sidebar-mascot img {
        width: 60px;
        height: 60px;
    }

    /* 메뉴 아이템 스타일 (16px 간격) */
    .menu-item-container {
        display: flex;
        flex-direction: column;
        gap: 16px; /* 항목 간격 16px 적용 */
    }

    /* 커스텀 버튼 디자인 (이미지의 둥근 스타일) */
    .stButton > button {
        width: 100% !important;
        border: none !important;
        padding: 12px 20px !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        border-radius: 30px !important; /* 대형 터치 친화적 둥근 버튼 */
        text-align: left !important;
        display: flex !important;
        align-items: center !important;
        gap: 10px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton > button:hover {
        transform: scale(1.03);
        box-shadow: 0 6px 12px rgba(0,0,0,0.1) !important;
    }

    /* 메뉴별 파스텔 색상 적용 */
    /* 내 저축함 (노랑) */
    button[key*="side_pages/9_💵_용돈_관리.py"] { background-color: #FFE5A5 !important; color: #7F6000 !important; }
    /* AI 선생님 (민트) */
    button[key*="side_pages/1_💬_아이_채팅.py"] { background-color: #C1F0D5 !important; color: #1E4D2B !important; }
    /* 오늘의 퀴즈 (코랄) */
    button[key*="side_pages/7_🎯_금융_미션.py"] { background-color: #FFB3B3 !important; color: #661A1A !important; }
    /* 부모 상담실 (라벤더) */
    button[key*="side_pages/3_💼_부모_상담실.py"] { background-color: #D9D1F2 !important; color: #3D2B66 !important; }
    /* 기본 (화이트) */
    .stButton > button[kind="secondary"] { background-color: white !important; color: #444 !important; }

    /* 하단 구분선 */
    .side-divider {
        margin: 20px 0;
        border-top: 1px dashed #ddd;
    }
    </style>
    
    <div class="sidebar-mascot">
        <div style="font-size: 50px;">🐷</div>
        <div style="font-weight: 800; font-size: 18px; color: #444; margin-top: 10px;">AI Money Friends</div>
    </div>
    """, unsafe_allow_html=True)

    # 홈으로 가기 (기본 버튼)
    if st.sidebar.button("🏠 홈으로", key="side_home", use_container_width=True):
        st.switch_page("app.py")

    # 서비스 메뉴
    if user_type == 'parent':
        menu_items = [
            ("💼", "부모 상담실", "pages/3_💼_부모_상담실.py"),
            ("📊", "자녀 대시보드", "pages/2_📊_부모_대시보드.py"),
            ("💰", "용돈 추천기", "pages/5_💰_용돈_추천.py"),
            ("📖", "꿈꾸기 가이드", "pages/6_📚_금융_교육_가이드.py"),
            ("📝", "대화 기록", "pages/10_📝_대화_기록.py")
        ]
    else:
        menu_items = [
            ("💬", "AI 선생님", "pages/1_💬_아이_채팅.py"),
            ("🎯", "오늘의 퀴즈", "pages/7_🎯_금융_미션.py"),
            ("📖", "금융 스토리", "pages/8_📖_금융_스토리.py"),
            ("💵", "거래 내역", "pages/9_💵_용돈_관리.py"),
            ("📝", "대화 기록", "pages/10_📝_대화_기록.py")
        ]

    for icon, name, path in menu_items:
        if st.sidebar.button(f"{icon} {name}", key=f"side_{path}", use_container_width=True):
            st.switch_page(path)

    st.sidebar.markdown('<div class="side-divider"></div>', unsafe_allow_html=True)
    
    # 설정 및 계정
    if st.sidebar.button("👤 내 정보", key="side_info", use_container_width=True):
        st.switch_page("pages/4_👤_내정보.py")
        
    if st.sidebar.button("🚪 로그아웃", key="side_logout", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

def hide_sidebar_navigation():
    st.markdown("<style>[data-testid='stSidebarNav'] {display: none !important;}</style>", unsafe_allow_html=True)
