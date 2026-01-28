import streamlit as st
from database.db_manager import DatabaseManager
from utils.menu import render_sidebar_menu, hide_sidebar_navigation

st.set_page_config(
    page_title="📚 금융 교육 가이드",
    page_icon="📚",
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

# 사이드바 메뉴 렌더링 (가장 먼저 실행하여 메뉴 유실 방지)
render_sidebar_menu(user_id, user_name, user_type)

# 부모 전용 페이지 확인
if user_type != 'parent':
    st.warning("이 페이지는 부모 전용입니다.")
    st.stop()

# 페이지 제목
st.title("📚 금융 교육 가이드")
st.markdown("---")

# 탭 구성
tab1, tab2, tab3, tab4 = st.tabs(["🎯 기본 원칙", "💬 대화 가이드", "📊 나이별 가이드", "🎮 실전 활동"])

with tab1:
    st.subheader("🎯 키즈 금융 교육 기본 원칙")
    
    st.markdown("""
    ### 1. 긍정적 접근
    - 돈을 부정적으로 표현하지 않기
    - "돈이 없어서 못 산다"보다 "지금은 필요 없어서 나중에 사자"
    - 저축을 억압이 아닌 목표 달성으로 표현
    
    ### 2. 실전 경험 제공
    - 실제 돈을 다루는 경험 쌓기
    - 작은 금액부터 시작하여 점진적 확대
    - 성공 경험을 통해 자신감 형성
    
    ### 3. 선택의 기회 제공
    - 아이가 직접 선택하고 결정하도록 유도
    - 실수를 통해 배울 수 있는 안전한 환경 조성
    - 결과에 대한 책임감 인식
    """)

with tab2:
    st.subheader("💬 자녀와의 금융 대화 가이드")
    
    st.markdown("""
    ### 좋은 대화 예시
    
    **❌ 피해야 할 표현:**
    - "돈이 없어서 못 산다"
    - "비싸니까 안 돼"
    - "돈 낭비하지 마"
    
    **✅ 권장 표현:**
    - "이번 달 예산을 확인해볼까?"
    - "이것과 저것 중에 어떤 게 더 필요할까?"
    - "저축 목표를 달성하면 살 수 있어"
    
    ### 대화 주제 제안
    1. **소비 결정 과정**: 왜 그 물건을 사고 싶은지
    2. **기회비용**: 이것을 사면 다른 것을 포기해야 함
    3. **저축의 가치**: 목표를 위해 기다리는 것의 의미
    4. **가격 비교**: 같은 물건을 더 저렴하게 살 수 있는 방법
    """)

with tab3:
    st.subheader("📊 나이별 금융 교육 가이드")
    
    age_guides = {
        "5-7세": {
            "개념": "돈의 기본 개념, 동전과 지폐 구분",
            "활동": "동전 세기, 간단한 구매 경험",
            "목표": "돈이 무엇인지 이해하기"
        },
        "8-10세": {
            "개념": "저축의 개념, 용돈 관리 시작",
            "활동": "저금통 사용, 작은 목표 설정",
            "목표": "기다림과 저축의 가치 이해"
        },
        "11-13세": {
            "개념": "예산 계획, 가격 비교, 기회비용",
            "활동": "용돈 계획표 작성, 가격 조사",
            "목표": "계획적 소비 습관 형성"
        },
        "14세 이상": {
            "개념": "복리, 투자 기본, 금융 상품",
            "활동": "장기 저축 목표, 간단한 투자 개념",
            "목표": "미래를 위한 금융 계획 수립"
        }
    }
    
    for age_range, guide in age_guides.items():
        with st.expander(f"👶 {age_range}세"):
            st.markdown(f"**핵심 개념**: {guide['개념']}")
            st.markdown(f"**추천 활동**: {guide['활동']}")
            st.markdown(f"**교육 목표**: {guide['목표']}")

with tab4:
    st.subheader("🎮 실전 금융 교육 활동")
    
    activities = [
        {
            "제목": "💰 저금통 만들기",
            "나이": "5세 이상",
            "방법": "아이와 함께 저금통을 만들고, 목표 금액을 정한 후 저축을 시작합니다.",
            "효과": "저축의 시각적 성취감을 느낄 수 있습니다."
        },
        {
            "제목": "🛒 쇼핑 게임",
            "나이": "7세 이상",
            "방법": "가상의 예산을 주고 필요한 물건을 선택하도록 합니다.",
            "효과": "예산 내에서 선택하는 능력을 기릅니다."
        },
        {
            "제목": "📝 용돈 일기",
            "나이": "9세 이상",
            "방법": "용돈을 받고 쓴 내역을 기록하도록 합니다.",
            "효과": "소비 패턴을 인식하고 개선할 수 있습니다."
        },
        {
            "제목": "🎯 저축 목표 설정",
            "나이": "10세 이상",
            "방법": "원하는 물건의 가격을 조사하고, 저축 계획을 세웁니다.",
            "효과": "목표 지향적 저축 습관을 형성합니다."
        }
    ]
    
    for activity in activities:
        with st.expander(f"{activity['제목']} ({activity['나이']})"):
            st.markdown(f"**방법**: {activity['방법']}")
            st.markdown(f"**효과**: {activity['효과']}")

# 사이드바 추가 정보
with st.sidebar:
    st.markdown("---")
    st.markdown("### 💡 참고 자료")
    st.info("""
    금융 교육은 하루아침에 이루어지지 않습니다.
    
    **꾸준함이 중요합니다:**
    - 매일 작은 대화로 시작
    - 실제 경험을 통한 학습
    - 긍정적 피드백 제공
    """)
