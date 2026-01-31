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
    
    # CSS 주입
    st.markdown("""
    <style>
    /* 기본 네비게이션 제거 */
    [data-testid="stSidebarNav"] {display: none !important;}
    
    /* 사이드바 전체 배경 및 스타일 */
    .stSidebar {
        background-color: #ffffff !important;
        border-right: 1px solid #f0f2f6;
    }
    [data-testid="stSidebarContent"] {
        padding-top: 0 !important;
    }
    
    /* 메뉴 버튼 스타일 */
    .stSidebar .stButton > button {
        width: 100% !important;
        padding: 12px 20px !important;
        border-radius: 12px !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
        text-align: left !important;
        margin-bottom: 5px !important;
    }
    
    .stSidebar .stButton > button[type="primary"] {
        background-color: #FF69B4 !important;
        color: white !important;
        box-shadow: 0 2px 8px rgba(255, 105, 180, 0.3) !important;
    }
    
    .stSidebar .stButton > button[type="secondary"] {
        background-color: transparent !important;
        color: #4a5568 !important;
        border: 1px solid #e0e0e0 !important;
    }
    
    .stSidebar .stButton > button:hover {
        transform: translateX(4px) !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
    }
    
    .stSidebar .stButton > button[type="secondary"]:hover {
        background-color: #f7fafc !important;
        border-color: #FF69B4 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # --- 사이드바 콘텐츠 시작 ---
    with st.sidebar:
        # 로고/제목
        st.markdown("""
            <div style='text-align: center; padding: 20px 0;'>
                <div style='font-size: 60px;'>🐷</div>
                <h2 style='color: #FF69B4; margin: 10px 0; font-size: 24px;'>
                    AI Money Friends
                </h2>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 세션 상태 초기화
        if 'current_page' not in st.session_state:
            st.session_state['current_page'] = 'home'
        
        # 메뉴 항목 (부모/아이에 따라 다름)
        if user_type == 'parent':
            menu_items = [
                ("🏠", "홈", "home"),
                ("👶", "자녀 관리", "children"),
                ("💰", "용돈 관리", "allowance"),
                ("📊", "리포트", "report"),
                ("⚙️", "설정", "settings"),
            ]
        elif user_type == 'child':
            menu_items = [
                ("🏠", "홈", "home"),
                ("💰", "내 용돈", "my_money"),
                ("🎯", "미션", "missions"),
                ("🤖", "AI 친구", "ai_chat"),
                ("📚", "학습", "learning"),
            ]
        else:
            menu_items = [
                ("🏠", "홈", "home"),
            ]
        
        # 메뉴 버튼 렌더링
        current_page = st.session_state.get('current_page', 'home')
        
        for icon, label, key in menu_items:
            is_active = current_page == key
            
            # 페이지 경로 매핑
            page_paths = {
                'home': 'app.py',
                'children': 'pages/2_📊_부모_대시보드.py',
                'allowance': 'pages/9_💵_용돈_관리.py',
                'report': 'pages/3_💼_부모_상담실.py',
                'settings': 'pages/4_👤_내정보.py',
                'my_money': 'pages/9_💵_용돈_관리.py',
                'missions': 'pages/7_🎯_금융_미션.py',
                'ai_chat': 'pages/1_💬_아이_채팅.py',
                'learning': 'pages/8_📖_금융_스토리.py',
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
                elif key == 'home':
                    st.switch_page("app.py")
                st.rerun()
        
        st.markdown("---")
        
        # 로그아웃 버튼
        if st.session_state.get('logged_in'):
            if st.button("🚪 로그아웃", use_container_width=True, type="secondary"):
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
