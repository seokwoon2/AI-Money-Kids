import streamlit as st
from datetime import datetime, date
from database.db_manager import DatabaseManager
from utils.menu import render_sidebar_menu, hide_sidebar_navigation

st.set_page_config(
    page_title="💵 용돈 관리",
    page_icon="💵",
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

# 아이 전용 페이지 확인
if user_type != 'child':
    st.warning("이 페이지는 아이 전용입니다.")
    st.stop()

# 사이드바 메뉴 렌더링
render_sidebar_menu(user_id, user_name, user_type)

# 페이지 제목
st.title(f"💵 {user_name}님의 용돈 관리")
st.markdown("---")

# 용돈 기록 (세션 상태로 관리)
if 'allowance_records' not in st.session_state:
    st.session_state.allowance_records = []

# 용돈 받기
st.subheader("💰 용돈 받기")

col1, col2 = st.columns(2)

with col1:
    allowance_amount = st.number_input("용돈 금액 (원)", min_value=0, value=0, step=100)
    allowance_date = st.date_input("받은 날짜", value=date.today())
    allowance_source = st.selectbox("누구에게 받았나요?", ["부모님", "할머니/할아버지", "기타"])

with col2:
    allowance_memo = st.text_area("메모", placeholder="용돈을 받은 이유나 계획을 적어보세요")

if st.button("💵 용돈 기록하기", type="primary", use_container_width=True):
    if allowance_amount > 0:
        record = {
            "date": allowance_date,
            "amount": allowance_amount,
            "source": allowance_source,
            "memo": allowance_memo,
            "type": "income"
        }
        st.session_state.allowance_records.append(record)
        st.success(f"✅ {allowance_amount:,}원 용돈이 기록되었습니다!")
        st.rerun()
    else:
        st.warning("용돈 금액을 입력해주세요.")

st.markdown("---")

# 용돈 사용 기록
st.subheader("🛒 용돈 사용하기")

col3, col4 = st.columns(2)

with col3:
    spending_amount = st.number_input("사용 금액 (원)", min_value=0, value=0, step=100, key="spending")
    spending_date = st.date_input("사용 날짜", value=date.today(), key="spending_date")
    spending_category = st.selectbox("사용 분야", ["저축", "간식", "장난감", "책", "기타"], key="category")

with col4:
    spending_item = st.text_input("구매한 물건", key="item")
    spending_memo = st.text_area("메모", placeholder="구매한 이유나 느낀 점을 적어보세요", key="spending_memo")

if st.button("🛒 사용 기록하기", type="primary", use_container_width=True):
    if spending_amount > 0:
        record = {
            "date": spending_date,
            "amount": spending_amount,
            "category": spending_category,
            "item": spending_item,
            "memo": spending_memo,
            "type": "expense"
        }
        st.session_state.allowance_records.append(record)
        st.success(f"✅ {spending_amount:,}원 사용이 기록되었습니다!")
        st.rerun()
    else:
        st.warning("사용 금액을 입력해주세요.")

st.markdown("---")

# 용돈 현황
st.subheader("📊 용돈 현황")

if st.session_state.allowance_records:
    total_income = sum(r['amount'] for r in st.session_state.allowance_records if r['type'] == 'income')
    total_expense = sum(r['amount'] for r in st.session_state.allowance_records if r['type'] == 'expense')
    balance = total_income - total_expense
    
    col5, col6, col7 = st.columns(3)
    
    with col5:
        st.metric("💰 받은 용돈", f"{total_income:,}원")
    
    with col6:
        st.metric("🛒 사용한 금액", f"{total_expense:,}원")
    
    with col7:
        st.metric("💵 남은 금액", f"{balance:,}원", delta=f"{balance - total_income:,}원" if balance < total_income else None)
    
    # 최근 기록
    st.markdown("---")
    st.subheader("📝 최근 기록")
    
    sorted_records = sorted(st.session_state.allowance_records, key=lambda x: x['date'], reverse=True)[:10]
    
    for record in sorted_records:
        if record['type'] == 'income':
            st.success(f"💰 {record['date']} | {record['amount']:,}원 받음 | {record['source']} | {record.get('memo', '')}")
        else:
            st.info(f"🛒 {record['date']} | {record['amount']:,}원 사용 | {record['category']} - {record.get('item', '')} | {record.get('memo', '')}")
else:
    st.info("아직 기록된 용돈 내역이 없습니다. 용돈을 받거나 사용하면 여기에 기록됩니다!")

# 사이드바 추가 정보
with st.sidebar:
    st.markdown("---")
    st.markdown("### 💡 용돈 관리 팁")
    st.info("""
    용돈을 잘 관리하는 방법:
    
    **저축하기:**
    - 목표 금액의 30% 이상 저축
    - 저축 목표를 정하기
    
    **계획하기:**
    - 용돈을 받기 전에 계획 세우기
    - 필요한 것과 원하는 것 구분하기
    """)
