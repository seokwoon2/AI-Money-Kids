import streamlit as st

from styles.common import inject_styles, COLORS

st.set_page_config(
    page_title="회원가입 - AI Money Friends",
    page_icon="✍️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

inject_styles()

# 세션 상태 초기화
if "signup_step" not in st.session_state:
    st.session_state.signup_step = 1
if "signup_data" not in st.session_state:
    st.session_state.signup_data = {}

# 헤더
st.markdown(
    """
<div style="text-align: center; margin-bottom: 40px;">
    <div style="font-size: 64px; margin-bottom: 16px;">🐷</div>
    <h1 style="font-size: 32px; font-weight: 700; margin-bottom: 8px;">회원가입</h1>
    <p style="font-size: 16px; color: #999;">어린이를 위한 금융 교육 친구</p>
</div>
""",
    unsafe_allow_html=True,
)

# 진행 표시
steps = ["⚫", "⚪", "⚪"]
if st.session_state.signup_step >= 2:
    steps[1] = "⚫"
if st.session_state.signup_step >= 3:
    steps[2] = "⚫"

st.markdown(
    f"""
<div style="text-align: center; margin-bottom: 40px; font-size: 24px;">
    {' '.join(steps)}
</div>
""",
    unsafe_allow_html=True,
)

# ====== STEP 1: 사용자 유형 선택 ======
if st.session_state.signup_step == 1:
    st.markdown("### 사용자 유형을 선택하세요")
    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("👨‍👩‍👧 부모님", key="parent", use_container_width=True):
        st.session_state.signup_data["user_type"] = "parent"
        st.session_state.signup_step = 2
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("👶 아이", key="child", use_container_width=True):
        st.session_state.signup_data["user_type"] = "child"
        st.session_state.signup_step = 2
        st.rerun()

# ====== STEP 2: 기본 정보 입력 ======
elif st.session_state.signup_step == 2:
    user_type = st.session_state.signup_data.get("user_type", "parent")

    st.markdown(f"### {'부모님' if user_type == 'parent' else '아이'} 정보 입력")
    st.markdown("<br>", unsafe_allow_html=True)

    name = st.text_input("이름", placeholder="홍길동")
    username = st.text_input("아이디", placeholder="gildong123")
    password = st.text_input("비밀번호", type="password", placeholder="6자 이상")
    password_confirm = st.text_input("비밀번호 확인", type="password")

    # 아이인 경우 초대 코드
    invite_code = None
    if user_type == "child":
        st.markdown("<br>", unsafe_allow_html=True)
        invite_code = st.text_input("부모님 초대 코드 (6자리)", placeholder="ABC123", max_chars=6)

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("← 이전", use_container_width=True):
            st.session_state.signup_step = 1
            st.rerun()

    with col2:
        can_proceed = name and username and password and (password == password_confirm) and (len(password) >= 6)

        if user_type == "child":
            can_proceed = can_proceed and invite_code and (len(invite_code) == 6)

        if st.button("다음 →", use_container_width=True, disabled=not can_proceed):
            st.session_state.signup_data.update(
                {"name": name, "username": username, "password": password, "invite_code": invite_code}
            )
            st.session_state.signup_step = 3
            st.rerun()

# ====== STEP 3: 약관 동의 ======
elif st.session_state.signup_step == 3:
    st.markdown("### 약관 동의")
    st.markdown("<br>", unsafe_allow_html=True)

    agree_all = st.checkbox("전체 동의")
    st.markdown("<br>", unsafe_allow_html=True)

    agree_terms = st.checkbox("이용약관 동의 (필수)", value=agree_all)
    agree_privacy = st.checkbox("개인정보처리방침 동의 (필수)", value=agree_all)
    agree_marketing = st.checkbox("마케팅 수신 동의 (선택)", value=agree_all)

    st.markdown("<br><br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("← 이전", use_container_width=True):
            st.session_state.signup_step = 2
            st.rerun()

    with col2:
        can_submit = agree_terms and agree_privacy

        if st.button("가입 완료 🚀", use_container_width=True, type="primary", disabled=not can_submit):
            # 회원가입 처리 (DB 저장 로직은 추후 연결)
            st.success("회원가입이 완료되었습니다! 🎉")
            st.balloons()

            # 초대 코드 표시 (부모인 경우)
            if st.session_state.signup_data.get("user_type") == "parent":
                import random
                import string

                invite_code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
                st.info(f"**초대 코드: {invite_code}**\n\n이 코드를 자녀에게 알려주세요!")

            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("시작하기", use_container_width=True):
                # 현재 레포에는 1_🏠_메인.py가 없어서 대시보드로 이동
                st.switch_page("pages/1_🏠_대시보드.py")

# 버튼 스타일
st.markdown(
    f"""
<style>
.stButton > button {{
    height: 56px !important;
    font-size: 18px !important;
    font-weight: 700 !important;
    border-radius: 12px !important;
}}
.stButton > button:hover {{
    transform: translateY(-2px);
}}
button[kind="primary"] {{
    background: {COLORS['secondary']} !important;
    color: {COLORS['black']} !important;
}}
</style>
""",
    unsafe_allow_html=True,
)

