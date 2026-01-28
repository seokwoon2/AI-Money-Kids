"""공통 메뉴 유틸리티 - 아이 친화적 스타일 A 컨셉"""
import streamlit as st
from database.db_manager import DatabaseManager

def add_to_recent(name, path, icon):
    """최근 접근한 메뉴 추가"""
    if 'recent_menus' not in st.session_state:
        st.session_state.recent_menus = []
    
    # 중복 제거 후 맨 앞에 추가
    menu_item = {"name": name, "path": path, "icon": icon}
    st.session_state.recent_menus = [m for u, m in enumerate([menu_item] + st.session_state.recent_menus) 
                                     if m not in st.session_state.recent_menus[:u]][:5] # 최근 5개만 유지

def toggle_favorite(name, path, icon):
    """즐겨찾기 토글"""
    if 'favorites' not in st.session_state:
        st.session_state.favorites = []
    
    menu_item = {"name": name, "path": path, "icon": icon}
    if menu_item in st.session_state.favorites:
        st.session_state.favorites.remove(menu_item)
    else:
        st.session_state.favorites.append(menu_item)

def render_sidebar_menu(user_id: int, user_name: str, user_type: str):
    """사이드바 메뉴 렌더링 - 파스텔 카드 & 귀여운 마스코트 스타일"""
    
    # 세션 상태 초기화
    if 'favorites' not in st.session_state:
        st.session_state.favorites = []
    if 'recent_menus' not in st.session_state:
        st.session_state.recent_menus = []

    # CSS 주입: 이미지의 디자인 규격 적용
    st.sidebar.markdown("""
    <style>
    /* 기본 네비게이션 제거 */
    [data-testid="stSidebarNav"] {display: none !important;}
    
    /* 사이드바가 닫혀있을 때 나타나는 열기 버튼 커스텀 - 딱 하나만! */
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
        z-index: 999999;
    }
    
    /* 열기 버튼에 '전체메뉴' 텍스트 추가 (정확히 열기 버튼에만) */
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
        padding: 24px 16px !important;
    }

    /* 사이드바 로고/마스코트 영역 */
    .sidebar-mascot {
        text-align: center;
        margin-bottom: 24px;
    }

    /* 메뉴 섹션 타이틀 */
    .menu-section-title {
        font-size: 13px;
        font-weight: 800;
        color: #a0aec0;
        margin: 20px 0 10px 5px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* 커스텀 버튼 디자인 (이미지의 둥근 스타일) */
    .stButton > button {
        width: 100% !important;
        border: none !important;
        padding: 10px 15px !important;
        font-size: 15px !important;
        font-weight: 700 !important;
        border-radius: 20px !important;
        text-align: left !important;
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03) !important;
        transition: all 0.2s ease !important;
        margin-bottom: 4px !important;
    }
    
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 8px rgba(0,0,0,0.08) !important;
    }

    /* 메뉴별 파스텔 색상 적용 - 사이드바 내부 버튼만 */
    .stSidebar .stButton > button[key*="side_"] { background-color: white; color: #4a5568; border: 1px solid #edf2f7 !important; }
    
    /* 활성 메뉴 스타일 */
    .active-menu { background-color: #eef2ff !important; color: #6366f1 !important; border: 1px solid #c7d2fe !important; }

    /* 하단 구분선 */
    .side-divider {
        margin: 15px 0;
        border-top: 1px dashed #ddd;
    }
    </style>
    
    <div class="sidebar-mascot">
        <div style="font-size: 40px;">🐷</div>
        <div style="font-weight: 800; font-size: 16px; color: #444; margin-top: 5px;">AI Money Friends</div>
    </div>
    """, unsafe_allow_html=True)

    # 1. 즐겨찾기 영역
    if st.session_state.favorites:
        st.sidebar.markdown('<div class="menu-section-title">⭐ 즐겨찾기</div>', unsafe_allow_html=True)
        for fav in st.session_state.favorites:
            if st.sidebar.button(f"{fav['icon']} {fav['name']}", key=f"fav_{fav['path']}", use_container_width=True):
                add_to_recent(fav['name'], fav['path'], fav['icon'])
                st.switch_page(fav['path'])

    # 2. 최근 방문 메뉴
    if st.session_state.recent_menus:
        st.sidebar.markdown('<div class="menu-section-title">🕒 최근 방문</div>', unsafe_allow_html=True)
        for recent in st.session_state.recent_menus:
            if st.sidebar.button(f"{recent['icon']} {recent['name']}", key=f"recent_{recent['path']}", use_container_width=True):
                st.switch_page(recent['path'])

    st.sidebar.markdown('<div class="side-divider"></div>', unsafe_allow_html=True)
    st.sidebar.markdown('<div class="menu-section-title">📂 전체 메뉴</div>', unsafe_allow_html=True)

    # 홈으로 가기 (기본 버튼)
    if st.sidebar.button("🏠 홈으로", key="side_home", use_container_width=True):
        st.switch_page("app.py")

    # 서비스 메뉴 정의
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

    # 전체 메뉴 리스트 렌더링
    for icon, name, path in menu_items:
        col_m, col_f = st.sidebar.columns([0.85, 0.15])
        with col_m:
            if st.button(f"{icon} {name}", key=f"side_{path}", use_container_width=True):
                add_to_recent(name, path, icon)
                st.switch_page(path)
        with col_f:
            # 즐겨찾기 별 버튼
            is_fav = any(f['path'] == path for f in st.session_state.favorites)
            star = "⭐" if is_fav else "☆"
            if st.button(star, key=f"star_{path}", help="즐겨찾기 토글"):
                toggle_favorite(name, path, icon)
                st.rerun()

    st.sidebar.markdown('<div class="side-divider"></div>', unsafe_allow_html=True)
    
    # 설정 및 계정
    if st.sidebar.button("👤 내 정보", key="side_info", use_container_width=True):
        add_to_recent("내 정보", "pages/4_👤_내정보.py", "👤")
        st.switch_page("pages/4_👤_내정보.py")
        
    if st.sidebar.button("🚪 로그아웃", key="side_logout", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

def hide_sidebar_navigation():
    st.markdown("<style>[data-testid='stSidebarNav'] {display: none !important;}</style>", unsafe_allow_html=True)
