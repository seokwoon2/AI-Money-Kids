import streamlit as st

from database.db_manager import DatabaseManager
from utils.menu import render_sidebar_menu, hide_sidebar_navigation
from utils.ui import render_page_header, section_label


def _guard_child() -> bool:
    if not st.session_state.get("logged_in"):
        st.switch_page("app.py")
        return False
    if st.session_state.get("user_type") != "child":
        st.error("아이 계정에서만 사용할 수 있어요.")
        return False
    return True


def main():
    if not _guard_child():
        return

    hide_sidebar_navigation()
    db = DatabaseManager()

    user_id = int(st.session_state.get("user_id"))
    user_name = st.session_state.get("user_name", "사용자")
    render_sidebar_menu(user_id, user_name, "child")

    render_page_header("🎯 저축 목표", "목표를 만들고, 목표별로 저축을 쌓아가요.")

    section_label("목표 만들기")
    with st.container(border=True):
        with st.form("create_goal"):
            title = st.text_input("목표 이름", placeholder="예: 자전거 사기")
            target = st.number_input("목표 금액(원)", min_value=1000, step=1000, value=50000)
            submitted = st.form_submit_button("목표 추가", use_container_width=True, type="primary")
    if submitted:
        if not title.strip():
            st.error("목표 이름을 입력하세요.")
        else:
            db.create_goal(user_id, title.strip(), float(target))
            st.success("목표를 만들었어요!")
            st.rerun()

    st.divider()

    goals = db.get_goals(user_id, active_only=False)
    if not goals:
        st.caption("아직 목표가 없어요.")
        return

    section_label("내 목표")
    active_goals = [g for g in goals if int(g.get("is_active") or 0) == 1]
    archived_goals = [g for g in goals if int(g.get("is_active") or 0) == 0]

    def _render_goal(g):
        gid = int(g["id"])
        title = g.get("title")
        target = float(g.get("target_amount") or 0)
        saved = db.get_goal_progress(gid)
        pct = 0 if target <= 0 else min(1.0, saved / target)
        left = max(0.0, target - saved)

        with st.container(border=True):
            st.markdown(f"### {title}")
            st.progress(pct)
            st.caption(f"{int(saved):,}원 / {int(target):,}원 · 남은 금액 {int(left):,}원")

            # ✅ 모바일 우선: 3컬럼 대신 세로 스택 (폼/버튼이 좁아지는 문제 방지)
            with st.form(f"add_contrib_{gid}"):
                amt = st.number_input("저축 추가(원)", min_value=100, step=100, value=1000, key=f"amt_{gid}")
                note = st.text_input("메모(선택)", key=f"note_{gid}")
                add = st.form_submit_button("저축하기", use_container_width=True, type="primary")
            if add:
                db.add_goal_contribution(gid, float(amt), note or None)
                # 저축 행동도 같이 기록(지갑/리포트 연동)
                db.save_behavior_v2(user_id, "saving", float(amt), description="목표 저축", category="저축")
                st.balloons()
                st.rerun()

            if pct >= 1.0:
                st.success("목표 달성! 🎉")
            a1, a2 = st.columns(2)
            with a1:
                if st.button("비활성/보관", key=f"archive_{gid}", use_container_width=True):
                    db.set_goal_active(gid, False)
                    st.rerun()
            with a2:
                if st.button("활성화", key=f"activate_{gid}", use_container_width=True, disabled=int(g.get("is_active") or 0) == 1):
                    db.set_goal_active(gid, True)
                    st.rerun()

    if active_goals:
        st.markdown("#### 진행 중")
        for g in active_goals:
            _render_goal(g)
    if archived_goals:
        st.markdown("#### 보관함")
        for g in archived_goals[:5]:
            _render_goal(g)


if __name__ == "__main__":
    main()

