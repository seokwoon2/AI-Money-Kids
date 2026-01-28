import streamlit as st
from datetime import datetime
from database.db_manager import DatabaseManager
from services.analysis_service import AnalysisService
from utils.menu import render_sidebar_menu, hide_sidebar_navigation

st.set_page_config(
    page_title="👤 내정보",
    page_icon="👤",
    layout="wide",
    menu_items=None
)

# Streamlit 기본 네비게이션 숨기기
hide_sidebar_navigation()
st.markdown("""
<style>
[data-testid="stSidebarNav"] {
    display: none !important;
}
nav[data-testid="stSidebarNav"] {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

# 로그인 확인
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("로그인이 필요합니다. 메인 페이지에서 로그인해주세요.")
    st.stop()

user_id = st.session_state.user_id
user_name = st.session_state.user_name

db = DatabaseManager()
analysis_service = AnalysisService()

# 사용자 정보 가져오기
user = db.get_user_by_id(user_id)
if not user:
    st.error("사용자 정보를 찾을 수 없습니다.")
    st.stop()

user_type = user.get('user_type', 'child')
user_age = user.get('age')
parent_code = user.get('parent_code')
created_at = user.get('created_at')

# 페이지 제목
st.title("👤 내정보")
st.markdown("---")

# 기본 정보
col1, col2 = st.columns(2)

with col1:
    st.subheader("📋 기본 정보")
    
    # 트렌디한 정보 카드
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 25px; border-radius: 16px; color: white; margin-bottom: 20px;'>
        <h3 style='color: white; margin-top: 0;'>👤 {user.get('name')}</h3>
        <p style='color: white; opacity: 0.9; margin: 5px 0;'>ID: {user.get('username')}</p>
        <p style='color: white; opacity: 0.8; margin: 5px 0;'>
            {'👨‍👩‍👧 부모 계정' if user_type == 'parent' else '👶 아이 계정'}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # 정보 수정 섹션 - 트렌디한 탭 방식 (3개 탭)
    tab1, tab2, tab3 = st.tabs(["✏️ 이름 변경", "🔐 비밀번호 변경", "🔄 계정 타입 변경"])
    
    with tab1:
        st.markdown("### 이름 변경")
        new_name = st.text_input(
            "새 이름", 
            value=user.get('name'), 
            key="edit_name",
            placeholder="변경할 이름을 입력하세요"
        )
        
        if st.button("💾 이름 저장", type="primary", use_container_width=True, key="save_name"):
            if new_name != user.get('name'):
                if new_name.strip():
                    if db.update_user_info(user_id, name=new_name):
                        st.session_state.user_name = new_name
                        st.success("✅ 이름이 변경되었습니다!")
                        st.rerun()
                    else:
                        st.error("❌ 이름 변경에 실패했습니다.")
                else:
                    st.warning("⚠️ 이름을 입력해주세요.")
            else:
                st.info("ℹ️ 변경할 내용이 없습니다.")
    
    with tab2:
        st.markdown("### 비밀번호 변경")
        current_password = st.text_input(
            "현재 비밀번호", 
            type="password", 
            key="current_password",
            placeholder="현재 비밀번호를 입력하세요"
        )
        new_password = st.text_input(
            "새 비밀번호", 
            type="password", 
            key="new_password",
            placeholder="새 비밀번호를 입력하세요"
        )
        confirm_password = st.text_input(
            "새 비밀번호 확인", 
            type="password", 
            key="confirm_password",
            placeholder="새 비밀번호를 다시 입력하세요"
        )
        
        if st.button("💾 비밀번호 저장", type="primary", use_container_width=True, key="save_password"):
            errors = []
            
            if not new_password:
                st.warning("⚠️ 새 비밀번호를 입력해주세요.")
            elif not current_password:
                errors.append("현재 비밀번호를 입력해주세요.")
            elif not db.verify_password(current_password, user.get('password_hash')):
                errors.append("현재 비밀번호가 일치하지 않습니다.")
            elif new_password != confirm_password:
                errors.append("새 비밀번호가 일치하지 않습니다.")
            elif len(new_password) < 4:
                errors.append("비밀번호는 최소 4자 이상이어야 합니다.")
            else:
                if db.update_user_info(user_id, password=new_password):
                    st.success("✅ 비밀번호가 변경되었습니다!")
                    st.rerun()
                else:
                    errors.append("비밀번호 변경에 실패했습니다.")
            
            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
    
    with tab3:
        st.markdown("### 계정 타입 변경")
        st.info("💡 계정 타입을 잘못 설정하셨나요? 아래에서 수정할 수 있습니다.")
        
        current_type_display = "부모" if user_type == 'parent' else "아이"
        st.markdown(f"**현재 계정 타입**: {current_type_display}")
        
        new_type = st.radio(
            "변경할 계정 타입 선택",
            ["👨‍👩‍👧 부모", "👶 아이"],
            index=0 if user_type == 'parent' else 1,
            key="user_type_selector"
        )
        
        if st.button("🔄 계정 타입 변경", type="primary", use_container_width=True, key="change_user_type"):
            new_type_value = 'parent' if new_type == "👨‍👩‍👧 부모" else 'child'
            if new_type_value != user_type:
                if db.update_user_type(user_id, new_type_value):
                    st.success("✅ 계정 타입이 변경되었습니다!")
                    st.info("💡 변경사항을 적용하려면 로그아웃 후 다시 로그인하거나 페이지를 새로고침하세요.")
                    st.rerun()
                else:
                    st.error("❌ 계정 타입 변경에 실패했습니다.")
            else:
                st.info("ℹ️ 이미 선택한 계정 타입입니다.")
    
    st.markdown("---")
    
    # 추가 정보 표시
    info_items = [
        ("📝 사용자명", user.get('username'), "변경 불가"),
        ("🔑 부모 코드", parent_code, "변경 불가"),
    ]
    
    if user_age:
        info_items.append(("🎂 만나이", f"{user_age}세", "변경 불가"))
    
    if created_at:
        try:
            if isinstance(created_at, str):
                created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            else:
                created_date = datetime.fromisoformat(str(created_at))
            info_items.append(("📅 가입일", created_date.strftime('%Y년 %m월 %d일'), ""))
        except:
            info_items.append(("📅 가입일", str(created_at), ""))
    
    for icon_label, value, note in info_items:
        st.markdown(f"""
        <div style='background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 10px; 
                    border-left: 4px solid #667eea;'>
            <strong>{icon_label}</strong>: {value}
            {f'<span style="color: #6c757d; font-size: 0.9em;">({note})</span>' if note else ''}
        </div>
        """, unsafe_allow_html=True)

with col2:
    st.subheader("📊 활동 통계")
    
    if user_type == 'child':
        # 아이인 경우 금융습관 점수 표시
        scores = analysis_service.get_latest_scores(user_id)
        
        st.metric("충동성 점수", f"{scores['impulsivity']:.1f}", 
                 delta=f"{100 - scores['impulsivity']:.1f}점 낮을수록 좋음", 
                 delta_color="inverse")
        st.metric("저축성향 점수", f"{scores['saving_tendency']:.1f}", 
                 delta=f"{scores['saving_tendency']:.1f}점 높을수록 좋음")
        st.metric("인내심 점수", f"{scores['patience']:.1f}", 
                 delta=f"{scores['patience']:.1f}점 높을수록 좋음")
        
        # 행동 기록 통계
        behaviors = db.get_user_behaviors(user_id, limit=1000)
        if behaviors:
            saving_count = sum(1 for b in behaviors if b['behavior_type'] == 'saving')
            impulse_count = sum(1 for b in behaviors if b['behavior_type'] == 'impulse_buying')
            planned_count = sum(1 for b in behaviors if b['behavior_type'] == 'planned_spending')
            
            st.markdown("---")
            st.subheader("📈 행동 통계")
            st.metric("💰 저축 횟수", saving_count)
            st.metric("⚡ 충동구매", impulse_count)
            st.metric("📝 계획적 소비", planned_count)
    else:
        # 부모인 경우 자녀 통계
        children = db.get_users_by_parent_code(parent_code)
        st.metric("등록된 자녀 수", len(children))
        
        if children:
            st.markdown("---")
            st.subheader("👨‍👩‍👧 자녀 목록")
            for child in children:
                age_info = f" ({child.get('age', '?')}세)" if child.get('age') else ""
                st.caption(f"• {child['name']}{age_info}")

st.markdown("---")

# 대화 통계
st.subheader("💬 대화 통계")

conn = db._get_connection()
cursor = conn.cursor()

conversations_count = cursor.execute(
    "SELECT COUNT(*) as count FROM conversations WHERE user_id = ?", 
    (user_id,)
).fetchone()

messages_count = cursor.execute(
    "SELECT COUNT(*) as count FROM messages WHERE conversation_id IN (SELECT id FROM conversations WHERE user_id = ?)", 
    (user_id,)
).fetchone()

conn.close()

col3, col4 = st.columns(2)
with col3:
    st.metric("총 대화 세션", conversations_count['count'] if conversations_count else 0)
with col4:
    st.metric("총 메시지 수", messages_count['count'] if messages_count else 0)

st.markdown("---")

# 사이드바 메뉴 렌더링
render_sidebar_menu(user_id, user_name, user_type)
