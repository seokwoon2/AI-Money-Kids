import streamlit as st
from textwrap import dedent as _dedent

from styles.common import inject_styles, COLORS
from utils.db import get_database
from utils.auth import verify_password


def _pill_badges_html() -> str:
    return _dedent(
        """
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
        """
    ).strip()


def _social_button(label: str, bg: str, fg: str, border: str | None = None) -> None:
    b = f"border: 1px solid {border};" if border else "border: none;"
    st.markdown(
        _dedent(
            f"""
            <div style="
              width:100%;
              height:56px;
              border-radius:12px;
              background:{bg};
              color:{fg};
              display:flex;
              align-items:center;
              justify-content:center;
              font-weight:800;
              font-size:16px;
              {b}
              opacity:0.65;
              user-select:none;
              margin-bottom: 12px;
            ">
              {label} <span style="margin-left:8px; font-weight:900; opacity:0.85;">(준비중)</span>
            </div>
            """
        ).strip(),
        unsafe_allow_html=True,
    )


def main():
    st.set_page_config(
        page_title="로그인 - AI Money Friends",
        page_icon="🔐",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    inject_styles()
    db = get_database()

    # 페이지 추가 스타일(2컬럼 로그인 레이아웃)
    st.markdown(
        _dedent(
            f"""
            <style>
              .block-container {{ padding-top: 1.2rem !important; }}

              /* 버튼 높이/라운드 통일 */
              .stButton > button {{
                height: 56px !important;
                border-radius: 12px !important;
                font-weight: 800 !important;
              }}

              /* 탭 pill */
              .stTabs [data-baseweb="tab-list"] {{
                gap: 8px;
                background: {COLORS["gray_1"]};
                border-radius: 12px;
                padding: 4px;
              }}
              .stTabs [data-baseweb="tab"] {{
                border-radius: 10px;
                padding: 10px 14px;
                font-weight: 700;
              }}
              .stTabs [aria-selected="true"] {{
                background: white !important;
              }}
            </style>
            """
        ).strip(),
        unsafe_allow_html=True,
    )

    col_left, col_right = st.columns([1, 1])

    # ==================== 왼쪽: 히어로 ====================
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
                    <div style="font-size: 120px; margin-bottom: 24px;">🐷</div>
                    <h2 style="color: white; font-size: 32px; font-weight: 800; margin-bottom: 16px;">
                        다시 만나서 반가워요!
                    </h2>
                    <p style="color: rgba(255,255,255,0.9); font-size: 16px; margin-bottom: 40px;">
                        AI Money Friends와 함께<br/>
                        오늘도 금융 교육을 시작해요!
                    </p>
                    {_pill_badges_html()}
                    <div style="
                        background: rgba(255,255,255,0.1);
                        backdrop-filter: blur(10px);
                        padding: 16px 24px;
                        border-radius: 16px;
                        color: white;
                        font-size: 14px;
                    ">
                        ✅ 1,000+ 가족이 함께 사용 중
                    </div>
                </div>
                """
            ).strip(),
            unsafe_allow_html=True,
        )

    # ==================== 오른쪽: 로그인 폼 ====================
    with col_right:
        st.markdown(
            _dedent(
                """
                <div style="padding: 40px 20px;">
                    <div style="text-align: center; margin-bottom: 32px;">
                        <div style="font-size: 48px; margin-bottom: 12px;">🐷</div>
                        <h1 style="font-size: 28px; font-weight: 800; margin-bottom: 8px;">로그인</h1>
                        <p style="font-size: 14px; color: #999;">AI Money Friends에 오신 것을 환영합니다!</p>
                    </div>
                </div>
                """
            ).strip(),
            unsafe_allow_html=True,
        )

        tab1, tab2 = st.tabs(["간편 로그인", "아이디 로그인"])

        with tab1:
            st.info("간편 로그인 기능은 준비 중입니다 🔧")
            _social_button("🟡 카카오로 시작하기", bg="#FEE500", fg="#000000")
            _social_button("🟢 네이버로 시작하기", bg="#03C75A", fg="#FFFFFF")
            _social_button("⚪ 구글로 시작하기", bg="#FFFFFF", fg="#111827", border="#E8E8E8")

        with tab2:
            username = st.text_input("아이디", placeholder="아이디를 입력하세요", key="login_username")
            password = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요", key="login_password")

            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

            if st.button("로그인 🚀", use_container_width=True, type="primary", key="login_submit"):
                if not username or not password:
                    st.error("아이디와 비밀번호를 입력해주세요")
                else:
                    user = db.users.find_one({"username": username})
                    pw_hash = None
                    if user:
                        pw_hash = user.get("password_hash") or user.get("password")

                    if user and pw_hash and verify_password(password, pw_hash):
                        uid = user.get("_id") or user.get("id")
                        st.session_state["logged_in"] = True
                        st.session_state["user_id"] = uid
                        st.session_state["user_name"] = user.get("name") or username
                        st.session_state["user_type"] = user.get("user_type") or "child"
                        st.session_state["username"] = user.get("username") or username
                        if (user.get("user_type") or "") == "parent":
                            st.session_state["invite_code"] = user.get("invite_code")

                        st.success(f"환영합니다, {st.session_state['user_name']}님! 🎉")
                        st.balloons()

                        # 현재 레포에 메인 페이지는 대시보드로 통일
                        st.switch_page("pages/1_🏠_대시보드.py")
                    else:
                        st.error("아이디 또는 비밀번호가 올바르지 않습니다")

            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                if st.button("아이디 찾기", use_container_width=True, key="find_id"):
                    st.info("준비 중입니다")
            with c2:
                if st.button("비밀번호 찾기", use_container_width=True, key="find_pw"):
                    st.info("준비 중입니다")

        st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
        st.markdown(
            _dedent(
                """
                <div style="text-align: center;">
                    <p style="font-size: 14px; color: #999;">아직 계정이 없나요?</p>
                </div>
                """
            ).strip(),
            unsafe_allow_html=True,
        )
        if st.button("회원가입하러 가기", use_container_width=True, key="goto_signup"):
            st.switch_page("pages/2_✍️_회원가입.py")


if __name__ == "__main__":
    main()

