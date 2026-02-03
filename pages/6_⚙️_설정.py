import streamlit as st

from datetime import date

from database.db_manager import DatabaseManager
from utils.menu import render_sidebar_menu, hide_sidebar_navigation
from utils.characters import get_character_catalog, get_character_by_code, get_skins_for_character, get_skin_by_code


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
        # ✅ 모바일 우선: 프로필은 세로 스택(파일 업로더가 옆에 있으면 너무 좁아짐)
        st.write(f"- 이름: **{(user or {}).get('name', user_name)}**")
        if username:
            st.write(f"- 아이디: **{username}**")
        st.write(f"- 유형: **{(user or {}).get('user_type', user_type)}**")
        if (user or {}).get("birth_date"):
            st.write(f"- 생년월일: **{(user or {}).get('birth_date')}**")
        if (user or {}).get("character_code"):
            c = get_character_by_code((user or {}).get("character_code"))
            if c:
                st.write(f"- 캐릭터: **{c.get('emoji','🐾')} {c.get('name')}** ({c.get('role')})")
        st.write("- 부모 코드:")
        st.code((user or {}).get("parent_code", ""), language=None)

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

        # ✅ 생년월일 관리(특히 아이 계정)
        st.divider()
        st.subheader("생년월일")
        current_bd = (user or {}).get("birth_date") or ""
        default_bd = None
        try:
            if current_bd:
                y, m, d = [int(x) for x in str(current_bd).split("-")]
                default_bd = date(y, m, d)
        except Exception:
            default_bd = None
        with st.form("update_birth_date"):
            bd = st.date_input(
                "생년월일",
                value=default_bd,
                min_value=date(1900, 1, 1),
                max_value=date.today(),
            )
            submitted_bd = st.form_submit_button("저장", use_container_width=True)
        if submitted_bd:
            if not bd:
                st.error("생년월일을 선택해주세요.")
            else:
                if hasattr(db, "update_user_birth_date"):
                    ok = db.update_user_birth_date(user_id, bd.isoformat())
                    if ok:
                        st.success("생년월일을 저장했어요.")
                        st.rerun()
                    else:
                        st.error("저장에 실패했어요.")
                else:
                    st.error("DB 업데이트 기능이 준비되지 않았어요. 앱을 업데이트해주세요.")

        # ✅ 캐릭터 관리
        st.divider()
        st.subheader("내 캐릭터")
        catalog = get_character_catalog()
        current_code = (user or {}).get("character_code")
        options = ["(선택 안 함)"] + [f"{c.get('emoji','🐾')} {c.get('name')} · {c.get('role')} [{c.get('code')}]" for c in catalog]
        current_idx = 0
        if current_code:
            for i, c in enumerate(catalog, start=1):
                if c.get("code") == current_code:
                    current_idx = i
                    break
        picked = st.selectbox("캐릭터 선택", options=options, index=current_idx, key="settings_character_pick")
        if st.button("캐릭터 저장", use_container_width=True, key="settings_character_save"):
            code = None
            if picked != "(선택 안 함)":
                try:
                    code = picked.split("[")[-1].split("]")[0].strip()
                except Exception:
                    code = None
            if hasattr(db, "update_user_character_code"):
                ok = db.update_user_character_code(user_id, code)
                if ok:
                    st.success("캐릭터를 저장했어요.")
                    st.rerun()
                else:
                    st.error("저장에 실패했어요.")
            else:
                st.error("DB 업데이트 기능이 준비되지 않았어요. 앱을 업데이트해주세요.")

        # 캐릭터 별명
        st.subheader("캐릭터 이름(별명)")
        current_nick = (user or {}).get("character_nickname") or ""
        with st.form("update_character_nickname"):
            new_nick = st.text_input("별명", value=current_nick, placeholder="예: 모치카짱")
            submitted_nick = st.form_submit_button("저장", use_container_width=True)
        if submitted_nick:
            if hasattr(db, "update_user_character_nickname"):
                ok = db.update_user_character_nickname(user_id, new_nick.strip())
                st.success("저장했어요." if ok else "저장에 실패했어요.")
                if ok:
                    st.rerun()
            else:
                st.error("DB 업데이트 기능이 준비되지 않았어요. 앱을 업데이트해주세요.")

        # 스킨(해금/선택)
        st.subheader("스킨")
        current = db.get_user_by_id(user_id) or {}
        ccode = (current or {}).get("character_code")
        if not ccode:
            st.caption("캐릭터를 먼저 선택해주세요.")
        else:
            unlocked = set(db.get_unlocked_skins(user_id)) if hasattr(db, "get_unlocked_skins") else set()
            skins = get_skins_for_character(ccode)
            # 기본 스킨은 항상 보이게
            options = []
            option_to_code = {}
            for s in skins:
                code = s.get("code")
                req = int(s.get("required_level") or 9999)
                is_unlocked = code in unlocked or req <= 1
                label = f"{s.get('emoji','🎨')} {s.get('name')} (Lv.{req})" + ("" if is_unlocked else " 🔒")
                options.append(label)
                option_to_code[label] = code
            current_skin_code = (current or {}).get("character_skin_code") or f"{ccode}:default"
            current_label = None
            for lbl, code in option_to_code.items():
                if code == current_skin_code:
                    current_label = lbl
                    break
            idx = options.index(current_label) if current_label in options else 0
            picked_lbl = st.selectbox("내 스킨", options=options, index=idx, key="settings_skin_pick")
            picked_code = option_to_code.get(picked_lbl)
            req_lv = 1
            try:
                s = get_skin_by_code(picked_code)
                req_lv = int((s or {}).get("required_level") or 1)
            except Exception:
                req_lv = 1
            if picked_code and (picked_code in unlocked or req_lv <= 1):
                if st.button("스킨 적용", use_container_width=True, key="apply_skin_btn"):
                    if hasattr(db, "update_user_character_skin_code"):
                        ok = db.update_user_character_skin_code(user_id, picked_code)
                        st.success("스킨을 적용했어요!" if ok else "적용에 실패했어요.")
                        if ok:
                            st.rerun()
                    else:
                        st.error("DB 업데이트 기능이 준비되지 않았어요. 앱을 업데이트해주세요.")
            else:
                st.info("아직 해금되지 않은 스킨이에요. 레벨을 올려보세요!")

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

