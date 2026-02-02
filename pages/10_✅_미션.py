import streamlit as st

from datetime import date

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
    db.seed_default_missions_and_badges()

    user_id = int(st.session_state.get("user_id"))
    user_name = st.session_state.get("user_name", "사용자")
    user_type = st.session_state.get("user_type", "child")

    render_sidebar_menu(user_id, user_name, user_type)

    st.title("✅ 미션")
    st.caption("일일/주간/커스텀 미션을 진행하고 보상을 받아요.")

    today = date.today().isoformat()

    if user_type == "child":
        db.assign_daily_missions_if_needed(user_id, today)
        tab_daily, tab_history = st.tabs(["📌 오늘의 미션", "🗂️ 기록"])

        with tab_daily:
            missions = db.get_missions_for_user(user_id, date_str=today, active_only=True)
            if not missions:
                st.caption("오늘의 미션이 없어요.")
            else:
                for m in missions:
                    with st.container(border=True):
                        st.markdown(f"**{m.get('title')}**")
                        if m.get("description"):
                            st.caption(m.get("description"))
                        st.caption(f"난이도: {m.get('difficulty')} · 보상: {int(m.get('reward_amount') or 0):,}원")
                        if st.button("완료!", key=f"complete_{m['id']}", use_container_width=True, type="primary"):
                            ok = db.complete_mission(int(m["id"]))
                            if ok:
                                reward = float(m.get("reward_amount") or 0)
                                if reward > 0:
                                    db.save_behavior_v2(user_id, "allowance", reward, description="미션 보상", category="미션")
                                db.create_notification(user_id, "미션 완료!", f"보상 {int(reward):,}원을 받았어요.", level="success")
                                db.award_badges_if_needed(user_id)
                                st.balloons()
                                st.rerun()
                            else:
                                st.info("이미 완료했거나 처리할 수 없어요.")

        with tab_history:
            # completed missions (최근 30개)
            conn = db._get_connection()
            cur = conn.cursor()
            try:
                cur.execute(
                    """
                    SELECT a.assigned_date, a.completed_at, t.title, t.reward_amount
                    FROM mission_assignments a
                    JOIN mission_templates t ON a.template_id = t.id
                    WHERE a.user_id = ? AND a.status = 'completed'
                    ORDER BY a.completed_at DESC
                    LIMIT 30
                    """,
                    (user_id,),
                )
                rows = cur.fetchall()
            finally:
                conn.close()
            if not rows:
                st.caption("아직 완료한 미션이 없어요.")
            else:
                st.dataframe(
                    [
                        {
                            "완료일": r.get("assigned_date"),
                            "미션": r.get("title"),
                            "보상(원)": int(r.get("reward_amount") or 0),
                            "완료시각": r.get("completed_at"),
                        }
                        for r in rows
                    ],
                    use_container_width=True,
                    hide_index=True,
                )

    else:
        # 부모: 커스텀 미션 생성/관리(간단)
        parent = db.get_user_by_id(user_id)
        parent_code = (parent or {}).get("parent_code", "")
        children = db.get_users_by_parent_code(parent_code) if parent_code else []

        st.subheader("✨ 커스텀 미션 만들기")
        if not children:
            st.info("연결된 자녀가 없어요. 자녀가 가입할 때 부모 코드를 입력하면 자동 연결됩니다.")
            st.code(parent_code or "부모 코드 없음", language=None)
            return

        child_label_to_id = {f"{c['name']} ({c['username']})": c["id"] for c in children}
        selected = st.selectbox("자녀 선택", list(child_label_to_id.keys()))
        child_id = int(child_label_to_id[selected])

        with st.form("create_custom_mission"):
            title = st.text_input("미션 제목", placeholder="예: 이번 주 3,000원 저축하기")
            desc = st.text_input("설명(선택)", placeholder="예: 저축(saving) 기록을 3번 남겨요")
            difficulty = st.selectbox("난이도", ["easy", "normal", "hard"])
            reward = st.number_input("보상(원)", min_value=0, step=100, value=500)
            submitted = st.form_submit_button("미션 추가", use_container_width=True, type="primary")

        if submitted:
            if not title.strip():
                st.error("제목을 입력하세요.")
            else:
                tid = db.create_custom_mission(parent_code, title.strip(), desc or None, difficulty, float(reward), user_id)
                # 바로 자녀에게 할당(custom)
                conn = db._get_connection()
                cur = conn.cursor()
                try:
                    cur.execute(
                        """
                        INSERT INTO mission_assignments (user_id, template_id, cycle, assigned_date, status)
                        VALUES (?, ?, 'custom', ?, 'active')
                        """,
                        (child_id, tid, today),
                    )
                    conn.commit()
                finally:
                    conn.close()
                db.create_notification(child_id, "새 미션이 도착했어요!", title.strip(), level="info")
                st.success("커스텀 미션을 만들고 자녀에게 보냈어요!")

        st.divider()
        st.subheader("내 커스텀 미션 템플릿")
        custom = db.get_custom_missions(parent_code)
        if not custom:
            st.caption("아직 커스텀 미션이 없어요.")
        else:
            st.dataframe(
                [
                    {
                        "제목": m.get("title"),
                        "난이도": m.get("difficulty"),
                        "보상(원)": int(m.get("reward_amount") or 0),
                        "생성일": m.get("created_at"),
                    }
                    for m in custom[:30]
                ],
                use_container_width=True,
                hide_index=True,
            )


if __name__ == "__main__":
    main()

