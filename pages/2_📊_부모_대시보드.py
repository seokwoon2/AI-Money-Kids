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

    user_id = st.session_state.get("user_id")
    user_name = st.session_state.get("user_name", "사용자")
    user_type = st.session_state.get("user_type", "parent")

    render_sidebar_menu(user_id, user_name, user_type)

    if user_type != "parent":
        st.error("이 메뉴는 부모님 계정에서만 사용할 수 있어요.")
        if st.button("🏠 메인으로 돌아가기", use_container_width=True):
            st.switch_page("app.py")
        return

    parent = db.get_user_by_id(int(user_id)) if user_id else None
    parent_code = parent.get("parent_code") if parent else ""
    children = db.get_users_by_parent_code(parent_code) if parent_code else []

    # 구버전 페이지 → 새 구조로 이동
    st.switch_page("pages/2_👶_자녀_관리.py")

    # 상단 요약
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("연결된 자녀", f"{len(children)}명")
    with c2:
        st.metric("부모 코드", parent_code or "없음")
    with c3:
        st.metric("오늘", datetime.now().strftime("%Y.%m.%d"))

    st.divider()

    if not children:
        st.info("아직 연결된 자녀가 없어요. 자녀 계정 가입 시 부모 코드를 입력하면 자동으로 연결됩니다.")
        st.code(parent_code or "부모 코드 없음", language=None)
        st.caption("부모 코드를 복사해 자녀에게 알려주세요.")
        if st.button("💵 용돈 관리로 이동", use_container_width=True):
            st.switch_page("pages/9_💵_용돈_관리.py")
        return

    # 자녀 선택
    child_label_to_id = {f"{c['name']} ({c['username']})": c["id"] for c in children}
    selected_label = st.selectbox("자녀 선택", list(child_label_to_id.keys()), label_visibility="collapsed")
    child_id = int(child_label_to_id[selected_label])
    child = db.get_user_by_id(child_id)

    if not child:
        st.error("선택한 자녀 정보를 불러오지 못했어요.")
        return

    # 자녀 현황
    stats = db.get_child_stats(child_id)
    behaviors = db.get_user_behaviors(child_id, limit=200)
    total_allowance = sum((b.get("amount") or 0) for b in behaviors if b.get("behavior_type") == "allowance")
    total_saving = sum((b.get("amount") or 0) for b in behaviors if b.get("behavior_type") == "saving")
    total_spend = sum((b.get("amount") or 0) for b in behaviors if b.get("behavior_type") in ("planned_spending", "impulse_buying"))
    balance = total_allowance - total_saving - total_spend

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("잔액(추정)", f"{int(balance):,}원")
    with m2:
        st.metric("총 용돈(지급)", f"{int(total_allowance):,}원")
    with m3:
        st.metric("총 저축", f"{int(stats.get('total_savings') or 0):,}원")
    with m4:
        st.metric("활동 수", f"{int(stats.get('activity_count') or 0)}개")

    st.divider()

    # 관리 액션
    st.subheader("관리")
    a1, a2 = st.columns(2)
    with a1:
        with st.form("rename_child"):
            new_name = st.text_input("자녀 이름 변경", value=child.get("name", ""), placeholder="새 이름", label_visibility="visible")
            submit_rename = st.form_submit_button("이름 변경", use_container_width=True)
        if submit_rename:
            if not new_name.strip():
                st.error("이름을 입력하세요.")
            else:
                ok = db.update_user_name(child_id, new_name.strip())
                if ok:
                    st.success("이름을 변경했어요.")
                    st.rerun()
                else:
                    st.error("이름 변경에 실패했어요.")

    with a2:
        with st.form("reset_child_password"):
            st.caption("비밀번호 재설정(부모용)")
            new_pw = st.text_input("새 비밀번호", type="password", placeholder="4자 이상", label_visibility="visible")
            submit_pw = st.form_submit_button("비밀번호 재설정", use_container_width=True)
        if submit_pw:
            if not new_pw or len(new_pw) < 4:
                st.error("비밀번호는 최소 4자 이상이어야 해요.")
            else:
                ok = db.update_user_password(child_id, new_pw)
                if ok:
                    st.success("비밀번호를 재설정했어요.")
                else:
                    st.error("비밀번호 재설정에 실패했어요.")

    st.divider()

    # 최근 기록
    st.subheader("최근 활동")
    if not behaviors:
        st.caption("아직 기록된 활동이 없어요.")
    else:
        # 최신 15개만 표시
        recent = behaviors[:15]
        rows = []
        for b in recent:
            t = b.get("timestamp")
            rows.append(
                {
                    "일시": t,
                    "유형": b.get("behavior_type"),
                    "금액": int(b.get("amount") or 0),
                    "내용": b.get("description") or "",
                }
            )
        st.dataframe(rows, use_container_width=True, hide_index=True)

    st.divider()
    b1, b2 = st.columns(2)
    with b1:
        if st.button("💵 용돈/저축 관리로 이동", use_container_width=True):
            st.switch_page("pages/9_💵_용돈_관리.py")
    with b2:
        if st.button("🏠 메인 대시보드", use_container_width=True):
            st.switch_page("app.py")

    st.info("현재는 메인 대시보드에서 자녀 현황을 확인할 수 있어요.")
    if st.button("🏠 메인 대시보드로 돌아가기", use_container_width=True):
        st.switch_page("app.py")


if __name__ == "__main__":
    main()

