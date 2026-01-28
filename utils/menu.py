"""공통 메뉴 유틸리티 - 토스 스타일 UI 개편 (최종 수정본)"""
import streamlit as st
from database.db_manager import DatabaseManager

def add_to_recent(name, path, icon):
    """최근 접근한 메뉴 추가 (세션 상태에 저장)"""
    if 'recent_menus' not in st.session_state:
        st.session_state.recent_menus = []
    
    menu_item = {"name": name, "path": path, "icon": icon}
    # 기존 목록에서 중복 제거 후 맨 앞에 추가
    filtered_menus = [m for m in st.session_state.recent_menus if m['path'] != path]
    st.session_state.recent_menus = ([menu_item] + filtered_menus)[:5]

def toggle_favorite(name, path, icon):
    """즐겨찾기 토글"""
    if 'favorites' not in st.session_state:
        st.session_state.favorites = []
    
    menu_item = {"name": name, "path": path, "icon": icon}
    if any(f['path'] == path for f in st.session_state.favorites):
        st.session_state.favorites = [f for f in st.session_state.favorites if f['path'] != path]
    else:
        st.session_state.favorites.append(menu_item)

def render_sidebar_menu(user_id: int, user_name: str, user_type: str):
    """사이드바 메뉴 렌더링 - 토스 스타일 및 헤더 버튼 오류 해결"""
    
    # 세션 상태 초기화
    if 'favorites' not in st.session_state:
        st.session_state.favorites = []
    if 'recent_menus' not in st.session_state:
        st.session_state.recent_menus = []

    # CSS 주입: 오직 헤더의 첫 번째 버튼(메뉴)에만 '전체메뉴' 텍스트 추가
    st.markdown("""
    <style>
    /* 1. 기본 네비게이션 제거 */
    [data-testid="stSidebarNav"] {display: none !important;}
    
    /* 2. 상단 헤더 '전체메뉴' 버튼 딱 하나만 적용 */
    /* Streamlit의 사이드바 버튼을 정확히 타겟팅 */
    header[data-testid="stHeader"] button[title="Open sidebar"]::after {
        content: " 전체메뉴" !important;
        font-size: 14px !important;
        font-weight: 700 !important;
        margin-left: 5px !important;
    }
    header[data-testid="stHeader"] button[title="Open sidebar"] {
        background-color: #6366f1 !important;
        color: white !important;
        border-radius: 8px !important;
        padding: 0 12px !important;
        width: auto !important;
        height: 35px !important;
        margin-left: 10px !important;
        display: flex !important;
        align-items: center !important;
    }
    
    /* 다른 헤더 버튼(Share, Star 등)에는 글자가 붙지 않도록 초기화 */
    header[data-testid="stHeader"] button:not([title="Open sidebar"])::after {
        content: "" !important;
    }

    /* 3. 사이드바 스타일 (토스 리스트 스타일) */
    .stSidebar {
        background-color: #ffffff !important;
        border-right: 1px solid #f0f2f6;
    }
    [data-testid="stSidebarContent"] {
        padding-top: 0 !important;
    }

    /* 사이드바 헤더 (사용자 정보) */
    .sb-header {
        padding: 40px 20px 20px 20px;
        background-color: #f8faff;
        border-bottom: 1px solid #edf2f7;
        margin-bottom: 10px;
    }
    .sb-badge {
        background-color: #eef2ff;
        color: #6366f1;
        padding: 4px 10px;
        border-radius: 8px;
        font-size: 12px;
        font-weight: 700;
        display: inline-block;
        margin-bottom: 8px;
    }
    .sb-name {
        color: #1a202c;
        font-size: 19px;
        font-weight: 700;
    }

    /* 섹션 타이틀 */
    .sb-group-title {
        color: #a0aec0;
        font-size: 12px;
        font-weight: 700;
        padding: 25px 20px 8px 20px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* 토스 스타일 리스트 메뉴 버튼 */
    .stSidebar .stButton > button {
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
    
    .stSidebar .stButton > button:hover {
        background-color: #f7fafc !important;
        color: #6366f1 !important;
        transform: translateX(4px);
    }

    /* 아이콘과 텍스트 정렬 */
    .stSidebar .stButton > button div[data-testid="stMarkdownContainer"] p {
        margin: 0 !important;
        display: flex !important;
        align-items: center !important;
        gap: 12px !important;
    }

    /* 즐겨찾기 별 버튼 특수 스타일 */
    div.star-col .stButton > button {
        padding: 10px 5px !important;
        justify-content: center !important;
    }
    
    .sb-divider {
        margin: 15px 20px;
        border-top: 1px solid #f0f2f6;
    }
    </style>
    """, unsafe_allow_html=True)

    # 사이드바 프로필
    user_type_kr = "부모님 모드" if user_type == 'parent' else "어린이 모드"
    st.sidebar.markdown(f"""
    <div class="sb-header">
        <div class="sb-badge">{user_type_kr}</div>
        <div class="sb-name">{"👨‍👩‍👧" if user_type == 'parent' else "🐣"} {user_name}님</div>
    </div>
    """, unsafe_allow_html=True)

    # 1. ⭐ 즐겨찾기
    if st.session_state.favorites:
        st.sidebar.markdown('<div class="sb-group-title">⭐ 즐겨찾기</div>', unsafe_allow_html=True)
        for fav in st.session_state.favorites:
            if st.sidebar.button(f"{fav['icon']} {fav['name']}", key=f"fav_{fav['path']}"):
                add_to_recent(fav['name'], fav['path'], fav['icon'])
                st.switch_page(fav['path'])

    # 2. 🕒 최근 방문
    if st.session_state.recent_menus:
        st.sidebar.markdown('<div class="sb-group-title">🕒 최근 방문</div>', unsafe_allow_html=True)
        for recent in st.session_state.recent_menus:
            if st.sidebar.button(f"{recent['icon']} {recent['name']}", key=f"recent_{recent['path']}"):
                st.switch_page(recent['path'])

    st.sidebar.markdown('<div class="sb-divider"></div>', unsafe_allow_html=True)
    st.sidebar.markdown('<div class="sb-group-title">📂 전체 메뉴</div>', unsafe_allow_html=True)

    # 전체 메뉴 리스트 정의
    if user_type == 'parent':
        menu_items = [
            ("🏠", "홈으로 가기", "app.py"),
            ("💼", "부모 상담실", "pages/3_💼_부모_상담실.py"),
            ("📊", "자녀 대시보드", "pages/2_📊_부모_대시보드.py"),
            ("💰", "용돈 추천기", "pages/5_💰_용돈_추천.py"),
            ("📖", "꿈꾸기 가이드", "pages/6_📚_금융_교육_가이드.py"),
            ("📝", "대화 기록", "pages/10_📝_대화_기록.py")
        ]
    else:
        menu_items = [
            ("🏠", "홈으로 가기", "app.py"),
            ("💬", "AI 선생님", "pages/1_💬_아이_채팅.py"),
            ("🎯", "오늘의 퀴즈", "pages/7_🎯_금융_미션.py"),
            ("📖", "금융 스토리", "pages/8_📖_금융_스토리.py"),
            ("💵", "거래 내역", "pages/9_💵_용돈_관리.py"),
            ("📝", "대화 기록", "pages/10_📝_대화_기록.py")
        ]

    # 전체 메뉴 렌더링 (즐겨찾기 버튼 포함)
    for icon, name, path in menu_items:
        col_m, col_s = st.sidebar.columns([0.8, 0.2])
        with col_m:
            if st.button(f"{icon} {name}", key=f"side_{path}"):
                if path != "app.py":
                    add_to_recent(name, path, icon)
                st.switch_page(path)
        with col_s:
            if path != "app.py":
                st.markdown('<div class="star-col">', unsafe_allow_html=True)
                is_fav = any(f['path'] == path for f in st.session_state.favorites)
                if st.button("⭐" if is_fav else "☆", key=f"star_{path}"):
                    toggle_favorite(name, path, icon)
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

    st.sidebar.markdown('<div class="sb-divider"></div>', unsafe_allow_html=True)
    
    if st.sidebar.button("👤 내 정보 수정", key="side_info"):
        add_to_recent("내 정보 수정", "pages/4_👤_내정보.py", "👤")
        st.switch_page("pages/4_👤_내정보.py")
        
    if st.sidebar.button("🚪 로그아웃", key="side_logout"):
        st.session_state.logged_in = False
        st.rerun()

def hide_sidebar_navigation():
    st.markdown("<style>[data-testid='stSidebarNav'] {display: none !important;}</style>", unsafe_allow_html=True)
