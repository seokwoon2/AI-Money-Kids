import streamlit as st

from datetime import datetime

from database.db_manager import DatabaseManager
from utils.menu import render_sidebar_menu, hide_sidebar_navigation


def _guard_parent() -> bool:
    if not st.session_state.get("logged_in"):
        st.switch_page("app.py")
        return False
    if st.session_state.get("user_type") != "parent":
        st.error("부모님만 접근할 수 있어요.")
        return False
    return True


def main():
    if not _guard_parent():
        return

    hide_sidebar_navigation()
    db = DatabaseManager()

    user_id = int(st.session_state.get("user_id"))
    user_name = st.session_state.get("user_name", "사용자")
    render_sidebar_menu(user_id, user_name, "parent")

    parent = db.get_user_by_id(user_id)
    parent_code = (parent or {}).get("parent_code", "")
    children = db.get_users_by_parent_code(parent_code) if parent_code else []

    st.title("📊 리포트")
    st.caption("자녀별 소비/저축 패턴과 가족 통계를 확인해요.")

    # 기간: 이번 달 기준
    now = datetime.now()
    ym = f"{now.year}-{now.month:02d}"

    # 가족 지표
    monthly = db.get_children_behavior_stats_this_month(parent_code) if parent_code else {"monthly_total": 0, "yesterday_total": 0}
    monthly_total = int(monthly.get("monthly_total") or 0)
    yesterday_total = int(monthly.get("yesterday_total") or 0)

    a, b, c = st.columns(3)
    with a:
        st.metric("이번달 가족 저축", f"{monthly_total:,}원")
    with b:
        st.metric("어제 저축", f"{yesterday_total:,}원")
    with c:
        st.metric("자녀 수", f"{len(children)}명")

    st.divider()

    st.subheader("최근 6개월 저축 추이")
    rows = db.get_children_monthly_savings(parent_code) if parent_code else []
    month_map = {str(r.get("month") or "").lstrip("0"): float(r.get("total_amount") or 0) for r in rows}
    # chart labels
    chart = []
    cur_m = now.month
    for i in range(5, -1, -1):
        m = (cur_m - i - 1) % 12 + 1
        chart.append({"월": f"{m}월", "저축(원)": month_map.get(str(m), 0.0)})
    st.bar_chart(chart, x="월", y="저축(원)", use_container_width=True)

    st.divider()

    st.subheader("카테고리별 지출(이번 달)")
    if not children:
        st.info("연결된 자녀가 없어요.")
        return

    spend_by_cat = {}
    for ch in children:
        beh = db.get_user_behaviors(int(ch["id"]), limit=5000)
        for b in beh:
            ts = str(b.get("timestamp") or "")
            if not ts.startswith(ym):
                continue
            if b.get("behavior_type") not in ("planned_spending", "impulse_buying"):
                continue
            cat = (b.get("category") or "기타").strip()
            spend_by_cat[cat] = spend_by_cat.get(cat, 0) + float(b.get("amount") or 0)

    if not spend_by_cat:
        st.caption("이번 달 지출 기록이 아직 없어요.")
    else:
        chart2 = [{"카테고리": k, "지출(원)": v} for k, v in sorted(spend_by_cat.items(), key=lambda x: x[1], reverse=True)]
        st.bar_chart(chart2, x="카테고리", y="지출(원)", use_container_width=True)

    st.divider()

    st.subheader("자녀별 요약")
    summary = []
    for ch in children:
        cid = int(ch["id"])
        beh = db.get_user_behaviors(cid, limit=5000)
        total_allowance = sum((b.get("amount") or 0) for b in beh if b.get("behavior_type") == "allowance")
        total_saving = sum((b.get("amount") or 0) for b in beh if b.get("behavior_type") == "saving")
        total_spend = sum(
            (b.get("amount") or 0)
            for b in beh
            if b.get("behavior_type") in ("planned_spending", "impulse_buying")
        )
        balance = total_allowance - total_saving - total_spend
        summary.append(
            {
                "자녀": ch.get("name"),
                "잔액(추정)": int(balance),
                "용돈(지급)": int(total_allowance),
                "저축": int(total_saving),
                "지출": int(total_spend),
            }
        )
    st.dataframe(summary, use_container_width=True, hide_index=True)

    st.caption("잔액은 ‘용돈 지급 - 저축 - (계획/충동)지출’로 계산한 추정치입니다.")


if __name__ == "__main__":
    main()

