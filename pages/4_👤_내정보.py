import streamlit as st

from database.db_manager import DatabaseManager
from utils.menu import render_sidebar_menu, hide_sidebar_navigation


def _guard_login() -> bool:
    if not st.session_state.get("logged_in"):
        st.switch_page("app.py")
        return False
    return True


def main():
    if not _guard_login():
        return

    hide_sidebar_navigation()

    user_id = st.session_state.get("user_id")
    user_name = st.session_state.get("user_name", "사용자")
    user_type = st.session_state.get("user_type", "child")
    username = st.session_state.get("username", "")

    db = DatabaseManager()
    user = db.get_user_by_id(int(user_id)) if user_id else None

    render_sidebar_menu(user_id, user_name, user_type)

    # 구버전 페이지 → 새 구조로 이동
    st.switch_page("pages/6_⚙️_설정.py")

    st.subheader("내 정보")
    c1, c2 = st.columns(2)
    with c1:
        st.write(f"- 이름: **{user.get('name') if user else user_name}**")
        if username:
            st.write(f"- 아이디: **{username}**")
        st.write(f"- 유형: **{user.get('user_type') if user else user_type}**")
    with c2:
        parent_code = (user or {}).get("parent_code", "")
        if parent_code:
            st.write("- 부모 코드:")
            st.code(parent_code, language=None)
            st.caption("자녀 계정 가입 시 이 코드를 입력하면 연결됩니다.")

    st.divider()

    st.subheader("정보 변경")
    with st.form("update_profile"):
        new_name = st.text_input("이름 변경", value=(user.get("name") if user else user_name) or "")
        pw1 = st.text_input("새 비밀번호(선택)", type="password", placeholder="4자 이상")
        pw2 = st.text_input("새 비밀번호 확인", type="password")
        submitted = st.form_submit_button("저장", use_container_width=True)

    if submitted:
        if pw1 or pw2:
            if pw1 != pw2:
                st.error("비밀번호가 일치하지 않습니다.")
                return
            if len(pw1) < 4:
                st.error("비밀번호는 최소 4자 이상이어야 합니다.")
                return

        ok = db.update_user_info(int(user_id), name=new_name.strip() if new_name else None, password=pw1 if pw1 else None)
        if ok:
            st.success("저장했습니다.")
            # 세션 반영
            if new_name:
                st.session_state["user_name"] = new_name.strip()
            st.rerun()
        else:
            st.info("변경된 내용이 없거나 저장에 실패했습니다.")

    st.divider()
    st.subheader("계정")
    if st.button("🚪 로그아웃", use_container_width=True):
        for key in list(st.session_state.keys()):
            if key not in ["current_auth_screen"]:
                del st.session_state[key]
        st.session_state.logged_in = False
        st.session_state.current_auth_screen = "login"
        st.switch_page("app.py")

    if st.button("🏠 메인으로 돌아가기", use_container_width=True):
        st.switch_page("app.py")


if __name__ == "__main__":
    main()

