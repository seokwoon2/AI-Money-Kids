import streamlit as st

from database.db_manager import DatabaseManager
from utils.menu import render_sidebar_menu, hide_sidebar_navigation


def _guard_child(db: DatabaseManager):
    if not st.session_state.get("logged_in"):
        st.switch_page("app.py")
        return None
    user_type = st.session_state.get("user_type", "child")
    if user_type != "child":
        st.error("아이 계정에서만 사용할 수 있어요.")
        st.stop()
    user_id = int(st.session_state.get("user_id"))
    child = db.get_user_by_id(user_id)
    return child


def main():
    hide_sidebar_navigation()
    db = DatabaseManager()

    child = _guard_child(db)
    user_id = int(st.session_state.get("user_id"))
    user_name = st.session_state.get("user_name", "사용자")

    render_sidebar_menu(user_id, user_name, "child")

    st.title("📝 용돈/지출 요청")
    st.caption("부모님께 용돈을 요청하거나 지출 승인을 요청할 수 있어요.")

    parent_code = (child or {}).get("parent_code", "")
    if not parent_code:
        st.error("부모 코드가 없어서 요청을 보낼 수 없어요. 부모님에게 코드를 확인해달라고 해주세요.")
        return

    with st.form("request_form"):
        request_type = st.selectbox("요청 종류", ["💵 용돈 요청", "🧾 지출 승인 요청"])
        amount = st.number_input("금액(원)", min_value=100, step=100, value=1000)
        category = st.selectbox("카테고리", ["간식", "장난감", "학용품", "저축", "기타"])
        reason = st.text_input("이유", placeholder="예: 친구 생일 선물 사고 싶어요")
        submitted = st.form_submit_button("요청 보내기", use_container_width=True)

    if submitted:
        rtype = "allowance" if "용돈" in request_type else "spend"
        rid = db.create_request(user_id, parent_code, rtype, float(amount), category=category, reason=reason or None)
        # 부모에게 알림(부모 찾기)
        parent = db.get_parent_by_code(parent_code)
        if parent:
            db.create_notification(int(parent["id"]), "새 요청이 도착했어요", f"{user_name}의 요청: {int(amount):,}원", level="info")
        st.success("요청을 보냈어요!")
        st.rerun()

    st.divider()
    st.subheader("내 요청 히스토리")
    history = db.get_requests_for_child(user_id, limit=30)
    if not history:
        st.caption("아직 요청한 기록이 없어요.")
    else:
        rows = []
        for r in history:
            rows.append(
                {
                    "날짜": r.get("created_at"),
                    "종류": "용돈" if r.get("request_type") == "allowance" else "지출",
                    "금액": int(r.get("amount") or 0),
                    "상태": r.get("status"),
                    "카테고리": r.get("category") or "",
                    "이유": r.get("reason") or "",
                }
            )
        st.dataframe(rows, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()

