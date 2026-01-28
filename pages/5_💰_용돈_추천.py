import streamlit as st
from database.db_manager import DatabaseManager
from services.gemini_service import GeminiService
from utils.menu import render_sidebar_menu, hide_sidebar_navigation

st.set_page_config(
    page_title="💰 용돈 추천",
    page_icon="💰",
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
gemini_service = GeminiService()

# 사용자 정보 가져오기
user = db.get_user_by_id(user_id)
user_type = user.get('user_type', 'child') if user else 'child'

# 사이드바 메뉴 렌더링 (가장 먼저 실행하여 메뉴 유실 방지)
render_sidebar_menu(user_id, user_name, user_type)

# 부모 전용 페이지 확인
if user_type != 'parent':
    st.warning("이 페이지는 부모 전용입니다.")
    st.stop()

parent_code = user.get('parent_code')
children = db.get_users_by_parent_code(parent_code)

if not children:
    st.info("아직 등록된 자녀가 없습니다. 자녀가 회원가입하면 용돈 추천을 받을 수 있습니다.")
    st.stop()

# 페이지 제목
st.title("💰 용돈 추천 시스템")
st.markdown("---")

# 자녀 선택
child_names = [f"{child['name']} ({child.get('age', '?')}세)" for child in children]
selected_index = st.selectbox("자녀 선택", range(len(children)), format_func=lambda i: child_names[i])
selected_child = children[selected_index]
child_id = selected_child['id']
child_age = selected_child.get('age', 0)

# 자녀의 금융 행동 데이터 가져오기
from services.analysis_service import AnalysisService
analysis_service = AnalysisService()
scores = analysis_service.get_latest_scores(child_id)
behaviors = db.get_user_behaviors(child_id, limit=100)

# 용돈 추천 요청
if st.button("🤖 AI 용돈 추천 받기", type="primary", use_container_width=True):
    with st.spinner("자녀의 금융 습관을 분석하여 용돈을 추천하고 있습니다..."):
        # 자녀 정보 요약
        behavior_summary = []
        if behaviors:
            saving_count = sum(1 for b in behaviors if b['behavior_type'] == 'saving')
            impulse_count = sum(1 for b in behaviors if b['behavior_type'] == 'impulse_buying')
            planned_count = sum(1 for b in behaviors if b['behavior_type'] == 'planned_spending')
            behavior_summary.append(f"저축 횟수: {saving_count}회")
            behavior_summary.append(f"충동구매: {impulse_count}회")
            behavior_summary.append(f"계획적 소비: {planned_count}회")
        
        prompt = f"""다음 정보를 바탕으로 {selected_child['name']}님({child_age}세)에게 적합한 용돈 지급 방식을 추천해주세요.

**금융 습관 점수:**
- 충동성: {scores['impulsivity']:.1f}/100 (낮을수록 좋음)
- 저축성향: {scores['saving_tendency']:.1f}/100 (높을수록 좋음)
- 인내심: {scores['patience']:.1f}/100 (높을수록 좋음)

**행동 기록:**
{chr(10).join(behavior_summary) if behavior_summary else '아직 기록이 없습니다.'}

다음 항목을 포함하여 추천해주세요:
1. 주간/월간 용돈 금액 추천
2. 용돈 지급 방식 (고정/성과 기반/혼합)
3. 저축 목표 설정 제안
4. 용돈 사용 가이드라인

한국어로 친절하고 구체적으로 답변해주세요."""

        try:
            recommendation = gemini_service.chat_with_context(prompt, user_type='parent', user_age=None)
            
            st.markdown("### 💡 AI 추천 결과")
            st.markdown("---")
            st.markdown(recommendation)
            
            st.success("✅ 용돈 추천이 완료되었습니다!")
        except Exception as e:
            st.error(f"용돈 추천 중 오류가 발생했습니다: {str(e)}")

# 용돈 가이드
st.markdown("---")
st.subheader("📋 용돈 지급 가이드")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    #### 💰 고정 용돈
    - 매주/매월 일정한 금액 지급
    - 예측 가능한 소비 계획 수립 가능
    - 초보자에게 적합
    """)

with col2:
    st.markdown("""
    #### 🎯 성과 기반 용돈
    - 저축, 미션 완료 등에 따라 지급
    - 목표 달성 동기 부여
    - 금융 습관 형성에 효과적
    """)

with col3:
    st.markdown("""
    #### 🔄 혼합 방식
    - 기본 용돈 + 보너스
    - 안정성과 동기 부여 균형
    - 중급 이상에게 추천
    """)

# 사이드바 추가 정보
with st.sidebar:
    st.markdown("---")
    st.markdown("### 💡 팁")
    st.info("""
    자녀의 나이와 금융 습관을 고려하여 용돈을 결정하세요.
    
    **일반적인 가이드:**
    - 초등 저학년: 주간 1,000-3,000원
    - 초등 고학년: 주간 3,000-5,000원
    - 중학생: 주간 5,000-10,000원
    """)
