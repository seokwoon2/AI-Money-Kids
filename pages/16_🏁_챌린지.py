import streamlit as st

from datetime import date, timedelta

from database.db_manager import DatabaseManager
from utils.menu import render_sidebar_menu, hide_sidebar_navigation
from utils.money_format import format_korean_won


def _guard_login() -> bool:
    if not st.session_state.get("logged_in"):
        st.switch_page("app.py")
        return False
    return True


def _daterange_days(start: date, end: date) -> int:
    return max(1, (end - start).days + 1)


def _fmt_range(start_s: str, end_s: str) -> str:
    return f"{start_s} ~ {end_s}"


def _type_badge(ctype: str) -> str:
    ctype = str(ctype or "").strip()
    return {
        "spend_cap": "🧾 소비 제한",
        "reduce_category": "🛒 패턴 개선",
        "daily_save_fixed": "🐷 하루 저축",
        "daily_save_increasing": "📈 늘리는 저축",
        "habit_custom": "✅ 습관",
    }.get(ctype, "🏁 챌린지")


def _days_left(end_date_s: str) -> int:
    try:
        e = date.fromisoformat(str(end_date_s))
    except Exception:
        return 0
    return (e - date.today()).days


def main():
    if not _guard_login():
        return

    hide_sidebar_navigation()
    db = DatabaseManager()

    user_id = int(st.session_state.get("user_id"))
    user_name = st.session_state.get("user_name", "사용자")
    user_type = st.session_state.get("user_type", "child")

    render_sidebar_menu(user_id, user_name, user_type)

    st.title("🏁 챌린지")
    st.caption("소비·저축·습관 목표에 도전하고 보상을 받아요.")

    if user_type == "child":
        # 상단 요약 카드(실사용 UX)
        try:
            active_cnt = len(db.get_challenge_instances(user_id, status="active", limit=50) or [])
        except Exception:
            active_cnt = 0
        with st.container(border=True):
            st.markdown("### 오늘의 도전")
            st.caption(f"진행 중 {active_cnt}개 · 기간이 끝나면 ‘정산하기’로 보상을 받아요.")

        st.subheader("진행 중인 챌린지")
        active = db.get_challenge_instances(user_id, status="active", limit=20) if hasattr(db, "get_challenge_instances") else []
        if not active:
            st.caption("진행 중인 챌린지가 없어요. 아래에서 새로 시작해보자!")
        else:
            for inst in active:
                prog = db.compute_challenge_progress(inst) if hasattr(db, "compute_challenge_progress") else {}
                with st.container(border=True):
                    st.markdown(f"**{_type_badge(inst.get('challenge_type'))} · {inst.get('template_title')}**")
                    st.caption(_fmt_range(inst.get("start_date"), inst.get("end_date")))
                    dl = _days_left(inst.get("end_date"))
                    if dl >= 0:
                        st.caption(f"남은 기간: **D-{dl}**")
                    st.caption(prog.get("summary") or "")
                    st.progress(float(prog.get("progress") or 0))
                    c1, c2 = st.columns(2)
                    with c1:
                        if prog.get("can_finalize") and st.button("🏁 정산하기", key=f"final_{inst.get('id')}", use_container_width=True, type="primary"):
                            db.finalize_challenge_if_due(int(inst["id"]))
                            st.rerun()
                        elif st.button("🔄 새로고침", key=f"ref_{inst.get('id')}", use_container_width=True):
                            st.rerun()
                    with c2:
                        if str(inst.get("challenge_type")) == "habit_custom":
                            today = date.today().isoformat()
                            if st.button("✅ 오늘 했어요", key=f"checkin_{inst.get('id')}", use_container_width=True):
                                if hasattr(db, "create_challenge_checkin"):
                                    db.create_challenge_checkin(int(inst["id"]), today, value=1.0, note=None)
                                st.rerun()

        st.divider()
        st.subheader("새 챌린지 시작")

        tab_spend, tab_save, tab_auto = st.tabs(["1) 소비", "2) 저축", "3) 자동저축"])

        with tab_spend:
            st.markdown("#### 1) 소비 N원 이하 도전")
            c1, c2 = st.columns(2)
            with c1:
                period = st.selectbox("기간", ["하루", "3일", "일주일"], index=2, key="spend_period")
            with c2:
                cap = st.number_input("목표 소비 상한(원)", min_value=0, step=1000, value=10000, key="spend_cap")

            days = 1 if period == "하루" else (3 if period == "3일" else 7)
            start = date.today()
            end = start + timedelta(days=days - 1)
            st.caption(f"기간: **{_fmt_range(start.isoformat(), end.isoformat())}** · 목표: **{int(cap):,}원({format_korean_won(cap)}) 이하**")

            # 프리셋(실사용 UX)
            p1, p2, p3 = st.columns(3)
            if p1.button("1만원", use_container_width=True, key="cap_1w"):
                st.session_state["spend_cap"] = 10_000
                st.rerun()
            if p2.button("2만원", use_container_width=True, key="cap_2w"):
                st.session_state["spend_cap"] = 20_000
                st.rerun()
            if p3.button("5만원", use_container_width=True, key="cap_5w"):
                st.session_state["spend_cap"] = 50_000
                st.rerun()

            if st.button("🏁 소비 챌린지 시작", use_container_width=True, type="primary", key="start_spend_cap"):
                tid = db.create_challenge_template(
                    None,
                    title=f"{period} 소비 {int(cap):,}원 이하",
                    challenge_type="spend_cap",
                    params={"cap_amount": int(cap), "days": int(days)},
                    reward_amount=0,
                    reward_coins=10,
                    created_by=None,
                )
                db.start_challenge(user_id, tid, start.isoformat(), end.isoformat())
                st.success("시작했어요! 기간이 끝나면 정산할 수 있어요.")
                st.rerun()

            st.markdown("---")
            st.markdown("#### 2) 소비패턴 줄이기 도전(카테고리)")
            st.caption("지난 기간(예: 지난주/지난달) 대비 특정 카테고리 소비를 n% 줄이는 챌린지예요.")
            base = st.selectbox("기준 기간", ["지난 7일", "지난 30일"], index=0, key="reduce_base")
            pct = st.slider("줄이기 목표(%)", min_value=5, max_value=50, value=10, step=5, key="reduce_pct")
            period_days = 7 if base == "지난 7일" else 30

            # 카테고리 추천(최근 지출 상위)
            try:
                conn = db._get_connection()  # pylint: disable=protected-access
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT COALESCE(category,'미분류') as cat, COALESCE(SUM(amount),0) as s
                    FROM behaviors
                    WHERE user_id = ?
                      AND behavior_type IN ('planned_spending','impulse_buying','spend')
                      AND datetime(timestamp) >= datetime('now', ?)
                    GROUP BY COALESCE(category,'미분류')
                    ORDER BY s DESC
                    LIMIT 10
                    """,
                    (int(user_id), f"-{int(period_days)} day"),
                )
                cats = [(str(r["cat"]), float(r["s"] or 0)) for r in cur.fetchall()]
            except Exception:
                cats = []
            finally:
                try:
                    conn.close()
                except Exception:
                    pass

            options = [c[0] for c in cats] or ["편의점", "간식", "게임", "미분류"]
            cat = st.selectbox("카테고리 선택", options, index=0, key="reduce_cat")
            # baseline: 직전 기간(같은 길이) 합계
            baseline_start = date.today() - timedelta(days=period_days * 2)
            baseline_end = date.today() - timedelta(days=period_days + 1)
            baseline = db._sum_spend_in_range(user_id, baseline_start.isoformat(), baseline_end.isoformat(), category=cat if cat != "미분류" else "미분류") if hasattr(db, "_sum_spend_in_range") else 0
            target = float(baseline) * (1.0 - (float(pct) / 100.0))
            st.caption(f"기준(직전 {period_days}일) {cat} 소비: **{int(baseline):,}원** → 목표: **{int(target):,}원 이하**")

            if st.button("🏁 패턴 줄이기 챌린지 시작", use_container_width=True, type="primary", key="start_reduce_cat"):
                start2 = date.today()
                end2 = start2 + timedelta(days=period_days - 1)
                tid = db.create_challenge_template(
                    None,
                    title=f"{cat} 소비 {int(pct)}% 줄이기",
                    challenge_type="reduce_category",
                    params={"category": cat, "reduction_pct": int(pct), "baseline_amount": float(baseline), "days": int(period_days)},
                    reward_amount=0,
                    reward_coins=20,
                    created_by=None,
                )
                db.start_challenge(user_id, tid, start2.isoformat(), end2.isoformat())
                st.success("시작했어요! 기간이 끝나면 정산할 수 있어요.")
                st.rerun()

        with tab_save:
            st.markdown("#### 1) 하루 500원 저축(고정)")
            fixed_amt = st.number_input("하루 저축(원)", min_value=0, step=100, value=500, key="save_fixed_amt")
            fixed_days = st.selectbox("기간", ["3일", "일주일"], index=1, key="save_fixed_days")
            d = 3 if fixed_days == "3일" else 7
            start = date.today()
            end = start + timedelta(days=d - 1)
            st.caption(f"기간: **{_fmt_range(start.isoformat(), end.isoformat())}** · 하루 **{int(fixed_amt):,}원({format_korean_won(fixed_amt)})**")
            if st.button("🐷 하루 저축 챌린지 시작", use_container_width=True, type="primary", key="start_daily_save_fixed"):
                tid = db.create_challenge_template(
                    None,
                    title=f"{d}일 매일 {int(fixed_amt):,}원 저축",
                    challenge_type="daily_save_fixed",
                    params={"daily_amount": int(fixed_amt), "days": int(d)},
                    reward_amount=0,
                    reward_coins=15,
                    created_by=None,
                )
                db.start_challenge(user_id, tid, start.isoformat(), end.isoformat())
                st.success("시작했어요! 매일 저축 기록을 남기면 달성돼요.")
                st.rerun()

            st.markdown("---")
            st.markdown("#### 2) 금액이 매일 100원씩 증가(예: 500→600→700...)")
            inc_start = st.number_input("첫날 저축(원)", min_value=0, step=100, value=500, key="save_inc_start")
            inc_step = st.number_input("증가분(원)", min_value=0, step=50, value=100, key="save_inc_step")
            inc_days = st.selectbox("기간", ["3일", "일주일"], index=1, key="save_inc_days")
            d2 = 3 if inc_days == "3일" else 7
            s2 = date.today()
            e2 = s2 + timedelta(days=d2 - 1)
            st.caption(
                f"기간: **{_fmt_range(s2.isoformat(), e2.isoformat())}** · 첫날 **{int(inc_start):,}원({format_korean_won(inc_start)})** → 매일 +{int(inc_step):,}원"
            )
            if st.button("📈 늘리는 저축 챌린지 시작", use_container_width=True, type="primary", key="start_daily_save_inc"):
                tid = db.create_challenge_template(
                    None,
                    title=f"{d2}일 늘리는 저축({int(inc_start):,}+{int(inc_step):,}/일)",
                    challenge_type="daily_save_increasing",
                    params={"start_amount": int(inc_start), "daily_increment": int(inc_step), "days": int(d2)},
                    reward_amount=0,
                    reward_coins=25,
                    created_by=None,
                )
                db.start_challenge(user_id, tid, s2.isoformat(), e2.isoformat())
                st.success("시작했어요! 매일 저축 기록을 남기면 달성돼요.")
                st.rerun()

        with tab_auto:
            st.markdown("#### 용돈의 n% 자동저축")
            st.caption("용돈이 들어오면 자동으로 저축 기록을 만들어줘요.")
            stg = db.get_auto_saving_setting(user_id) if hasattr(db, "get_auto_saving_setting") else None
            current_pct = int((stg or {}).get("percent") or 0)
            current_on = bool(int((stg or {}).get("is_active") or 0) == 1)
            on = st.toggle("자동저축 켜기", value=current_on, key="auto_save_toggle")
            pct = st.slider("자동저축 비율(%)", min_value=0, max_value=50, value=current_pct, step=5, key="auto_save_pct")
            if st.button("💾 저장", use_container_width=True, type="primary", key="save_auto_setting"):
                db.set_auto_saving_setting(user_id, pct, on)
                st.success("저장했어요! 다음 용돈부터 자동저축이 적용돼요.")
                st.rerun()

            st.markdown("---")
            st.markdown("#### 주간 보상(간단)")
            st.caption("지난주 자동저축을 달성했으면 코인을 받을 수 있어요.")
            if st.button("🪙 지난주 보상 받기", use_container_width=True, key="autosave_bonus"):
                ok, msg = db.try_grant_autosave_weekly_bonus(user_id, bonus_coins=20)
                (st.success if ok else st.info)(msg)

    else:
        # parent
        st.subheader("부모: 자체 챌린지(습관) 만들기")
        st.caption("방 청소, 스크린타임 줄이기 같은 습관 챌린지를 만들고 자녀에게 보낼 수 있어요.")
        parent = db.get_user_by_id(user_id) or {}
        parent_code = (parent or {}).get("parent_code") or ""
        children = db.get_users_by_parent_code(parent_code) if parent_code else []
        if not children:
            st.info("연결된 자녀가 없어요. 먼저 자녀 연동을 해주세요.")
            return

        label_to_id = {f"{c.get('name')} ({c.get('username')})": int(c["id"]) for c in children}
        who = st.selectbox("자녀 선택", list(label_to_id.keys()), key="ch_parent_child")
        child_id = int(label_to_id[who])

        with st.form("create_habit_challenge"):
            title = st.text_input("챌린지 이름", placeholder="예: 방 청소하기")
            days = st.selectbox("기간", ["3일", "일주일", "2주"], index=1)
            total_days = 3 if days == "3일" else (7 if days == "일주일" else 14)
            target = st.number_input("달성 체크 횟수(예: 5회)", min_value=1, value=min(5, total_days), step=1)
            reward_coins = st.number_input("보상 코인(선택)", min_value=0, value=30, step=5)
            reward_amount = st.number_input("보상 용돈(원, 선택)", min_value=0, value=0, step=100)
            submit = st.form_submit_button("🏁 자녀에게 챌린지 보내기", use_container_width=True, type="primary")

        if submit:
            if not title.strip():
                st.error("챌린지 이름을 입력하세요.")
            else:
                start = date.today()
                end = start + timedelta(days=int(total_days) - 1)
                tid = db.create_challenge_template(
                    parent_code=str(parent_code),
                    title=title.strip(),
                    challenge_type="habit_custom",
                    params={"target_count": int(target)},
                    reward_amount=float(reward_amount),
                    reward_coins=int(reward_coins),
                    created_by=int(user_id),
                )
                db.start_challenge(int(child_id), tid, start.isoformat(), end.isoformat())
                db.create_notification(int(child_id), "새 챌린지가 도착했어요! 🏁", title.strip(), level="info")
                st.success("보냈어요!")

        st.divider()
        st.subheader("자녀 진행 상황(최근)")
        insts = db.get_challenge_instances(child_id, status="active", limit=10) if hasattr(db, "get_challenge_instances") else []
        if not insts:
            st.caption("진행 중인 챌린지가 없어요.")
        else:
            for inst in insts:
                prog = db.compute_challenge_progress(inst) if hasattr(db, "compute_challenge_progress") else {}
                with st.container(border=True):
                    st.markdown(f"**{_type_badge(inst.get('challenge_type'))} · {inst.get('template_title')}**")
                    st.caption(_fmt_range(inst.get("start_date"), inst.get("end_date")))
                    st.caption(prog.get("summary") or "")
                    st.progress(float(prog.get("progress") or 0))


if __name__ == "__main__":
    main()

