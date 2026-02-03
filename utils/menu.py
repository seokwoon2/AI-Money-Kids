"""공통 메뉴 유틸리티 - 카카오뱅크 스타일 UI 개편"""
import streamlit as st
import os
from database.db_manager import DatabaseManager

def safe_page_link(page_path: str, label: str, icon: str = None):
    """안전하게 페이지 링크를 생성하는 헬퍼 함수"""
    try:
        # 파일 존재 여부 확인
        if os.path.exists(page_path):
            st.page_link(page_path, label=label, icon=icon)
    except Exception:
        # 페이지가 없거나 오류가 발생하면 무시
        pass

def render_sidebar_menu(user_id: int, user_name: str, user_type: str):
    """개선된 사이드바 메뉴"""
    # 전역 레이아웃 모드: auto(기기폭) / mobile(강제) / pc(강제)
    if "layout_mode" not in st.session_state:
        st.session_state["layout_mode"] = "auto"
    layout_mode = st.session_state.get("layout_mode", "auto")
    
    # CSS 주입
    # 공통 반응형 CSS: auto는 미디어쿼리로, mobile/pc는 강제로 override
    responsive_css = """
    /* ====== Responsive (global) ====== */
    /* auto: 작은 화면에서 컬럼 래핑 + 터치 타겟/타이포 조정 */
    @media (max-width: 768px){
        .block-container{
            padding-top: 0.6rem !important;
            padding-left: 0.9rem !important;
            padding-right: 0.9rem !important;
        }
        /* st.columns() 래핑: 모바일에서 2열/1열로 자연스럽게 줄바꿈 */
        div[data-testid="stHorizontalBlock"]{
            flex-wrap: wrap !important;
            gap: 0.75rem !important;
        }
        div[data-testid="stHorizontalBlock"] > div{
            flex: 1 1 calc(50% - 0.5rem) !important;
            min-width: calc(50% - 0.5rem) !important;
        }
        /* 아주 작은 기기에서는 1열 */
        @media (max-width: 420px){
            div[data-testid="stHorizontalBlock"] > div{
                flex: 1 1 100% !important;
                min-width: 100% !important;
            }
        }
        /* 버튼/입력 조금 더 촘촘하게 */
        .stButton > button{
            padding: 10px 12px !important;
            border-radius: 14px !important;
            font-weight: 900 !important;
        }
        [data-testid="stMetricValue"]{ font-size: 22px !important; }
    }
    """

    # 강제 모바일: 화면이 넓어도 모바일 스타일 적용
    if layout_mode == "mobile":
        responsive_css += """
        /* ====== Force Mobile ====== */
        .block-container{
            padding-top: 0.6rem !important;
            padding-left: 0.9rem !important;
            padding-right: 0.9rem !important;
            max-width: 740px !important;
        }
        div[data-testid="stHorizontalBlock"]{
            flex-wrap: wrap !important;
            gap: 0.75rem !important;
        }
        div[data-testid="stHorizontalBlock"] > div{
            flex: 1 1 calc(50% - 0.5rem) !important;
            min-width: calc(50% - 0.5rem) !important;
        }
        @media (max-width: 99999px){
            /* 강제 모바일: 매우 작은 화면처럼 1열을 더 쉽게 */
            div[data-testid="stHorizontalBlock"] > div{
                flex: 1 1 100% !important;
                min-width: 100% !important;
            }
        }
        """

    # 강제 PC: 모바일 폭에서도 래핑을 막고 PC처럼 유지(원하면 가로 스크롤이 생길 수 있음)
    if layout_mode == "pc":
        responsive_css += """
        /* ====== Force PC ====== */
        @media (max-width: 768px){
            .block-container{
                padding-left: 1.5rem !important;
                padding-right: 1.5rem !important;
            }
            div[data-testid="stHorizontalBlock"]{
                flex-wrap: nowrap !important;
                gap: 1rem !important;
            }
            div[data-testid="stHorizontalBlock"] > div{
                flex: 1 1 0 !important;
                min-width: 0 !important;
            }
        }
        """

    st.markdown(f"""
    <style>
    /* 기본 네비게이션 제거 */
    [data-testid="stSidebarNav"] {display: none !important;}

    /* 사이드바 접힘(»») 컨트롤을 '메뉴'처럼 보이게 */
    button[data-testid="collapsedControl"],
    button[aria-label="Open sidebar"],
    button[title="Open sidebar"],
    button[aria-label="Expand sidebar"],
    button[title="Expand sidebar"] {
        background: rgba(255,255,255,0.92) !important;
        border: 1px solid rgba(17,24,39,0.08) !important;
        border-radius: 999px !important;
        padding: 8px 12px !important;
        box-shadow: 0 10px 24px rgba(0,0,0,0.12) !important;
        backdrop-filter: blur(8px);
        width: auto !important;
        height: auto !important;
        margin: 8px !important;
        gap: 8px !important;
    }
    /* 아이콘은 유지하고 '메뉴' 라벨만 추가 (DOM 차이에도 안전) */
    button[data-testid="collapsedControl"]::after,
    button[aria-label="Open sidebar"]::after,
    button[title="Open sidebar"]::after,
    button[aria-label="Expand sidebar"]::after,
    button[title="Expand sidebar"]::after {
        content: " 메뉴";
        font-weight: 800;
        color: #111827;
        letter-spacing: -0.2px;
    }
    /* 사이드바 펼친 상태의 접기 버튼도 통일감 */
    button[data-testid="stSidebarCollapseButton"] {
        border-radius: 10px !important;
    }
    
    /* 사이드바 전체 배경 및 스타일 */
    section[data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #f0f2f6;
    }
    [data-testid="stSidebarContent"] {
        padding-top: 0 !important;
        padding-left: 14px !important;
        padding-right: 14px !important;
    }

    /* 프로필 카드 */
    .amf-profile {
        background: linear-gradient(135deg, rgba(102,126,234,0.10), rgba(118,75,162,0.10));
        border: 1px solid rgba(102,126,234,0.18);
        border-radius: 16px;
        padding: 14px 14px;
        margin: 6px 0 12px 0;
    }
    .amf-profile-name {
        font-size: 15px;
        font-weight: 800;
        color: #111827;
        line-height: 1.2;
    }
    .amf-profile-badge {
        display: inline-block;
        margin-top: 6px;
        font-size: 12px;
        font-weight: 800;
        padding: 4px 10px;
        border-radius: 999px;
        background: rgba(255,255,255,0.9);
        border: 1px solid rgba(17,24,39,0.08);
        color: #374151;
    }
    .amf-section-title {
        margin: 14px 4px 8px 4px;
        font-size: 12px;
        font-weight: 900;
        color: #6b7280;
        letter-spacing: 0.2px;
        text-transform: uppercase;
    }
    
    /* 메뉴 버튼 스타일 */
    .stSidebar .stButton > button {
        width: 100% !important;
        padding: 12px 20px !important;
        border-radius: 12px !important;
        font-size: 14px !important;
        font-weight: 800 !important;
        transition: all 0.2s ease !important;
        text-align: left !important;
        margin-bottom: 5px !important;
    }
    
    /* 활성 메뉴: 보라색 */
    .stSidebar .stButton > button[type="primary"] {
        background-color: #6C5CE7 !important;
        color: white !important;
        box-shadow: 0 2px 8px rgba(108, 92, 231, 0.3) !important;
        border: none !important;
    }
    
    /* 비활성 메뉴: 라이트 */
    .stSidebar .stButton > button[type="secondary"] {
        background-color: transparent !important;
        color: #374151 !important;
        border: 1px solid #DFE6E9 !important;
    }
    
    /* 호버 효과 */
    .stSidebar .stButton > button:hover {
        transform: translateX(4px) !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
    }
    
    .stSidebar .stButton > button[type="secondary"]:hover {
        background-color: #F1F3F5 !important;
        border-color: #6C5CE7 !important;
        color: #636E72 !important;
    }
    
    /* 로그아웃 버튼 */
    button[key*="menu_logout"],
    button[key*="로그아웃"] {
        background-color: #FF7675 !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 2px 8px rgba(255, 118, 117, 0.3) !important;
    }
    
    button[key*="menu_logout"]:hover,
    button[key*="로그아웃"]:hover {
        background-color: #FF6B6B !important;
        box-shadow: 0 4px 12px rgba(255, 118, 117, 0.4) !important;
    }

    /* 레이아웃 모드 토글 */
    .amf-toggle-title{
        margin: 10px 4px 6px 4px;
        font-size: 12px;
        font-weight: 900;
        color: #6b7280;
        letter-spacing: 0.2px;
        text-transform: uppercase;
    }
    </style>
    {responsive_css}
    """, unsafe_allow_html=True)

    # --- 사이드바 콘텐츠 시작 ---
    with st.sidebar:
        # 로고/제목
        st.markdown("""
            <div style='text-align: center; padding: 20px 0;'>
                <div style='font-size: 60px;'>🐷</div>
                <h2 style='color: #111827; margin: 10px 0 0 0; font-size: 20px; font-weight: 900; letter-spacing:-0.3px;'>
                    AI Money Friends
                </h2>
                <div style='color:#6b7280; font-size:12px; font-weight:700; margin-top:4px;'>Menu</div>
            </div>
        """, unsafe_allow_html=True)

        # 프로필
        role_kr = "부모님" if user_type == "parent" else ("아이" if user_type == "child" else "사용자")
        st.markdown(
            f"""
            <div class="amf-profile">
                <div class="amf-profile-name">안녕하세요, {user_name}님</div>
                <div class="amf-profile-badge">{role_kr} 계정</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 레이아웃 모드(자동/모바일/PC)
        st.markdown('<div class="amf-toggle-title">View</div>', unsafe_allow_html=True)
        selected = st.radio(
            "화면 모드",
            options=["자동", "모바일", "PC"],
            index={"auto": 0, "mobile": 1, "pc": 2}.get(layout_mode, 0),
            horizontal=True,
            label_visibility="collapsed",
            key="amf_layout_mode_radio",
        )
        new_mode = {"자동": "auto", "모바일": "mobile", "PC": "pc"}[selected]
        if new_mode != st.session_state.get("layout_mode", "auto"):
            st.session_state["layout_mode"] = new_mode
            st.rerun()
        
        # 세션 상태 초기화
        if 'current_page' not in st.session_state:
            st.session_state['current_page'] = 'home'
        
        # 메뉴 항목 (요청한 구조로 교체)
        if user_type == "parent":
            menu_items = [
                ("🏠", "대시보드", "parent_dashboard"),
                ("👶", "자녀 관리", "parent_children"),
                ("💵", "용돈 관리", "allowance_manage"),
                ("📝", "요청 승인", "request_approve"),
                ("📊", "리포트", "parent_report"),
                ("⚙️", "설정", "settings"),
            ]
        else:  # child
            menu_items = [
                ("🏠", "홈", "child_dashboard"),
                ("💰", "내 지갑", "wallet"),
                ("🎯", "저축 목표", "goals"),
                ("📝", "용돈 요청", "allowance_request"),
                ("✅", "미션", "missions"),
                ("🤖", "AI 친구", "ai_friend"),
                ("📚", "경제 교실", "classroom"),
                ("🏆", "내 성장", "growth"),
                ("⚙️", "설정", "settings"),
            ]
        
        # 메뉴 버튼 렌더링
        current_page = st.session_state.get('current_page', 'home')

        st.markdown('<div class="amf-section-title">Main</div>', unsafe_allow_html=True)
        
        for icon, label, key in menu_items:
            is_active = current_page == key

            # 페이지 경로 매핑 (새 구조)
            page_paths = {
                # parent
                "parent_dashboard": "pages/1_🏠_대시보드.py",
                "parent_children": "pages/2_👶_자녀_관리.py",
                "allowance_manage": "pages/3_💵_용돈_관리.py",
                "request_approve": "pages/4_📝_요청_승인.py",
                "parent_report": "pages/5_📊_리포트.py",
                # child
                "child_dashboard": "pages/1_🏠_대시보드.py",
                "wallet": "pages/7_💰_내_지갑.py",
                "goals": "pages/8_🎯_저축_목표.py",
                "allowance_request": "pages/9_📝_용돈_요청.py",
                "missions": "pages/10_✅_미션.py",
                "ai_friend": "pages/11_🤖_AI_친구.py",
                "classroom": "pages/12_📚_경제_교실.py",
                "growth": "pages/13_🏆_내_성장.py",
                # shared
                "settings": "pages/6_⚙️_설정.py",
            }
            
            page_path = page_paths.get(key)
            
            if st.button(
                f"{icon} {label}",
                key=f"menu_{key}",
                use_container_width=True,
                type="primary" if is_active else "secondary"
            ):
                st.session_state['current_page'] = key
                if page_path and os.path.exists(page_path):
                    st.switch_page(page_path)
                else:
                    st.info("페이지가 준비 중입니다.")
                st.rerun()

        st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)
        
        # 로그아웃 버튼
        if st.session_state.get('logged_in'):
            st.markdown('<div class="amf-section-title">Account</div>', unsafe_allow_html=True)
            if st.button("🚪 로그아웃", use_container_width=True, key="menu_logout", type="secondary"):
                # 카카오 로그아웃 처리
                if hasattr(st.session_state, 'access_token') and st.session_state.access_token:
                    try:
                        from services.oauth_service import OAuthService
                        oauth_service = OAuthService()
                        oauth_service.kakao_logout(st.session_state.access_token)
                    except Exception:
                        pass  # 카카오 로그아웃 실패해도 계속 진행
                
                # 세션 상태 초기화
                for key in list(st.session_state.keys()):
                    if key not in ['current_auth_screen']:  # 인증 화면 상태는 유지
                        del st.session_state[key]
                
                st.session_state.logged_in = False
                st.session_state.current_auth_screen = 'login'
                
                # 메인 페이지로 이동
                st.switch_page("app.py")

def hide_sidebar_navigation():
    st.markdown("<style>[data-testid='stSidebarNav'] {display: none !important;}</style>", unsafe_allow_html=True)
