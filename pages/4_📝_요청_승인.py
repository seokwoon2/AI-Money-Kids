import streamlit as st

from database.db_manager import DatabaseManager
from utils.menu import render_sidebar_menu, hide_sidebar_navigation


def _guard_parent(db: DatabaseManager):
    if not st.session_state.get("logged_in"):
        st.switch_page("app.py")
        return None, None
    user_type = st.session_state.get("user_type", "child")
    if user_type != "parent":
        st.error("부모님만 접근할 수 있어요.")
        st.stop()
    user_id = int(st.session_state.get("user_id"))
    parent = db.get_user_by_id(user_id)
    return user_id, parent


def main():
    hide_sidebar_navigation()
    db = DatabaseManager()

    parent_id, parent = _guard_parent(db)
    user_name = st.session_state.get("user_name", "사용자")

    render_sidebar_menu(parent_id, user_name, "parent")

    parent_code = parent.get("parent_code") if parent else ""
    st.title("📝 요청 승인")
    st.caption("아이의 용돈/지출 요청을 승인하거나 거절할 수 있어요.")

    if not parent_code:
        st.error("부모 코드를 확인할 수 없어요.")
        return

    pending = db.get_requests_for_parent(parent_code, status="pending")
    if not pending:
        st.success("현재 대기 중인 요청이 없어요.")
        return

    for req in pending:
        rtype = req.get("request_type")
        rtype_kr = "용돈 요청" if rtype == "allowance" else ("지출 승인" if rtype == "spend" else rtype)
        amount = int(req.get("amount") or 0)
        title = f"{req.get('child_name')} ({req.get('child_username')}) - {rtype_kr}"
        with st.container(border=True):
            st.markdown(f"**{title}**")
            st.write(f"- 금액: **{amount:,}원**")
            if req.get("category"):
                st.write(f"- 카테고리: **{req.get('category')}**")
            if req.get("reason"):
                st.write(f"- 사유: {req.get('reason')}")

            c1, c2 = st.columns(2)
            approve = c1.button("✅ 승인", use_container_width=True, key=f"approve_{req['id']}")
            reject = c2.button("❌ 거절", use_container_width=True, key=f"reject_{req['id']}")

            if approve or reject:
                new_status = "approved" if approve else "rejected"
                ok = db.decide_request(int(req["id"]), parent_id, new_status)
                if not ok:
                    st.error("처리에 실패했어요.")
                    continue

                child_id = int(req["child_id"])
                if new_status == "approved":
                    # 승인 시: 행동 기록 생성
                    if rtype == "allowance":
                        db.save_behavior_v2(
                            child_id,
                            "allowance",
                            float(req.get("amount") or 0),
                            description="부모 승인 지급",
                            category=req.get("category"),
                            related_request_id=int(req["id"]),
                        )
                    elif rtype == "spend":
                        # 지출 승인: 최근 충동 시그널이 높으면 impulse_buying으로 기록
                        btype = "planned_spending"
                        try:
                            sig = db.get_latest_risk_signal(child_id, within_minutes=60) if hasattr(db, "get_latest_risk_signal") else None
                            if sig and (sig.get("signal_type") in ("impulse_request", "impulse_stop")) and int(sig.get("score") or 0) >= 70:
                                btype = "impulse_buying"
                        except Exception:
                            btype = "planned_spending"
                        db.save_behavior_v2(
                            child_id,
                            btype,
                            float(req.get("amount") or 0),
                            description="부모 승인 지출",
                            category=req.get("category"),
                            related_request_id=int(req["id"]),
                        )
                    db.create_notification(
                        child_id,
                        "요청이 승인되었어요!",
                        f"{amount:,}원이 승인되었습니다.",
                        level="success",
                    )
                    st.success("승인 완료!")
                else:
                    db.create_notification(
                        child_id,
                        "요청이 거절되었어요",
                        f"{amount:,}원 요청이 거절되었습니다.",
                        level="warning",
                    )
                    st.info("거절 완료")

                st.rerun()


if __name__ == "__main__":
    main()

