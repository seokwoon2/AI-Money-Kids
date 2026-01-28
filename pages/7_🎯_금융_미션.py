import streamlit as st
from datetime import datetime, timedelta
from database.db_manager import DatabaseManager
from utils.menu import render_sidebar_menu, hide_sidebar_navigation

st.set_page_config(
    page_title="🎯 금융 미션",
    page_icon="🎯",
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
user = db.get_user_by_id(user_id)
user_type = user.get('user_type', 'child') if user else 'child'
user_age = user.get('age', 10) if user else 10

# 아이 전용 페이지 확인
if user_type != 'child':
    st.warning("이 페이지는 아이 전용입니다.")
    st.stop()

# 사이드바 메뉴 렌더링
render_sidebar_menu(user_id, user_name, user_type)

# 페이지 제목
st.title(f"🎯 {user_name}님의 금융 미션")
st.markdown("---")

# 미션 데이터 (세션 상태로 관리)
if 'missions' not in st.session_state:
    st.session_state.missions = []

# 사용자의 행동 기록 확인
behaviors = db.get_user_behaviors(user_id, limit=100)

# 미션 목록
missions = [
    {
        "id": 1,
        "title": "💰 저축 습관 만들기",
        "description": "이번 주에 3번 이상 저축 행동을 기록해보세요!",
        "target": "saving",
        "count": 3,
        "reward": "저축 습관 배지 획득",
        "difficulty": "쉬움"
    },
    {
        "id": 2,
        "title": "📝 계획적 소비하기",
        "description": "계획한 후에 구매하는 습관을 5번 실천해보세요!",
        "target": "planned_spending",
        "count": 5,
        "reward": "계획왕 배지 획득",
        "difficulty": "보통"
    },
    {
        "id": 3,
        "title": "⏰ 인내심 기르기",
        "description": "사고 싶은 것을 참고 기다린 경험을 3번 기록해보세요!",
        "target": "delayed_gratification",
        "count": 3,
        "reward": "인내왕 배지 획득",
        "difficulty": "보통"
    },
    {
        "id": 4,
        "title": "🔍 가격 비교하기",
        "description": "물건을 살 때 가격을 비교한 경험을 3번 기록해보세요!",
        "target": "comparing_prices",
        "count": 3,
        "reward": "현명한 소비자 배지 획득",
        "difficulty": "쉬움"
    }
]

# 진행 중인 미션 표시
st.subheader("🚀 진행 중인 미션")

if behaviors:
    for mission in missions:
        mission_count = sum(1 for b in behaviors if b['behavior_type'] == mission['target'])
        progress = min(mission_count / mission['count'] * 100, 100)
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"### {mission['title']}")
            st.markdown(f"**목표**: {mission['description']}")
            st.progress(progress / 100)
            st.caption(f"진행률: {mission_count}/{mission['count']} ({progress:.0f}%)")
        
        with col2:
            if progress >= 100:
                st.success("✅ 완료!")
                st.balloons()
            else:
                st.info(f"🎁 보상: {mission['reward']}")
        
        st.markdown("---")
else:
    st.info("아직 기록된 행동이 없습니다. 금융 활동을 시작해보세요!")

# 새로운 미션 제안
st.subheader("💡 오늘의 미션 추천")

recommended_mission = missions[0]  # 간단하게 첫 번째 미션 추천
st.markdown(f"""
<div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            padding: 20px; border-radius: 12px; color: white; margin: 20px 0;'>
    <h3 style='color: white; margin-top: 0;'>{recommended_mission['title']}</h3>
    <p style='color: white; opacity: 0.9;'>{recommended_mission['description']}</p>
    <p style='color: white; opacity: 0.8;'>난이도: {recommended_mission['difficulty']} | 보상: {recommended_mission['reward']}</p>
</div>
""", unsafe_allow_html=True)

if st.button("🎯 이 미션 시작하기", type="primary", use_container_width=True):
    st.success("미션이 시작되었습니다! 금융 활동을 기록하면 자동으로 진행됩니다.")
    st.info("💡 팁: '아이 채팅'에서 금융 활동을 대화로 기록할 수 있어요!")

# 사이드바 추가 정보
with st.sidebar:
    st.markdown("---")
    st.markdown("### 💡 미션 안내")
    st.info("""
    금융 미션을 완료하면 배지를 받을 수 있어요!
    
    **미션 완료 방법:**
    1. 금융 활동을 실천하기
    2. '아이 채팅'에서 활동 기록하기
    3. 미션이 자동으로 진행돼요!
    """)
