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
    st.switch_page("pages/5_📊_리포트.py")

    # 이번 달 요약
    monthly = db.get_children_behavior_stats_this_month(parent_code) if parent_code else {"monthly_total": 0, "yesterday_total": 0}
    monthly_total = int(monthly.get("monthly_total") or 0)
    yesterday_total = int(monthly.get("yesterday_total") or 0)

    a, b, c = st.columns(3)
    with a:
        st.metric("이번달 가족 저축", f"{monthly_total:,}원")
    with b:
        st.metric("어제 저축", f"{yesterday_total:,}원")
    with c:
        st.metric("연결된 자녀", f"{len(children)}명")

    st.divider()

    # 월별 저축 (최근 6개월)
    st.subheader("최근 6개월 저축 추이")
    rows = db.get_children_monthly_savings(parent_code) if parent_code else []
    # rows: {month:'02', total_amount:...}
    month_map = {int(r["month"]): float(r.get("total_amount") or 0) for r in rows if r.get("month")}
    current_month = datetime.now().month
    chart = []
    for i in range(5, -1, -1):
        m = (current_month - i - 1) % 12 + 1
        chart.append({"월": f"{m}월", "저축(원)": month_map.get(m, 0.0)})
    st.bar_chart(chart, x="월", y="저축(원)", use_container_width=True)

    st.divider()

    # 자녀별 요약
    st.subheader("자녀별 요약")
    if not children:
        st.info("연결된 자녀가 없어요. 자녀 계정 가입 시 부모 코드를 입력하면 자동 연결됩니다.")
        st.code(parent_code or "부모 코드 없음", language=None)
    else:
        summary_rows = []
        for ch in children:
            cid = int(ch["id"])
            stats = db.get_child_stats(cid)
            behaviors = db.get_user_behaviors(cid, limit=500)
            total_allowance = sum((b.get("amount") or 0) for b in behaviors if b.get("behavior_type") == "allowance")
            total_saving = sum((b.get("amount") or 0) for b in behaviors if b.get("behavior_type") == "saving")
            total_spend = sum((b.get("amount") or 0) for b in behaviors if b.get("behavior_type") in ("planned_spending", "impulse_buying"))
            balance = total_allowance - total_saving - total_spend
            summary_rows.append(
                {
                    "자녀": ch.get("name"),
                    "아이디": ch.get("username"),
                    "잔액(추정)": int(balance),
                    "총 용돈(지급)": int(total_allowance),
                    "총 저축": int(stats.get("total_savings") or 0),
                    "활동 수": int(stats.get("activity_count") or 0),
                }
            )
        st.dataframe(summary_rows, use_container_width=True, hide_index=True)

        st.caption("잔액은 기록된 ‘용돈 지급/저축/지출’로 계산한 추정값이에요.")

    st.divider()
    st.subheader("다음 액션")
    x1, x2 = st.columns(2)
    with x1:
        if st.button("💵 용돈 관리로 이동", use_container_width=True):
            st.switch_page("pages/9_💵_용돈_관리.py")
    with x2:
        if st.button("👶 자녀 관리로 이동", use_container_width=True):
            st.switch_page("pages/2_📊_부모_대시보드.py")


if __name__ == "__main__":
    main()

