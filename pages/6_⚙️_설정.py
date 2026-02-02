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
    db = DatabaseManager()

    user_id = int(st.session_state.get("user_id"))
    user_name = st.session_state.get("user_name", "사용자")
    user_type = st.session_state.get("user_type", "child")
    username = st.session_state.get("username", "")

    render_sidebar_menu(user_id, user_name, user_type)

    user = db.get_user_by_id(user_id)

    st.title("⚙️ 설정")
    tab_profile, tab_notify, tab_security = st.tabs(["👤 프로필", "🔔 알림", "🔒 보안"])

    with tab_profile:
        st.subheader("프로필")
        c1, c2 = st.columns([1.2, 0.8])
        with c1:
            st.write(f"- 이름: **{(user or {}).get('name', user_name)}**")
            if username:
                st.write(f"- 아이디: **{username}**")
            st.write(f"- 유형: **{(user or {}).get('user_type', user_type)}**")
            st.write("- 부모 코드:")
            st.code((user or {}).get("parent_code", ""), language=None)
        with c2:
            st.caption("프로필 사진(임시)")
            st.file_uploader("사진 업로드", type=["png", "jpg", "jpeg"])
            st.caption("※ 현재는 저장소 연동이 없어 업로드는 미리보기용입니다.")

        st.divider()
        with st.form("update_name"):
            new_name = st.text_input("이름 변경", value=(user or {}).get("name", user_name))
            submitted = st.form_submit_button("저장", use_container_width=True)
        if submitted:
            ok = db.update_user_name(user_id, new_name.strip())
            if ok:
                st.session_state["user_name"] = new_name.strip()
                st.success("이름을 변경했어요.")
                st.rerun()
            else:
                st.error("변경에 실패했어요.")

    with tab_notify:
        st.subheader("알림")
        st.caption("알림은 `notifications` 테이블에 저장됩니다.")

        unread = db.get_notifications(user_id, unread_only=True, limit=20)
        if not unread:
            st.success("읽지 않은 알림이 없어요.")
        else:
            for n in unread:
                level = n.get("level", "info")
                title = n.get("title", "")
                body = n.get("body") or ""
                if level == "success":
                    st.success(f"**{title}**\n\n{body}")
                elif level == "warning":
                    st.warning(f"**{title}**\n\n{body}")
                else:
                    st.info(f"**{title}**\n\n{body}")

                if st.button("읽음 처리", key=f"read_{n['id']}"):
                    db.mark_notification_read(int(n["id"]))
                    st.rerun()

    with tab_security:
        st.subheader("비밀번호 변경")
        with st.form("change_password"):
            pw1 = st.text_input("새 비밀번호", type="password", placeholder="4자 이상")
            pw2 = st.text_input("새 비밀번호 확인", type="password")
            submitted = st.form_submit_button("변경", use_container_width=True)
        if submitted:
            if pw1 != pw2:
                st.error("비밀번호가 일치하지 않습니다.")
            elif not pw1 or len(pw1) < 4:
                st.error("비밀번호는 최소 4자 이상이어야 합니다.")
            else:
                ok = db.update_user_password(user_id, pw1)
                st.success("비밀번호를 변경했어요." if ok else "변경에 실패했어요.")

        st.divider()
        if st.button("🚪 로그아웃", use_container_width=True):
            for key in list(st.session_state.keys()):
                if key not in ["current_auth_screen"]:
                    del st.session_state[key]
            st.session_state.logged_in = False
            st.session_state.current_auth_screen = "login"
            st.switch_page("app.py")


if __name__ == "__main__":
    main()

