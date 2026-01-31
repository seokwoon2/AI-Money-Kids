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
                <h2 style='color: #FF69B4; margin: 10px 0;'>AI Money Friends</h2>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 메뉴 항목
        menu_items = []
        
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
        
        # 메뉴 버튼 렌더링
        current_page = st.session_state.get('current_page', 'home')
        
        # 부모 메뉴
        if user_type == 'parent':
            if st.button("🏠 홈", key="menu_home", use_container_width=True, 
                        type="primary" if current_page == 'home' else "secondary"):
                st.session_state['current_page'] = 'home'
                st.switch_page("app.py")
            
            if os.path.exists("pages/2_📊_부모_대시보드.py"):
                if st.button("👶 자녀 관리", key="menu_children", use_container_width=True,
                            type="primary" if current_page == 'children' else "secondary"):
                    st.session_state['current_page'] = 'children'
                    st.switch_page("pages/2_📊_부모_대시보드.py")
            
            if os.path.exists("pages/9_💵_용돈_관리.py"):
                if st.button("💰 용돈 관리", key="menu_allowance", use_container_width=True,
                            type="primary" if current_page == 'allowance' else "secondary"):
                    st.session_state['current_page'] = 'allowance'
                    st.switch_page("pages/9_💵_용돈_관리.py")
            
            if os.path.exists("pages/3_💼_부모_상담실.py"):
                if st.button("📊 리포트", key="menu_report", use_container_width=True,
                            type="primary" if current_page == 'report' else "secondary"):
                    st.session_state['current_page'] = 'report'
                    st.switch_page("pages/3_💼_부모_상담실.py")
            
            if os.path.exists("pages/4_👤_내정보.py"):
                if st.button("⚙️ 설정", key="menu_settings", use_container_width=True,
                            type="primary" if current_page == 'settings' else "secondary"):
                    st.session_state['current_page'] = 'settings'
                    st.switch_page("pages/4_👤_내정보.py")
        
        # 아이 메뉴
        elif user_type == 'child':
            if st.button("🏠 홈", key="menu_home", use_container_width=True,
                        type="primary" if current_page == 'home' else "secondary"):
                st.session_state['current_page'] = 'home'
                st.switch_page("app.py")
            
            if os.path.exists("pages/9_💵_용돈_관리.py"):
                if st.button("💰 내 용돈", key="menu_my_money", use_container_width=True,
                            type="primary" if current_page == 'my_money' else "secondary"):
                    st.session_state['current_page'] = 'my_money'
                    st.switch_page("pages/9_💵_용돈_관리.py")
            
            if os.path.exists("pages/7_🎯_금융_미션.py"):
                if st.button("🎯 미션", key="menu_missions", use_container_width=True,
                            type="primary" if current_page == 'missions' else "secondary"):
                    st.session_state['current_page'] = 'missions'
                    st.switch_page("pages/7_🎯_금융_미션.py")
            
            if os.path.exists("pages/1_💬_아이_채팅.py"):
                if st.button("🤖 AI 친구", key="menu_ai_chat", use_container_width=True,
                            type="primary" if current_page == 'ai_chat' else "secondary"):
                    st.session_state['current_page'] = 'ai_chat'
                    st.switch_page("pages/1_💬_아이_채팅.py")
            
            if os.path.exists("pages/8_📖_금융_스토리.py"):
                if st.button("📚 학습", key="menu_learning", use_container_width=True,
                            type="primary" if current_page == 'learning' else "secondary"):
                    st.session_state['current_page'] = 'learning'
                    st.switch_page("pages/8_📖_금융_스토리.py")
        
        st.markdown("---")
        
        # 로그아웃 버튼
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
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.user_name = None
            st.session_state.user_info = None
            st.session_state.access_token = None
            
            # 메인 페이지로 이동
            st.switch_page("app.py")

def hide_sidebar_navigation():
    st.markdown("<style>[data-testid='stSidebarNav'] {display: none !important;}</style>", unsafe_allow_html=True)
