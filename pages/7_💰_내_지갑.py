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


def main():
    if not _guard_child():
        return

    hide_sidebar_navigation()
    db = DatabaseManager()

    user_id = int(st.session_state.get("user_id"))
    user_name = st.session_state.get("user_name", "사용자")
    render_sidebar_menu(user_id, user_name, "child")

    st.title("💰 내 지갑")
    behaviors = db.get_user_behaviors(user_id, limit=5000)

    total_allowance = sum((b.get("amount") or 0) for b in behaviors if b.get("behavior_type") == "allowance")
    total_saving = sum((b.get("amount") or 0) for b in behaviors if b.get("behavior_type") == "saving")
    total_spend = sum(
        (b.get("amount") or 0)
        for b in behaviors
        if b.get("behavior_type") in ("planned_spending", "impulse_buying")
    )
    balance = total_allowance - total_saving - total_spend

    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,#667eea,#764ba2); color:white; border-radius:18px; padding:18px 16px;">
            <div style="font-weight:800; opacity:0.9;">현재 잔액</div>
            <div style="font-size:40px; font-weight:900; letter-spacing:-0.6px; margin-top:4px; line-height:1.05;">{int(balance):,}원</div>
            <div style="margin-top:6px; opacity:0.9; font-weight:700; font-size:13px;">
                받은 용돈 {int(total_allowance):,}원 · 저축 {int(total_saving):,}원 · 지출 {int(total_spend):,}원
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()
    st.subheader("최근 거래")
    if not behaviors:
        st.caption("아직 거래 기록이 없어요.")
    else:
        rows = []
        for b in behaviors[:50]:
            t = b.get("behavior_type")
            amt = float(b.get("amount") or 0)
            sign = "+" if t == "allowance" else "-"
            rows.append(
                {
                    "일시": b.get("timestamp"),
                    "구분": t,
                    "금액": f"{sign}{int(amt):,}",
                    "카테고리": b.get("category") or "",
                    "메모": b.get("description") or "",
                }
            )
        st.dataframe(rows, use_container_width=True, hide_index=True)

    st.divider()
    # ✅ 모바일 우선: 3열 → 2열 + 단일
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📝 용돈 요청", use_container_width=True):
            st.switch_page("pages/9_📝_용돈_요청.py")
    with c2:
        if st.button("🎯 저축 목표", use_container_width=True):
            st.switch_page("pages/8_🎯_저축_목표.py")
    if st.button("✅ 미션", use_container_width=True):
        st.switch_page("pages/10_✅_미션.py")


if __name__ == "__main__":
    main()

