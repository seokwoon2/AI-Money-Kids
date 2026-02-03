import streamlit as st

from datetime import datetime

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

    render_sidebar_menu(user_id, user_name, user_type)

    if user_type != "parent":
        st.error("부모님만 접근할 수 있어요.")
        st.stop()

    parent = db.get_user_by_id(user_id)
    parent_code = (parent or {}).get("parent_code", "")
    children = db.get_users_by_parent_code(parent_code) if parent_code else []

    st.title("👶 자녀 관리")
    st.caption("자녀 계정 연결/현황/기록을 한 곳에서 관리해요.")

    # ✅ 모바일 우선: 3열 대신 2열(2줄)
    c1, c2 = st.columns(2)
    with c1:
        st.metric("연결된 자녀", f"{len(children)}명")
    with c2:
        st.metric("오늘", datetime.now().strftime("%Y.%m.%d"))
    st.metric("부모 코드", parent_code or "없음")

    st.divider()

    if not children:
        st.info("아직 연결된 자녀가 없어요. 자녀가 가입할 때 부모 코드를 입력하면 자동으로 연결돼요.")
        st.code(parent_code or "부모 코드 없음", language=None)
        return

    child_label_to_id = {f"{c['name']} ({c['username']})": c["id"] for c in children}
    selected_label = st.selectbox("자녀 선택", list(child_label_to_id.keys()))
    child_id = int(child_label_to_id[selected_label])
    child = db.get_user_by_id(child_id)

    behaviors = db.get_user_behaviors(child_id, limit=2000)
    total_allowance = sum((b.get("amount") or 0) for b in behaviors if b.get("behavior_type") == "allowance")
    total_saving = sum((b.get("amount") or 0) for b in behaviors if b.get("behavior_type") == "saving")
    total_spend = sum(
        (b.get("amount") or 0)
        for b in behaviors
        if b.get("behavior_type") in ("planned_spending", "impulse_buying")
    )
    balance = total_allowance - total_saving - total_spend
    stats = db.get_child_stats(child_id)

    # ✅ 모바일 우선: 4열 → 2열(2줄)
    m1, m2 = st.columns(2)
    with m1:
        st.metric("잔액(추정)", f"{int(balance):,}원")
    with m2:
        st.metric("총 용돈(지급)", f"{int(total_allowance):,}원")
    m3, m4 = st.columns(2)
    with m3:
        st.metric("총 저축", f"{int(stats.get('total_savings') or 0):,}원")
    with m4:
        st.metric("활동 수", f"{int(stats.get('activity_count') or 0)}개")

    st.divider()

    st.subheader("관리")
    a1, a2 = st.columns(2)
    with a1:
        with st.form("rename_child"):
            new_name = st.text_input("자녀 이름 변경", value=child.get("name", ""))
            submit_rename = st.form_submit_button("이름 변경", use_container_width=True)
        if submit_rename:
            if not new_name.strip():
                st.error("이름을 입력하세요.")
            else:
                ok = db.update_user_name(child_id, new_name.strip())
                st.success("이름을 변경했어요." if ok else "변경에 실패했어요.")
                st.rerun()

    with a2:
        with st.form("reset_child_password"):
            st.caption("비밀번호 재설정(부모용)")
            new_pw = st.text_input("새 비밀번호", type="password", placeholder="4자 이상")
            submit_pw = st.form_submit_button("비밀번호 재설정", use_container_width=True)
        if submit_pw:
            if not new_pw or len(new_pw) < 4:
                st.error("비밀번호는 최소 4자 이상이어야 해요.")
            else:
                ok = db.update_user_password(child_id, new_pw)
                st.success("비밀번호를 재설정했어요." if ok else "재설정에 실패했어요.")

    st.divider()
    st.subheader("최근 기록")
    if not behaviors:
        st.caption("아직 기록이 없어요.")
    else:
        recent = behaviors[:20]
        st.dataframe(
            [
                {
                    "일시": r.get("timestamp"),
                    "유형": r.get("behavior_type"),
                    "금액": int(r.get("amount") or 0),
                    "카테고리": r.get("category") or "",
                    "내용": r.get("description") or "",
                }
                for r in recent
            ],
            use_container_width=True,
            hide_index=True,
        )

    st.divider()
    b1, b2 = st.columns(2)
    with b1:
        if st.button("💵 용돈 관리로 이동", use_container_width=True):
            st.switch_page("pages/3_💵_용돈_관리.py")
    with b2:
        if st.button("🏠 대시보드", use_container_width=True):
            st.switch_page("pages/1_🏠_대시보드.py")


if __name__ == "__main__":
    main()

