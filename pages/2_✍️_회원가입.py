import streamlit as st
import re

from datetime import datetime

from database.db_manager import DatabaseManager
from utils.auth import generate_parent_code, validate_parent_code, hash_password
from utils.db import get_database
from utils.validators import validate_password, validate_username


def _init_state():
    if "signup_step" not in st.session_state:
        st.session_state.signup_step = 1  # 1~3
    if "signup_data" not in st.session_state:
        st.session_state.signup_data = {}


def _render_pw_strength_bar(strength: int, label: str):
    colors = ["#FF4D4F", "#FAAD14", "#52C41A"]
    s = int(strength or 0)
    st.markdown(
        f"""
        <div style="margin-top:-10px; margin-bottom: 16px;">
          <div style="display:flex; gap:4px; margin-bottom:6px;">
            <div style="flex:1; height:4px; background:{colors[0] if s >= 0 else '#ddd'}; border-radius: 2px;"></div>
            <div style="flex:1; height:4px; background:{colors[1] if s >= 1 else '#ddd'}; border-radius: 2px;"></div>
            <div style="flex:1; height:4px; background:{colors[2] if s >= 2 else '#ddd'}; border-radius: 2px;"></div>
          </div>
          <div style="font-size:12px; color: rgba(25,25,25,0.60); font-weight:800;">비밀번호 강도: {label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _step_dots(step: int) -> str:
    # ⚫⚪⚪ 스타일(요청 그대로)
    step = int(step or 1)
    dots = []
    for i in (1, 2, 3):
        dots.append("⚫" if step >= i else "⚪")
    return " ".join(dots)


def main():
    st.set_page_config(page_title="회원가입", page_icon="✍️", layout="wide", initial_sidebar_state="collapsed")
    _init_state()

    # 로그인/회원가입 페이지는 사이드바/기본 메뉴를 숨겨 “랜딩”처럼 보이게
    st.markdown(
        """
        <style>
          [data-testid="stSidebar"] { display:none !important; }
          [data-testid="stSidebarNav"] { display:none !important; }
          #MainMenu, footer { display:none !important; }
          header { background: transparent !important; }

          /* 페이지 전체 배경 */
          .stApp { background: #F9F9F9 !important; }
          .block-container { max-width: 1200px !important; padding-top: 1.2rem !important; }

          /* 오른쪽 폼 영역 카드 느낌 */
          div[data-testid="stVerticalBlockBorderWrapper"]:has(#amf_signup_right_anchor){
            background: #FFFFFF !important;
            border: 1px solid rgba(17,24,39,0.08) !important;
            border-radius: 20px !important;
            box-shadow: 0 18px 45px rgba(17,24,39,0.10) !important;
            overflow: hidden !important;
          }
          div[data-testid="stVerticalBlockBorderWrapper"]:has(#amf_signup_right_anchor) > div{
            padding: 34px 26px !important;
          }

          /* 버튼 기본 높이 */
          .stButton > button{
            height: 56px !important;
            border-radius: 12px !important;
            font-weight: 800 !important;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
          }
          .stButton > button:hover{
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.12);
          }
          /* CTA(노랑) */
          .stButton > button[kind="primary"], button[kind="primary"]{
            background: #FFEB00 !important;
            color: #191919 !important;
            border: 0 !important;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ✅ PC 2컬럼 레이아웃 (50% + 50%)
    col_left, col_right = st.columns([1, 1])

    # ===== 왼쪽: 일러스트/히어로 =====
    with col_left:
        st.markdown(
            """
            <div style="
                background: linear-gradient(135deg, #8B7EC8 0%, #6B5B95 100%);
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
                <h2 style="color: white; font-size: 32px; font-weight: 800; margin-bottom: 16px; letter-spacing:-0.3px;">
                    함께 시작해볼까요?
                </h2>
                <p style="color: rgba(255,255,255,0.92); font-size: 16px; margin-bottom: 40px; line-height: 1.55; font-weight:700;">
                    AI Money Friends와 함께<br/>
                    금융 교육을 시작해요!
                </p>

                <!-- 기능 뱃지 -->
                <div style="display: flex; flex-wrap: wrap; gap: 12px; justify-content: center; margin-bottom: 40px;">
                    <span style="background: rgba(255,255,255,0.18); padding: 8px 16px; border-radius: 20px; color: white; font-size: 14px; font-weight:800;">
                        💰 돈 관리
                    </span>
                    <span style="background: rgba(255,255,255,0.18); padding: 8px 16px; border-radius: 20px; color: white; font-size: 14px; font-weight:800;">
                        🎯 저축 목표
                    </span>
                    <span style="background: rgba(255,255,255,0.18); padding: 8px 16px; border-radius: 20px; color: white; font-size: 14px; font-weight:800;">
                        😊 감정 기록
                    </span>
                    <span style="background: rgba(255,255,255,0.18); padding: 8px 16px; border-radius: 20px; color: white; font-size: 14px; font-weight:800;">
                        👨‍👩‍👧 가족 연결
                    </span>
                </div>

                <!-- 신뢰 배지 -->
                <div style="
                    background: rgba(255,255,255,0.14);
                    backdrop-filter: blur(10px);
                    padding: 16px 24px;
                    border-radius: 16px;
                    color: white;
                    font-size: 14px;
                    font-weight: 800;
                    border: 1px solid rgba(255,255,255,0.18);
                ">
                    ✅ 1,000+ 가족이 함께해요
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ===== 오른쪽: 폼 영역(레이아웃만) =====
    with col_right:
        dbm = DatabaseManager()
        db = get_database()
        with st.container(border=True):
            st.markdown('<div id="amf_signup_right_anchor"></div>', unsafe_allow_html=True)

            st.markdown(
                """
                <div style="text-align:center; margin-bottom: 16px;">
                  <div style="font-size: 54px; line-height: 1;">🐷</div>
                  <div style="font-size: 28px; font-weight: 900; margin-top: 10px; letter-spacing:-0.3px;">회원가입</div>
                  <div style="margin-top: 6px; color: rgba(25,25,25,0.60); font-weight: 700; font-size: 14px;">
                    어린이를 위한 금융 교육 친구
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                f"""
                <div style="text-align:center; margin-bottom: 24px; font-size: 18px; letter-spacing: 2px;">
                  {_step_dots(int(st.session_state.signup_step))}
                </div>
                """,
                unsafe_allow_html=True,
            )

            step = int(st.session_state.get("signup_step") or 1)

            # =========================
            # STEP 1: 사용자 유형 선택
            # =========================
            if step == 1:
                st.markdown("### 사용자 유형을 선택하세요")
                c1, c2 = st.columns(2)
                with c1:
                    with st.container(border=True):
                        st.markdown("#### 👨‍👩‍👧 부모님")
                        st.caption("가족의 금융 활동을 관리해요")
                        if st.button("부모님 선택", key="signup_pick_parent", use_container_width=True, type="primary"):
                            st.session_state.signup_data["user_type"] = "parent"
                            st.session_state.signup_step = 2
                            st.rerun()
                with c2:
                    with st.container(border=True):
                        st.markdown("#### 👶 아이")
                        st.caption("용돈을 관리하고 경제를 배워요")
                        if st.button("아이 선택", key="signup_pick_child", use_container_width=True):
                            st.session_state.signup_data["user_type"] = "child"
                            st.session_state.signup_step = 2
                            st.rerun()

            # =========================
            # STEP 2: 기본 정보 입력
            # =========================
            elif step == 2:
                user_type = st.session_state.signup_data.get("user_type")
                if user_type not in ("parent", "child"):
                    st.session_state.signup_step = 1
                    st.rerun()

                st.markdown("### 기본 정보를 입력하세요")

                name = st.text_input("이름", placeholder="홍길동", key="signup_name")
                username = st.text_input("아이디", placeholder="gildong123", key="signup_username")

                # 실시간 아이디 중복 체크
                username_ok = False
                if username:
                    ok, msg = validate_username(username)
                    username_ok = bool(ok)
                    (st.success if ok else st.error)(msg)

                password = st.text_input("비밀번호", type="password", placeholder="6자 이상 입력", key="signup_password")
                if password:
                    strength, strength_text = validate_password(password)
                    _render_pw_strength_bar(strength, strength_text)

                password_confirm = st.text_input(
                    "비밀번호 확인", type="password", placeholder="비밀번호를 다시 입력", key="signup_password_confirm"
                )
                pw_ok = bool(password and password_confirm and password == password_confirm)
                if password and password_confirm:
                    if pw_ok:
                        st.success("비밀번호가 일치합니다 ✓")
                    else:
                        st.error("비밀번호가 일치하지 않습니다")

                invite_code = ""
                invite_ok = True
                parent_user = None
                if user_type == "child":
                    st.markdown("---")
                    st.markdown("**부모님 초대 코드(6자리)**")
                    invite_code = st.text_input("초대 코드", placeholder="ABC123", max_chars=6, key="signup_invite_code")
                    invite_code = (invite_code or "").strip().upper()
                    invite_ok = False
                    if invite_code:
                        if len(invite_code) != 6 or not validate_parent_code(invite_code):
                            st.error("초대 코드는 6자리로 입력해주세요")
                        else:
                            try:
                                parent_user = db.find_parent_by_invite_code(invite_code) if hasattr(db, "find_parent_by_invite_code") else None
                            except Exception:
                                parent_user = None
                            if parent_user:
                                invite_ok = True
                                st.success("유효한 초대 코드입니다 ✓")
                            else:
                                st.error("올바르지 않은 초대 코드입니다")

                # 버튼
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                b1, b2 = st.columns(2)
                with b1:
                    if st.button("← 이전", use_container_width=True, key="signup_back_step2"):
                        st.session_state.signup_step = 1
                        st.rerun()
                with b2:
                    form_ok = bool(name and username_ok and pw_ok)
                    if user_type == "child":
                        form_ok = form_ok and invite_ok

                    if st.button("다음 →", use_container_width=True, key="signup_next_step2", disabled=not form_ok):
                        st.session_state.signup_data.update(
                            {
                                "name": name.strip(),
                                "username": username.strip(),
                                "password": password,
                                "invite_code": invite_code if user_type == "child" else None,
                            }
                        )
                        st.session_state.signup_step = 3
                        st.rerun()

            # =========================
            # STEP 3: 약관 동의 + 가입 완료
            # =========================
            else:
                st.markdown("### 약관 동의")

                agree_all = st.checkbox("전체 동의", key="signup_agree_all")
                agree_terms = st.checkbox("이용약관 동의 (필수)", value=agree_all, key="signup_agree_terms")
                agree_privacy = st.checkbox("개인정보처리방침 동의 (필수)", value=agree_all, key="signup_agree_privacy")
                agree_marketing = st.checkbox("마케팅 수신 동의 (선택)", value=agree_all, key="signup_agree_marketing")

                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                b1, b2 = st.columns(2)
                with b1:
                    if st.button("← 이전", use_container_width=True, key="signup_back_step3"):
                        st.session_state.signup_step = 2
                        st.rerun()
                with b2:
                    can_submit = bool(agree_terms and agree_privacy)
                    if st.button("가입 완료 🚀", use_container_width=True, type="primary", key="signup_submit", disabled=not can_submit):
                        data = st.session_state.get("signup_data") or {}
                        user_type = data.get("user_type")
                        name = (data.get("name") or "").strip()
                        username = (data.get("username") or "").strip()
                        password = data.get("password") or ""

                        # 마지막 방어 검증
                    ok, msg = validate_username(username)
                        if not ok:
                            st.error(msg)
                            st.session_state.signup_step = 2
                            st.rerun()

                        if user_type not in ("parent", "child") or not name or not password:
                            st.error("입력 정보가 올바르지 않아요. 다시 시도해주세요.")
                            st.session_state.signup_step = 1
                            st.rerun()

                        try:
                            if user_type == "parent":
                                parent_code = generate_parent_code()
                            user_data = {
                                "username": username,
                                "password": hash_password(password),
                                "name": name,
                                "user_type": "parent",
                                "parent_code": parent_code,
                                "created_at": datetime.now(),
                            }
                            res = db.users.insert_one(user_data)
                            new_id = int(res.inserted_id)
                                st.success("회원가입이 완료되었습니다! 🎉")
                            invite_code = parent_code[-6:]
                            st.info(f"**초대 코드: {invite_code}**\n\n자녀가 가입할 때 이 코드를 입력하면 연결돼요.")
                            else:
                                invite_code = (data.get("invite_code") or "").strip().upper()
                                if len(invite_code) != 6 or not validate_parent_code(invite_code):
                                    st.error("초대 코드가 올바르지 않아요.")
                                    st.session_state.signup_step = 2
                                    st.rerun()
                            parent = dbm.find_parent_by_invite_code(invite_code)
                                if not parent:
                                    st.error("초대 코드가 올바르지 않아요.")
                                    st.session_state.signup_step = 2
                                    st.rerun()
                                parent_code = (parent.get("parent_code") or "").strip().upper()
                            user_data = {
                                "username": username,
                                "password": hash_password(password),
                                "name": name,
                                "user_type": "child",
                                "parent_code": parent_code,
                                "created_at": datetime.now(),
                            }
                            res = db.users.insert_one(user_data)
                            new_id = int(res.inserted_id)
                                st.success("회원가입이 완료되었습니다! 🎉")

                            # 로그인 처리(바로 사용)
                            st.session_state["logged_in"] = True
                            st.session_state["user_id"] = int(new_id)
                            st.session_state["user_name"] = name
                            st.session_state["user_type"] = user_type
                            st.session_state["username"] = username

                            st.balloons()
                            st.switch_page("pages/1_🏠_대시보드.py")
                        except Exception:
                            st.error("회원가입에 실패했습니다. 잠시 후 다시 시도해주세요.")


if __name__ == "__main__":
    main()

