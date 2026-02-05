import streamlit as st
from styles.common import inject_styles, COLORS
import re
from utils.db import get_database
from utils.auth import hash_password
import random
import string
from datetime import datetime
from textwrap import dedent as _dedent

st.set_page_config(
    page_title="회원가입 - AI Money Friends",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_styles()

# DB 연결 (현재 프로젝트는 SQLite 기반 Mongo-like facade)
db = get_database()

# 세션 상태 초기화
if "signup_step" not in st.session_state:
    st.session_state.signup_step = 1

if "signup_data" not in st.session_state:
    st.session_state.signup_data = {}


def validate_username(username):
    """아이디 유효성 검사"""
    if len(username) < 4:
        return False, "아이디는 4자 이상이어야 합니다"
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        return False, "영문, 숫자, 언더스코어만 사용 가능합니다"

    # 중복 체크
    if db.users.find_one({"username": username}):
        return False, "이미 사용 중인 아이디입니다"

    return True, "사용 가능한 아이디입니다 ✓"


def validate_password(password):
    """비밀번호 강도 검사"""
    if len(password) < 6:
        return 0, "너무 짧아요"
    elif len(password) < 8:
        return 1, "보통"
    elif len(password) >= 8 and re.search(r"[A-Z]", password) and re.search(r"[0-9]", password):
        return 2, "강함"
    else:
        return 1, "보통"


def generate_invite_code():
    """초대 코드 생성 (6자리)"""
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


def validate_invite_code(code):
    """초대 코드 유효성 검사"""
    parent = db.users.find_one({"user_type": "parent", "invite_code": code})
    return parent is not None


# ==================== PC 버전 레이아웃 ====================
is_mobile = st.session_state.get("is_mobile", False)

if not is_mobile:
    # 2컬럼 레이아웃
    col_left, col_right = st.columns([1, 1])

    # 왼쪽: 일러스트 영역
    with col_left:
        st.markdown(
            _dedent(
                f"""
                <div style="
                    background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['primary_dark']} 100%);
                    border-radius: 24px;
                    padding: 60px 40px;
                    height: 100%;
                    min-height: 600px;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    text-align: center;
                ">
                    <div style="font-size: 120px; margin-bottom: 24px;">🎉</div>
                    <h2 style="color: white; font-size: 32px; font-weight: 700; margin-bottom: 16px;">
                        함께 시작해볼까요?
                    </h2>
                    <p style="color: rgba(255,255,255,0.9); font-size: 16px; margin-bottom: 40px;">
                        AI Money Friends와 함께<br/>
                        금융 교육을 시작해요!
                    </p>

                    <div style="display: flex; flex-wrap: wrap; gap: 12px; justify-content: center; margin-bottom: 40px;">
                        <span style="background: rgba(255,255,255,0.2); padding: 8px 16px; border-radius: 20px; color: white; font-size: 14px;">
                            💰 돈 관리
                        </span>
                        <span style="background: rgba(255,255,255,0.2); padding: 8px 16px; border-radius: 20px; color: white; font-size: 14px;">
                            🎯 저축 목표
                        </span>
                        <span style="background: rgba(255,255,255,0.2); padding: 8px 16px; border-radius: 20px; color: white; font-size: 14px;">
                            😊 감정 기록
                        </span>
                        <span style="background: rgba(255,255,255,0.2); padding: 8px 16px; border-radius: 20px; color: white; font-size: 14px;">
                            👨‍👩‍👧 가족 연결
                        </span>
                    </div>

                    <div style="
                        background: rgba(255,255,255,0.1);
                        backdrop-filter: blur(10px);
                        padding: 16px 24px;
                        border-radius: 16px;
                        color: white;
                        font-size: 14px;
                    ">
                        ✅ 1,000+ 가족이 함께해요
                    </div>
                </div>
                """
            ),
            unsafe_allow_html=True,
        )

    # 오른쪽: 가입 폼
    with col_right:
        st.markdown(
            _dedent(
                """
                <div style="padding: 40px 20px;">
                    <div style="text-align: center; margin-bottom: 32px;">
                        <div style="font-size: 48px; margin-bottom: 12px;">🐷</div>
                        <h1 style="font-size: 28px; font-weight: 700; margin-bottom: 8px;">회원가입</h1>
                        <p style="font-size: 14px; color: #999;">어린이를 위한 금융 교육 친구</p>
                    </div>
                </div>
                """
            ),
            unsafe_allow_html=True,
        )

        # 진행 단계 표시
        st.markdown(
            _dedent(
                f"""
                <div style="text-align: center; margin-bottom: 32px;">
                    <span style="color: {'#8B7EC8' if st.session_state.signup_step >= 1 else '#ddd'}; font-size: 24px;">⚫</span>
                    <span style="color: {'#8B7EC8' if st.session_state.signup_step >= 2 else '#ddd'}; margin: 0 8px; font-size: 24px;">⚫</span>
                    <span style="color: {'#8B7EC8' if st.session_state.signup_step >= 3 else '#ddd'}; font-size: 24px;">⚫</span>
                </div>
                """
            ),
            unsafe_allow_html=True,
        )

        # STEP 1: 사용자 유형 선택
        if st.session_state.signup_step == 1:
            st.markdown("<h3 style='margin-bottom: 20px; text-align: center;'>사용자 유형을 선택하세요</h3>", unsafe_allow_html=True)

            col1, col2 = st.columns(2)

            with col1:
                if st.button("👨‍👩‍👧\n\n부모님", key="user_parent", use_container_width=True):
                    st.session_state.signup_data["user_type"] = "parent"
                    st.session_state.signup_step = 2
                    st.rerun()

            with col2:
                if st.button("👶\n\n아이", key="user_child", use_container_width=True):
                    st.session_state.signup_data["user_type"] = "child"
                    st.session_state.signup_step = 2
                    st.rerun()

            # 버튼 스타일 추가
            st.markdown(
                _dedent(
                    """
                    <style>
                    div[data-testid="column"] > div > div > div > button {
                        height: 120px !important;
                        font-size: 18px !important;
                        font-weight: 700 !important;
                        border: 2px solid #E8E8E8 !important;
                    }
                    div[data-testid="column"] > div > div > div > button:hover {
                        border-color: #8B7EC8 !important;
                        background: #F5F3FF !important;
                    }
                    </style>
                    """
                ),
                unsafe_allow_html=True,
            )

        # STEP 2: 기본 정보 입력
        elif st.session_state.signup_step == 2:
            user_type = st.session_state.signup_data["user_type"]

            st.markdown(
                f"<h3 style='margin-bottom: 20px; text-align: center;'>{'부모님' if user_type == 'parent' else '아이'} 정보를 입력하세요</h3>",
                unsafe_allow_html=True,
            )

            # 이름
            name = st.text_input("이름", placeholder="홍길동", key="signup_name")

            # 아이디
            username = st.text_input("아이디", placeholder="gildong123", key="signup_username")

            if username:
                is_valid, message = validate_username(username)
                if is_valid:
                    st.success(message)
                else:
                    st.error(message)

            # 비밀번호
            password = st.text_input("비밀번호", type="password", placeholder="6자 이상 입력", key="signup_password")

            if password:
                strength, strength_text = validate_password(password)
                colors = ["#FF4D4F", "#FAAD14", "#52C41A"]
                st.markdown(
                    f"""
                <div style="margin-top: -10px; margin-bottom: 16px;">
                    <div style="display: flex; gap: 4px; margin-bottom: 4px;">
                        <div style="flex: 1; height: 4px; background: {colors[0] if strength >= 0 else '#ddd'}; border-radius: 2px;"></div>
                        <div style="flex: 1; height: 4px; background: {colors[1] if strength >= 1 else '#ddd'}; border-radius: 2px;"></div>
                        <div style="flex: 1; height: 4px; background: {colors[2] if strength >= 2 else '#ddd'}; border-radius: 2px;"></div>
                    </div>
                    <div style="font-size: 12px; color: #999;">비밀번호 강도: {strength_text}</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

            # 비밀번호 확인
            password_confirm = st.text_input(
                "비밀번호 확인", type="password", placeholder="비밀번호를 다시 입력", key="signup_password_confirm"
            )

            if password and password_confirm:
                if password == password_confirm:
                    st.success("비밀번호가 일치합니다 ✓")
                else:
                    st.error("비밀번호가 일치하지 않습니다")

            # 아이 선택 시: 부모님 초대 코드
            invite_code = None
            if user_type == "child":
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("**부모님 초대 코드**")
                invite_code = st.text_input("초대 코드 (6자리)", placeholder="ABC123", max_chars=6, key="signup_invite_code")

                if invite_code and len(invite_code) == 6:
                    if validate_invite_code(invite_code.upper()):
                        st.success("유효한 초대 코드입니다 ✓")
                    else:
                        st.error("올바르지 않은 초대 코드입니다")

            st.markdown("<br>", unsafe_allow_html=True)

            # 버튼
            col1, col2 = st.columns(2)

            with col1:
                if st.button("← 이전", use_container_width=True, key="back_step2"):
                    st.session_state.signup_step = 1
                    st.rerun()

            with col2:
                # 입력 검증
                is_valid_form = (
                    name
                    and username
                    and password
                    and password_confirm
                    and password == password_confirm
                    and validate_username(username)[0]
                )

                if user_type == "child":
                    is_valid_form = (
                        is_valid_form
                        and invite_code
                        and len(invite_code) == 6
                        and validate_invite_code(invite_code.upper())
                    )

                if st.button("다음 →", use_container_width=True, disabled=not is_valid_form, key="next_step2"):
                    st.session_state.signup_data.update(
                        {
                            "name": name,
                            "username": username,
                            "password": password,
                            "invite_code": invite_code.upper() if user_type == "child" and invite_code else None,
                        }
                    )
                    st.session_state.signup_step = 3
                    st.rerun()

        # STEP 3: 약관 동의
        elif st.session_state.signup_step == 3:
            st.markdown("<h3 style='margin-bottom: 20px; text-align: center;'>약관 동의</h3>", unsafe_allow_html=True)

            agree_all = st.checkbox("전체 동의", key="agree_all")

            st.markdown("<br>", unsafe_allow_html=True)

            agree_terms = st.checkbox("이용약관 동의 (필수)", value=agree_all, key="agree_terms")
            agree_privacy = st.checkbox("개인정보처리방침 동의 (필수)", value=agree_all, key="agree_privacy")
            agree_marketing = st.checkbox("마케팅 수신 동의 (선택)", value=agree_all, key="agree_marketing")

            st.markdown("<br><br>", unsafe_allow_html=True)

            # 버튼
            col1, col2 = st.columns(2)

            with col1:
                if st.button("← 이전", use_container_width=True, key="back_step3"):
                    st.session_state.signup_step = 2
                    st.rerun()

            with col2:
                is_valid_terms = agree_terms and agree_privacy

                if st.button("가입 완료 🚀", use_container_width=True, disabled=not is_valid_terms, type="primary", key="submit_signup"):
                    # 회원가입 처리
                    user_data = {
                        "name": st.session_state.signup_data["name"],
                        "username": st.session_state.signup_data["username"],
                        "password": hash_password(st.session_state.signup_data["password"]),
                        "user_type": st.session_state.signup_data["user_type"],
                        "agree_marketing": agree_marketing,
                        "created_at": datetime.now(),
                    }

                    # 부모 계정: 초대 코드 생성
                    parent = None
                    if user_data["user_type"] == "parent":
                        user_data["invite_code"] = generate_invite_code()
                        user_data["children"] = []
                    else:
                        invite_code = st.session_state.signup_data["invite_code"]
                        parent = db.users.find_one({"invite_code": invite_code})
                        if not parent:
                            st.error("올바르지 않은 초대 코드입니다")
                            st.session_state.signup_step = 2
                            st.rerun()
                        user_data["parent_id"] = parent["_id"]
                        # 기존 앱 호환용: child는 parent_code도 저장
                        user_data["parent_code"] = parent.get("parent_code")

                    # DB 저장
                    result = db.users.insert_one(user_data)

                    # 부모-자녀 연결
                    if user_data["user_type"] == "child" and parent:
                        db.users.update_one({"_id": parent["_id"]}, {"$push": {"children": result.inserted_id}})

                    # 세션에 저장 (현재 앱은 logged_in 기준)
                    st.session_state["logged_in"] = True
                    st.session_state["user_id"] = result.inserted_id
                    st.session_state["user_name"] = user_data["name"]
                    st.session_state["user_type"] = user_data["user_type"]
                    st.session_state["username"] = user_data["username"]

                    if user_data["user_type"] == "parent":
                        st.session_state["invite_code"] = user_data["invite_code"]

                    st.success("회원가입이 완료되었습니다! 🎉")

                    # 초대 코드 표시 (부모 계정)
                    if user_data["user_type"] == "parent":
                        st.info(f"**초대 코드: {user_data['invite_code']}**\n\n이 코드를 자녀에게 알려주세요!")

                    st.balloons()

                    # 메인 페이지(대시보드)로 이동
                    if st.button("시작하기", use_container_width=True, key="goto_main"):
                        st.switch_page("pages/1_🏠_대시보드.py")

else:
    # 모바일 버전(간단 스켈레톤)
    st.markdown(
        """
    <div style="text-align: center; margin-bottom: 32px;">
        <div style="font-size: 64px; margin-bottom: 12px;">🐷</div>
        <h1 style="font-size: 24px; font-weight: 700; margin-bottom: 8px;">회원가입</h1>
        <p style="font-size: 14px; color: #999;">어린이를 위한 금융 교육 친구</p>
    </div>
    """,
        unsafe_allow_html=True,
    )
    st.info("모바일 버전은 PC 버전과 동일 로직으로 확장할 수 있어요.")

