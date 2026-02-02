import streamlit as st

from database.db_manager import DatabaseManager
from utils.menu import render_sidebar_menu, hide_sidebar_navigation


def _guard_child() -> bool:
    if not st.session_state.get("logged_in"):
        st.switch_page("app.py")
        return False
    if st.session_state.get("user_type") != "child":
        st.error("아이 계정에서만 사용할 수 있어요.")
        return False
    return True


def _level_from_xp(xp: int) -> tuple[int, int, int]:
    # 간단 레벨: 0~9 = Lv1, 10~29=Lv2, 30~59=Lv3, 60~99=Lv4, ...
    thresholds = [0, 10, 30, 60, 100, 150, 220]
    level = 1
    for i, t in enumerate(thresholds):
        if xp >= t:
            level = i + 1
    next_t = thresholds[level] if level < len(thresholds) else thresholds[-1] + 100
    prev_t = thresholds[level - 1] if level - 1 < len(thresholds) else thresholds[-1]
    return level, prev_t, next_t


def main():
    if not _guard_child():
        return

    hide_sidebar_navigation()
    db = DatabaseManager()

    user_id = int(st.session_state.get("user_id"))
    user_name = st.session_state.get("user_name", "사용자")
    render_sidebar_menu(user_id, user_name, "child")

    db.award_badges_if_needed(user_id)

    st.title("🏆 내 성장")
    st.caption("활동/미션을 완료할수록 레벨이 오르고 배지를 모을 수 있어요.")

    xp = db.get_xp(user_id)
    level, prev_t, next_t = _level_from_xp(xp)
    prog = 0 if next_t == prev_t else min(1.0, (xp - prev_t) / (next_t - prev_t))

    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,#111827,#374151); color:white; border-radius:18px; padding:18px 16px;">
            <div style="font-weight:900; opacity:0.9;">Lv.{level} · {user_name}</div>
            <div style="font-size:34px; font-weight:900; letter-spacing:-0.6px; margin-top:4px;">
                XP {xp}
            </div>
            <div style="margin-top:8px;">다음 레벨까지 {max(0, next_t - xp)} XP</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(prog)

    st.divider()
    st.subheader("배지")
    badges = db.get_user_badges(user_id)
    if not badges:
        st.caption("아직 배지가 없어요. 미션을 완료해보자!")
    else:
        for b in badges[:20]:
            icon = b.get("icon") or "🏅"
            st.markdown(f"- {icon} **{b.get('title')}** · {b.get('description')}")

    st.divider()
    st.subheader("추천 액션")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("✅ 미션 하러 가기", use_container_width=True):
            st.switch_page("pages/10_✅_미션.py")
    with c2:
        if st.button("🎯 목표 저축하기", use_container_width=True):
            st.switch_page("pages/8_🎯_저축_목표.py")
    with c3:
        if st.button("📚 경제 교실", use_container_width=True):
            st.switch_page("pages/12_📚_경제_교실.py")


if __name__ == "__main__":
    main()

