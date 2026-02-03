import streamlit as st

from datetime import date, datetime, timedelta

from database.db_manager import DatabaseManager
from utils.menu import render_sidebar_menu, hide_sidebar_navigation


def _guard_login() -> bool:
    if not st.session_state.get("logged_in"):
        st.switch_page("app.py")
        return False
    return True


def _month_prefix(dt: datetime) -> str:
    return f"{dt.year}-{dt.month:02d}"


def _compute_balance(db: DatabaseManager, user_id: int) -> dict:
    behaviors = db.get_user_behaviors(user_id, limit=5000)
    total_allowance = sum((b.get("amount") or 0) for b in behaviors if b.get("behavior_type") == "allowance")
    total_saving = sum((b.get("amount") or 0) for b in behaviors if b.get("behavior_type") == "saving")
    total_spend = sum(
        (b.get("amount") or 0)
        for b in behaviors
        if b.get("behavior_type") in ("planned_spending", "impulse_buying")
    )
    return {
        "behaviors": behaviors,
        "total_allowance": float(total_allowance),
        "total_saving": float(total_saving),
        "total_spend": float(total_spend),
        "balance": float(total_allowance - total_saving - total_spend),
    }


def _next_run_weekly(today: date, day_of_week: int) -> date:
    # 0=월..6=일
    delta = (day_of_week - today.weekday()) % 7
    if delta == 0:
        delta = 7
    return today + timedelta(days=delta)


def _next_run_monthly(today: date, day_of_month: int) -> date:
    # 이번 달 day_of_month가 아직 안 지났으면 이번 달, 아니면 다음 달
    y, m = today.year, today.month
    try_date = None
    for _ in range(2):
        try:
            try_date = date(y, m, min(day_of_month, 28 if m == 2 else 30 if m in (4, 6, 9, 11) else 31))
        except Exception:
            try_date = date(y, m, 28)
        if try_date > today:
            return try_date
        # next month
        if m == 12:
            y, m = y + 1, 1
        else:
            m += 1
    return try_date


def main():
    if not _guard_login():
        return

    hide_sidebar_navigation()
    db = DatabaseManager()
    # ✅ 스케줄러 대체: 페이지 진입 시 정기용돈 자동 실행
    try:
        db.run_due_recurring_allowances()
    except Exception:
        pass

    user_id = int(st.session_state.get("user_id"))
    user_name = st.session_state.get("user_name", "사용자")
    user_type = st.session_state.get("user_type", "child")

    render_sidebar_menu(user_id, user_name, user_type)

    st.title("💵 용돈 관리")

    # 대상(부모: 자녀 선택 / 아이: 본인)
    target_user_id = user_id
    target_label = user_name
    parent_code = ""

    if user_type == "parent":
        parent = db.get_user_by_id(user_id)
        parent_code = (parent or {}).get("parent_code", "")
        children = db.get_users_by_parent_code(parent_code) if parent_code else []
        if not children:
            st.info("연결된 자녀가 없어요. 자녀가 가입할 때 부모 코드를 입력하면 자동 연결됩니다.")
            st.code(parent_code or "부모 코드 없음", language=None)
            return

        child_label_to_id = {f"{c['name']} ({c['username']})": c["id"] for c in children}
        # 자녀 관리 카드에서 넘어온 경우 자동 선택
        preselect_id = st.session_state.get("allowance_target_child_id")
        labels = list(child_label_to_id.keys())
        default_idx = 0
        if preselect_id:
            for i, lbl in enumerate(labels):
                if int(child_label_to_id[lbl]) == int(preselect_id):
                    default_idx = i
                    break
        selected_label = st.selectbox("대상 자녀", labels, index=default_idx, key="allowance_target_select")
        target_user_id = int(child_label_to_id[selected_label])
        target_user = db.get_user_by_id(target_user_id)
        target_label = (target_user or {}).get("name") or selected_label
        # 1회 프리셀렉트는 소비
        if "allowance_target_child_id" in st.session_state:
            try:
                del st.session_state["allowance_target_child_id"]
            except Exception:
                pass

    stats = _compute_balance(db, target_user_id)
    st.caption(f"대상: **{target_label}**")

    # ✅ 모바일 우선: 4열 → 2열(2줄)
    m1, m2 = st.columns(2)
    with m1:
        st.metric("잔액(추정)", f"{int(stats['balance']):,}원")
    with m2:
        st.metric("용돈(지급)", f"{int(stats['total_allowance']):,}원")
    m3, m4 = st.columns(2)
    with m3:
        st.metric("저축", f"{int(stats['total_saving']):,}원")
    with m4:
        st.metric("지출", f"{int(stats['total_spend']):,}원")

    st.divider()

    if user_type == "parent":
        tab_pay, tab_recurring, tab_history = st.tabs(["💸 용돈 지급", "⏰ 정기 용돈", "📈 히스토리"])

        with tab_pay:
            st.subheader("용돈 지급")
            with st.form("give_allowance"):
                amount = st.number_input("금액(원)", min_value=100, step=100, value=5000)
                category = st.selectbox("카테고리", ["용돈", "보상", "미션", "기타"])
                memo = st.text_input("메모", placeholder="예: 이번 주 용돈")
                submitted = st.form_submit_button("💰 지급하기", use_container_width=True, type="primary")

            if submitted:
                db.save_behavior_v2(
                    target_user_id,
                    "allowance",
                    float(amount),
                    description=memo or "용돈 지급",
                    category=category,
                )
                db.create_notification(target_user_id, "용돈이 들어왔어요!", f"{int(amount):,}원을 받았어요.", level="success")
                st.success("지급 완료!")
                st.rerun()

        with tab_recurring:
            st.subheader("정기 용돈 자동 지급")
            st.caption("스케줄러가 없어서, 앱 실행 시/이 화면에서 ‘실행(테스트)’로 반영됩니다.")

            with st.form("create_recurring"):
                amount = st.number_input("정기 금액(원)", min_value=100, step=100, value=5000, key="rec_amt")
                frequency = st.selectbox("주기", ["매주", "매월"])
                day_of_week = None
                day_of_month = None
                if frequency == "매주":
                    day_of_week = st.selectbox("요일", ["월", "화", "수", "목", "금", "토", "일"])
                else:
                    day_of_month = st.number_input("매월 몇 일", min_value=1, max_value=31, value=1, step=1)
                memo = st.text_input("메모(선택)", placeholder="예: 월요일 아침 용돈")
                submitted = st.form_submit_button("정기 용돈 추가", use_container_width=True)

            if submitted:
                today = date.today()
                if frequency == "매주":
                    idx = ["월", "화", "수", "목", "금", "토", "일"].index(day_of_week)
                    next_run = _next_run_weekly(today, idx)
                    rid = db.create_recurring_allowance(
                        parent_id=user_id,
                        child_id=target_user_id,
                        amount=float(amount),
                        frequency="weekly",
                        day_of_week=idx,
                        next_run=next_run.isoformat(),
                        memo=memo or None,
                    )
                else:
                    next_run = _next_run_monthly(today, int(day_of_month))
                    rid = db.create_recurring_allowance(
                        parent_id=user_id,
                        child_id=target_user_id,
                        amount=float(amount),
                        frequency="monthly",
                        day_of_month=int(day_of_month),
                        next_run=next_run.isoformat(),
                        memo=memo or None,
                    )
                st.success(f"정기 용돈을 추가했어요. (ID: {rid}) 다음 지급: {next_run}")

            st.divider()
            st.subheader("내 정기 용돈 목록")
            recs = db.get_recurring_allowances(user_id)
            if not recs:
                st.caption("등록된 정기 용돈이 없어요.")
            else:
                for r in recs:
                    with st.container(border=True):
                        child_name = r.get("child_name") or ""
                        amt = int(r.get("amount") or 0)
                        freq = "매주" if r.get("frequency") == "weekly" else "매월"
                        next_run = r.get("next_run") or "-"
                        active = bool(r.get("is_active"))
                        st.markdown(f"**{child_name}** · {freq} · **{amt:,}원** · 다음: {next_run}")
                        if r.get("memo"):
                            st.caption(r.get("memo"))
                        c1, c2 = st.columns(2)
                        if c1.button(("⏸️ 중지" if active else "▶️ 재개"), key=f"toggle_{r['id']}", use_container_width=True):
                            db.set_recurring_allowance_active(int(r["id"]), not active)
                            st.rerun()
                        if c2.button("지금 지급(테스트)", key=f"run_{r['id']}", use_container_width=True):
                            db.save_behavior_v2(
                                int(r["child_id"]),
                                "allowance",
                                float(r.get("amount") or 0),
                                description=f"정기 용돈 지급({freq})",
                                category="정기용돈",
                            )
                            db.create_notification(int(r["child_id"]), "정기 용돈이 들어왔어요!", f"{amt:,}원을 받았어요.", level="success")
                            st.success("지급 완료!")

        with tab_history:
            st.subheader("용돈 지급 히스토리")
            # allowance만 필터
            allowance_rows = [b for b in stats["behaviors"] if b.get("behavior_type") == "allowance"]
            if not allowance_rows:
                st.caption("아직 용돈 기록이 없어요.")
            else:
                # 최근 30개 표
                st.dataframe(
                    [
                        {
                            "일시": r.get("timestamp"),
                            "금액": int(r.get("amount") or 0),
                            "카테고리": r.get("category") or "",
                            "내용": r.get("description") or "",
                        }
                        for r in allowance_rows[:30]
                    ],
                    use_container_width=True,
                    hide_index=True,
                )

                # 월별 그래프(최근 6개월)
                now = datetime.now()
                month_totals = {}
                for r in allowance_rows:
                    ts = str(r.get("timestamp") or "")
                    if len(ts) >= 7:
                        key = ts[:7]  # YYYY-MM
                        month_totals[key] = month_totals.get(key, 0) + float(r.get("amount") or 0)
                chart = [{"월": k, "지급(원)": v} for k, v in sorted(month_totals.items())[-6:]]
                st.bar_chart(chart, x="월", y="지급(원)", use_container_width=True)

    else:
        # 아이용: 내역/요청/카테고리
        st.subheader("최근 내역")
        recent = stats["behaviors"][:30]
        if not recent:
            st.caption("아직 기록이 없어요.")
        else:
            type_kr = {
                "allowance": "용돈",
                "saving": "저축",
                "planned_spending": "계획 소비",
                "impulse_buying": "충동 소비",
                "delayed_gratification": "참기",
                "comparing_prices": "가격 비교",
                "spend": "지출",
            }
            st.dataframe(
                [
                    {
                        "일시": r.get("timestamp"),
                        "유형": type_kr.get(str(r.get("behavior_type") or "").strip(), str(r.get("behavior_type") or "").strip()),
                        "금액": int(r.get("amount") or 0),
                        "카테고리": r.get("category") or "",
                        "내용": r.get("description") or "",
                    }
                    for r in recent
                ],
                use_container_width=True,
                hide_index=True,
            )

        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            if st.button("📝 용돈/지출 요청하기", use_container_width=True):
                st.switch_page("pages/9_📝_용돈_요청.py")
        with c2:
            if st.button("🎯 저축 목표로 이동", use_container_width=True):
                st.switch_page("pages/8_🎯_저축_목표.py")


if __name__ == "__main__":
    main()

