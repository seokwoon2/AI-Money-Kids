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
    user_type = st.session_state.get("user_type", "child")

    render_sidebar_menu(user_id, user_name, user_type)

    # 구버전 페이지 → 새 구조로 이동
    st.switch_page("pages/3_💵_용돈_관리.py")

    # 대상(부모: 자녀 선택 / 아이: 본인)
    target_user_id = int(user_id) if user_id else None
    target_label = user_name

    if user_type == "parent":
        parent = db.get_user_by_id(int(user_id)) if user_id else None
        parent_code = parent.get("parent_code") if parent else ""
        children = db.get_users_by_parent_code(parent_code) if parent_code else []

        if not children:
            st.info("연결된 자녀가 없어요. 자녀가 가입할 때 부모 코드를 입력하면 자동 연결됩니다.")
            st.code(parent_code or "부모 코드 없음", language=None)
            if st.button("👶 자녀 관리로 이동", use_container_width=True):
                st.switch_page("pages/2_📊_부모_대시보드.py")
            return

        child_label_to_id = {f"{c['name']} ({c['username']})": c["id"] for c in children}
        selected_label = st.selectbox("대상 자녀", list(child_label_to_id.keys()))
        target_user_id = int(child_label_to_id[selected_label])
        target_user = db.get_user_by_id(target_user_id)
        target_label = target_user.get("name") if target_user else selected_label

    if not target_user_id:
        st.error("대상을 확인할 수 없어요.")
        return

    # 데이터 로드
    behaviors = db.get_user_behaviors(target_user_id, limit=500)
    total_allowance = sum((b.get("amount") or 0) for b in behaviors if b.get("behavior_type") == "allowance")
    total_saving = sum((b.get("amount") or 0) for b in behaviors if b.get("behavior_type") == "saving")
    total_planned = sum((b.get("amount") or 0) for b in behaviors if b.get("behavior_type") == "planned_spending")
    total_impulse = sum((b.get("amount") or 0) for b in behaviors if b.get("behavior_type") == "impulse_buying")
    total_spend = total_planned + total_impulse
    balance = total_allowance - total_saving - total_spend

    st.caption(f"대상: **{target_label}**")
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("잔액(추정)", f"{int(balance):,}원")
    with m2:
        st.metric("용돈(지급)", f"{int(total_allowance):,}원")
    with m3:
        st.metric("저축", f"{int(total_saving):,}원")
    with m4:
        st.metric("지출", f"{int(total_spend):,}원")

    st.divider()

    st.subheader("기록 추가")
    # 부모는 지급까지 가능, 아이는 저축/지출만
    options = []
    if user_type == "parent":
        options.append(("allowance", "💵 용돈 지급"))
    options += [
        ("saving", "🪙 저축"),
        ("planned_spending", "🧾 계획 지출"),
        ("impulse_buying", "⚡ 충동 구매"),
    ]
    type_map = {label: key for key, label in options}
    picked_label = st.selectbox("유형", list(type_map.keys()))
    behavior_type = type_map[picked_label]

    with st.form("add_behavior"):
        amount = st.number_input("금액(원)", min_value=0, step=100, value=1000)
        description = st.text_input("메모(선택)", placeholder="예: 용돈 지급, 저금통에 넣었어요, 편의점 간식 등")
        submitted = st.form_submit_button("저장", use_container_width=True)

    if submitted:
        if amount <= 0:
            st.error("금액은 0원보다 커야 해요.")
        else:
            db.save_behavior(target_user_id, behavior_type, float(amount), description.strip() or None)
            st.success("저장했어요.")
            st.rerun()

    st.divider()

    st.subheader("최근 기록")
    if not behaviors:
        st.caption("아직 기록이 없어요. 위에서 한 번 추가해보세요.")
    else:
        recent = behaviors[:30]
        rows = []
        label_by_type = {
            "allowance": "💵 용돈",
            "saving": "🪙 저축",
            "planned_spending": "🧾 계획 지출",
            "impulse_buying": "⚡ 충동 구매",
            "delayed_gratification": "⏳ 만족 지연",
            "comparing_prices": "🔎 가격 비교",
        }
        for b in recent:
            rows.append(
                {
                    "일시": b.get("timestamp"),
                    "유형": label_by_type.get(b.get("behavior_type"), b.get("behavior_type")),
                    "금액": int(b.get("amount") or 0),
                    "내용": b.get("description") or "",
                }
            )
        st.dataframe(rows, use_container_width=True, hide_index=True)

    st.divider()
    if st.button("🏠 메인으로 돌아가기", use_container_width=True):
        st.switch_page("app.py")


if __name__ == "__main__":
    main()

