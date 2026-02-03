import streamlit as st

from datetime import date, timedelta
import html as _html
from textwrap import dedent as _dedent

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


def _parse_params_json(s: str) -> dict:
    try:
        import json

        return json.loads(s or "{}") or {}
    except Exception:
        return {}


def _sum_by_date(db: DatabaseManager, user_id: int, start_s: str, end_s: str, behavior_type: str, category: str | None = None) -> dict[str, float]:
    """
    date(timestamp) 기준 합계 맵
    """
    conn = db._get_connection()  # pylint: disable=protected-access
    cur = conn.cursor()
    try:
        q = """
            SELECT date(timestamp) as d, COALESCE(SUM(amount),0) as s
            FROM behaviors
            WHERE user_id = ?
              AND behavior_type = ?
              AND date(timestamp) BETWEEN ? AND ?
        """
        params = [int(user_id), str(behavior_type), str(start_s), str(end_s)]
        if category is not None:
            q += " AND COALESCE(category,'') = ?"
            params.append(str(category))
        q += " GROUP BY date(timestamp)"
        cur.execute(q, params)
        rows = cur.fetchall()
        return {str(r["d"]): float(r["s"] or 0) for r in rows}
    finally:
        try:
            conn.close()
        except Exception:
            pass


def _progress_ring(pct: float, label: str) -> str:
    try:
        p = float(pct or 0)
    except Exception:
        p = 0.0
    p = max(0.0, min(1.0, p))
    # SVG circle ring
    radius = 18
    circumference = 2 * 3.1415926535 * radius
    dash = circumference * p
    gap = circumference - dash
    percent_txt = int(round(p * 100))
    # ⚠️ 들여쓰기/선행 공백이 있으면 Streamlit markdown에서 코드블록으로 깨질 수 있어
    # HTML은 항상 0열 시작으로 정리해서 반환합니다.
    return _dedent(
        f"""
        <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; gap:2px; min-width:78px;">
          <svg width="52" height="52" viewBox="0 0 52 52" style="overflow:visible;">
            <circle cx="26" cy="26" r="{radius}" fill="none" stroke="rgba(15,23,42,0.10)" stroke-width="6"></circle>
            <circle cx="26" cy="26" r="{radius}" fill="none" stroke="rgba(16,185,129,0.95)" stroke-width="6"
              stroke-linecap="round"
              stroke-dasharray="{dash:.2f} {gap:.2f}"
              transform="rotate(-90 26 26)"></circle>
            <text x="26" y="30" text-anchor="middle" font-size="13" font-weight="900" fill="#0f172a">{percent_txt}%</text>
          </svg>
          <div style="font-size:11px; font-weight:800; color:rgba(15,23,42,0.60);">{_html.escape(str(label))}</div>
        </div>
        """
    ).strip()


def _days_remaining_inclusive(end_s: str) -> int:
    try:
        e = date.fromisoformat(str(end_s))
    except Exception:
        return 0
    d = (e - date.today()).days
    return 0 if d < 0 else int(d + 1)


def main():
    if not _guard_login():
        return

    hide_sidebar_navigation()
    db = DatabaseManager()

    user_id = int(st.session_state.get("user_id"))
    user_name = st.session_state.get("user_name", "사용자")
    user_type = st.session_state.get("user_type", "child")

    render_sidebar_menu(user_id, user_name, user_type)

    st.markdown('<div id="amf_challenge_anchor"></div>', unsafe_allow_html=True)
    st.markdown(
        _dedent(
            """
        <style>
        /* scope only challenge page */
        div[data-testid="stVerticalBlock"]:has(#amf_challenge_anchor) .amf-card {
          border-radius: 18px;
          padding: 14px 14px;
          border: 1px solid rgba(15,23,42,0.08);
          background: linear-gradient(135deg, rgba(16,185,129,0.14), rgba(99,102,241,0.10));
          box-shadow: 0 14px 30px rgba(0,0,0,0.08);
        }
        div[data-testid="stVerticalBlock"]:has(#amf_challenge_anchor) .amf-row {
          display:flex; justify-content:space-between; align-items:flex-start; gap:12px;
        }
        div[data-testid="stVerticalBlock"]:has(#amf_challenge_anchor) .amf-title {
          font-weight: 950;
          letter-spacing: -0.02em;
          color: #0f172a;
          font-size: 16px;
        }
        div[data-testid="stVerticalBlock"]:has(#amf_challenge_anchor) .amf-sub {
          margin-top: 4px;
          color: rgba(15,23,42,0.66);
          font-weight: 800;
          font-size: 12px;
        }
        div[data-testid="stVerticalBlock"]:has(#amf_challenge_anchor) .amf-chip {
          display:inline-flex;
          gap:6px;
          align-items:center;
          padding: 5px 10px;
          border-radius: 999px;
          border: 1px solid rgba(15,23,42,0.10);
          background: rgba(255,255,255,0.60);
          color: rgba(15,23,42,0.70);
          font-weight: 900;
          font-size: 12px;
          white-space: nowrap;
        }
        div[data-testid="stVerticalBlock"]:has(#amf_challenge_anchor) .amf-kpi {
          display:flex;
          gap:10px;
          flex-wrap:wrap;
          margin-top: 10px;
        }
        div[data-testid="stVerticalBlock"]:has(#amf_challenge_anchor) .amf-kpi .k {
          flex: 1 1 140px;
          border-radius: 14px;
          padding: 10px 10px;
          background: rgba(255,255,255,0.72);
          border: 1px solid rgba(15,23,42,0.06);
        }
        div[data-testid="stVerticalBlock"]:has(#amf_challenge_anchor) .amf-kpi .k .t {
          font-size: 11px;
          font-weight: 900;
          color: rgba(15,23,42,0.62);
        }
        div[data-testid="stVerticalBlock"]:has(#amf_challenge_anchor) .amf-kpi .k .v {
          font-size: 18px;
          font-weight: 950;
          color: #0f172a;
          margin-top: 3px;
          letter-spacing: -0.02em;
        }
        </style>
        """
        ).strip(),
        unsafe_allow_html=True,
    )

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
                params = _parse_params_json(inst.get("params_json") or "")
                ctype = str(inst.get("challenge_type") or "")
                with st.container(border=True):
                    dl = _days_left(inst.get("end_date"))
                    chips = []
                    chips.append(_type_badge(inst.get("challenge_type")))
                    if dl >= 0:
                        chips.append(f"D-{dl}")
                    chips_html = " ".join([f'<span class="amf-chip">{_html.escape(str(c))}</span>' for c in chips])
                    ring = _progress_ring(float(prog.get("progress") or 0), "진행")
                    title_safe = _html.escape(str(inst.get("template_title") or ""))
                    range_safe = _html.escape(_fmt_range(inst.get("start_date"), inst.get("end_date")))
                    summary_safe = _html.escape(str(prog.get("summary") or "")).replace("\n", "<br/>")
                    st.markdown(
                        _dedent(
                            f"""
                            <div class="amf-card">
                              <div class="amf-row">
                                <div style="flex:1;">
                                  <div class="amf-title">{title_safe}</div>
                                  <div class="amf-sub">{range_safe}</div>
                                  <div style="margin-top:8px;">{chips_html}</div>
                                </div>
                                {ring}
                              </div>
                              <div class="amf-sub" style="margin-top:10px;">{summary_safe}</div>
                            </div>
                            """
                        ).strip(),
                        unsafe_allow_html=True,
                    )
                    st.progress(float(prog.get("progress") or 0))

                    # ✅ 핵심 지표(실사용)
                    if ctype in ("spend_cap", "reduce_category"):
                        today = date.today().isoformat()
                        start_s = str(inst.get("start_date") or today)
                        end_s = str(min(today, str(inst.get("end_date") or today)))
                        days_left = _days_remaining_inclusive(str(inst.get("end_date") or today))
                        if ctype == "spend_cap":
                            cap = float(params.get("cap_amount") or 0)
                            spent_so_far = db._sum_spend_in_range(user_id, start_s, end_s) if hasattr(db, "_sum_spend_in_range") else 0
                            spent_today = db._sum_spend_in_range(user_id, today, today) if hasattr(db, "_sum_spend_in_range") else 0
                            left = float(cap) - float(spent_so_far)
                            recommend = 0 if days_left <= 0 else int(max(0.0, left) / float(days_left))
                            st.markdown(
                                _dedent(
                                    f"""
                                    <div class="amf-kpi">
                                      <div class="k"><div class="t">남은 금액</div><div class="v">{int(max(0,left)):,}원</div></div>
                                      <div class="k"><div class="t">오늘 소비</div><div class="v">{int(spent_today):,}원</div></div>
                                      <div class="k"><div class="t">오늘 권장 사용</div><div class="v">{int(recommend):,}원</div></div>
                                    </div>
                                    """
                                ).strip(),
                                unsafe_allow_html=True,
                            )
                        else:
                            cat = str(params.get("category") or "").strip()
                            baseline = float(params.get("baseline_amount") or 0)
                            pct = float(params.get("reduction_pct") or 10)
                            target = baseline * (1.0 - (pct / 100.0))
                            cur_cat = db._sum_spend_in_range(user_id, start_s, end_s, category=cat or None) if hasattr(db, "_sum_spend_in_range") else 0
                            today_cat = db._sum_spend_in_range(user_id, today, today, category=cat or None) if hasattr(db, "_sum_spend_in_range") else 0
                            left = float(target) - float(cur_cat)
                            recommend = 0 if days_left <= 0 else int(max(0.0, left) / float(days_left))
                            st.markdown(
                                _dedent(
                                    f"""
                                    <div class="amf-kpi">
                                      <div class="k"><div class="t">남은 금액({cat or "카테고리"})</div><div class="v">{int(max(0,left)):,}원</div></div>
                                      <div class="k"><div class="t">오늘 소비({cat or "카테고리"})</div><div class="v">{int(today_cat):,}원</div></div>
                                      <div class="k"><div class="t">오늘 권장 사용</div><div class="v">{int(recommend):,}원</div></div>
                                    </div>
                                    """
                                ).strip(),
                                unsafe_allow_html=True,
                            )

                    if ctype in ("daily_save_fixed", "daily_save_increasing"):
                        start_s = str(inst.get("start_date") or date.today().isoformat())
                        end_s = str(inst.get("end_date") or date.today().isoformat())
                        saving_by_date = _sum_by_date(db, user_id, start_s, end_s, "saving")
                        try:
                            s = date.fromisoformat(start_s)
                            e = date.fromisoformat(end_s)
                        except Exception:
                            s = date.today()
                            e = date.today()
                        total = max(1, (e - s).days + 1)
                        done = 0
                        pills: list[str] = []
                        # 오늘 KPI
                        today = date.today()
                        today_s = today.isoformat()
                        idx_today = (today - s).days
                        today_saved = float(saving_by_date.get(today_s, 0) or 0)
                        if ctype == "daily_save_fixed":
                            today_req = float(params.get("daily_amount") or 0)
                        else:
                            today_req = float(params.get("start_amount") or 500) + float(params.get("daily_increment") or 100) * max(0, idx_today)
                        today_left = max(0.0, float(today_req) - float(today_saved))
                        st.markdown(
                            _dedent(
                                f"""
                                <div class="amf-kpi">
                                  <div class="k"><div class="t">오늘 목표</div><div class="v">{int(today_req):,}원</div></div>
                                  <div class="k"><div class="t">오늘 저축</div><div class="v">{int(today_saved):,}원</div></div>
                                  <div class="k"><div class="t">오늘 남은 목표</div><div class="v">{int(today_left):,}원</div></div>
                                </div>
                                """
                            ).strip(),
                            unsafe_allow_html=True,
                        )
                        bcta1, bcta2 = st.columns(2)
                        with bcta1:
                            if st.button("🐷 저축하러 가기", key=f"go_save_{inst.get('id')}", use_container_width=True, type="primary"):
                                st.switch_page("pages/8_🎯_저축_목표.py")
                        with bcta2:
                            if st.button("💰 내 지갑", key=f"go_wallet_{inst.get('id')}", use_container_width=True):
                                st.switch_page("pages/7_💰_내_지갑.py")

                        for i in range(total):
                            d = (s + timedelta(days=i)).isoformat()
                            saved = float(saving_by_date.get(d, 0) or 0)
                            if ctype == "daily_save_fixed":
                                req = float(params.get("daily_amount") or 0)
                            else:
                                req = float(params.get("start_amount") or 500) + float(params.get("daily_increment") or 100) * i
                            ok = bool(req > 0 and saved >= req)
                            if d <= date.today().isoformat() and ok:
                                done += 1
                            mark = "✅" if ok else ("⬜" if d <= date.today().isoformat() else "⏳")
                            pills.append(f"{mark} {d[5:]} · 목표 {format_korean_won(int(req))}")

                        st.caption(f"달성: **{done}/{total}일**")
                        cA, cB = st.columns(2)
                        half = (len(pills) + 1) // 2
                        with cA:
                            st.caption("\n".join(pills[:half]))
                        with cB:
                            st.caption("\n".join(pills[half:]))
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
                        else:
                            if st.button("취소", key=f"cancel_{inst.get('id')}", use_container_width=True):
                                if hasattr(db, "cancel_challenge_instance"):
                                    db.cancel_challenge_instance(int(inst["id"]), user_id=user_id)
                                st.rerun()

        st.divider()
        st.subheader("새 챌린지 시작")

        tab_spend, tab_save, tab_auto = st.tabs(["1) 소비", "2) 저축", "3) 자동저축"])

        with tab_spend:
            st.markdown("#### 1) 소비 N원 이하 도전")
            # ✅ 프리셋은 위젯 생성(number_input) 전에 session_state를 세팅해야 Streamlit 오류가 안 납니다.
            if "spend_cap" not in st.session_state:
                st.session_state["spend_cap"] = 10_000

            p1, p2, p3 = st.columns(3)
            if p1.button("1만원", use_container_width=True, key="cap_1w"):
                st.session_state["spend_cap"] = 10_000
            if p2.button("2만원", use_container_width=True, key="cap_2w"):
                st.session_state["spend_cap"] = 20_000
            if p3.button("5만원", use_container_width=True, key="cap_5w"):
                st.session_state["spend_cap"] = 50_000

            c1, c2 = st.columns(2)
            with c1:
                period = st.selectbox("기간", ["하루", "3일", "일주일"], index=2, key="spend_period")
            with c2:
                cap = st.number_input("목표 소비 상한(원)", min_value=0, step=1000, key="spend_cap")

            days = 1 if period == "하루" else (3 if period == "3일" else 7)
            start = date.today()
            end = start + timedelta(days=days - 1)
            st.caption(f"기간: **{_fmt_range(start.isoformat(), end.isoformat())}** · 목표: **{int(cap):,}원({format_korean_won(cap)}) 이하**")

            if st.button("🏁 소비 챌린지 시작", use_container_width=True, type="primary", key="start_spend_cap"):
                # 중복 시작 방지(교체 토글로 해결)
                try:
                    cur_act = db.get_challenge_instances(user_id, status="active", limit=50) or []
                    exists = any(str(x.get("challenge_type")) == "spend_cap" for x in cur_act)
                except Exception:
                    exists = False
                if exists and not st.session_state.get("replace_spend_cap"):
                    st.warning("이미 ‘소비 제한’ 챌린지를 진행 중이에요. 아래 ‘기존 챌린지 교체’ 토글을 켜고 다시 시작하세요.")
                    st.stop()
                tid = db.create_challenge_template(
                    None,
                    title=f"{period} 소비 {int(cap):,}원 이하",
                    challenge_type="spend_cap",
                    params={"cap_amount": int(cap), "days": int(days)},
                    reward_amount=0,
                    reward_coins=10,
                    created_by=None,
                )
                if st.session_state.get("replace_spend_cap"):
                    try:
                        cur_act = db.get_challenge_instances(user_id, status="active", limit=50) or []
                        for x in cur_act:
                            if str(x.get("challenge_type")) == "spend_cap":
                                if hasattr(db, "cancel_challenge_instance"):
                                    db.cancel_challenge_instance(int(x["id"]), user_id=user_id)
                    except Exception:
                        pass
                db.start_challenge(user_id, tid, start.isoformat(), end.isoformat())
                st.success("시작했어요! 기간이 끝나면 정산할 수 있어요.")
                st.rerun()

            st.toggle("기존 챌린지 교체(취소 후 새로 시작)", value=False, key="replace_spend_cap")

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
                try:
                    cur_act = db.get_challenge_instances(user_id, status="active", limit=50) or []
                    exists = any(str(x.get("challenge_type")) == "reduce_category" for x in cur_act)
                except Exception:
                    exists = False
                if exists and not st.session_state.get("replace_reduce_cat"):
                    st.warning("이미 ‘패턴 개선’ 챌린지를 진행 중이에요. 아래 ‘기존 챌린지 교체’ 토글을 켜고 다시 시작하세요.")
                    st.stop()
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
                if st.session_state.get("replace_reduce_cat"):
                    try:
                        cur_act = db.get_challenge_instances(user_id, status="active", limit=50) or []
                        for x in cur_act:
                            if str(x.get("challenge_type")) == "reduce_category":
                                if hasattr(db, "cancel_challenge_instance"):
                                    db.cancel_challenge_instance(int(x["id"]), user_id=user_id)
                    except Exception:
                        pass
                db.start_challenge(user_id, tid, start2.isoformat(), end2.isoformat())
                st.success("시작했어요! 기간이 끝나면 정산할 수 있어요.")
                st.rerun()

            st.toggle("기존 챌린지 교체(취소 후 새로 시작)", value=False, key="replace_reduce_cat")

        with tab_save:
            st.markdown("#### 1) 하루 500원 저축(고정)")
            fixed_amt = st.number_input("하루 저축(원)", min_value=0, step=100, value=500, key="save_fixed_amt")
            fixed_days = st.selectbox("기간", ["3일", "일주일"], index=1, key="save_fixed_days")
            d = 3 if fixed_days == "3일" else 7
            start = date.today()
            end = start + timedelta(days=d - 1)
            st.caption(f"기간: **{_fmt_range(start.isoformat(), end.isoformat())}** · 하루 **{int(fixed_amt):,}원({format_korean_won(fixed_amt)})**")
            st.caption("버튼을 누르면 ‘하루 저축(고정)’ 챌린지가 시작돼요.")
            if st.button("🏁 챌린지 시작", use_container_width=True, type="primary", key="start_daily_save_fixed"):
                try:
                    cur_act = db.get_challenge_instances(user_id, status="active", limit=50) or []
                    exists = any(str(x.get("challenge_type")) == "daily_save_fixed" for x in cur_act)
                except Exception:
                    exists = False
                if exists and not st.session_state.get("replace_save_fixed"):
                    st.warning("이미 ‘하루 저축(고정)’ 챌린지를 진행 중이에요. 아래 ‘기존 챌린지 교체’ 토글을 켜고 다시 시작하세요.")
                    st.stop()
                tid = db.create_challenge_template(
                    None,
                    title=f"{d}일 매일 {int(fixed_amt):,}원 저축",
                    challenge_type="daily_save_fixed",
                    params={"daily_amount": int(fixed_amt), "days": int(d)},
                    reward_amount=0,
                    reward_coins=15,
                    created_by=None,
                )
                if st.session_state.get("replace_save_fixed"):
                    try:
                        cur_act = db.get_challenge_instances(user_id, status="active", limit=50) or []
                        for x in cur_act:
                            if str(x.get("challenge_type")) == "daily_save_fixed":
                                if hasattr(db, "cancel_challenge_instance"):
                                    db.cancel_challenge_instance(int(x["id"]), user_id=user_id)
                    except Exception:
                        pass
                db.start_challenge(user_id, tid, start.isoformat(), end.isoformat())
                st.success("시작했어요! 매일 저축 기록을 남기면 달성돼요.")
                st.rerun()

            st.toggle("기존 챌린지 교체(취소 후 새로 시작)", value=False, key="replace_save_fixed")

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
            st.caption("버튼을 누르면 ‘늘리는 저축’ 챌린지가 시작돼요.")
            if st.button("🏁 챌린지 시작", use_container_width=True, type="primary", key="start_daily_save_inc"):
                try:
                    cur_act = db.get_challenge_instances(user_id, status="active", limit=50) or []
                    exists = any(str(x.get("challenge_type")) == "daily_save_increasing" for x in cur_act)
                except Exception:
                    exists = False
                if exists and not st.session_state.get("replace_save_inc"):
                    st.warning("이미 ‘늘리는 저축’ 챌린지를 진행 중이에요. 아래 ‘기존 챌린지 교체’ 토글을 켜고 다시 시작하세요.")
                    st.stop()
                tid = db.create_challenge_template(
                    None,
                    title=f"{d2}일 늘리는 저축({int(inc_start):,}+{int(inc_step):,}/일)",
                    challenge_type="daily_save_increasing",
                    params={"start_amount": int(inc_start), "daily_increment": int(inc_step), "days": int(d2)},
                    reward_amount=0,
                    reward_coins=25,
                    created_by=None,
                )
                if st.session_state.get("replace_save_inc"):
                    try:
                        cur_act = db.get_challenge_instances(user_id, status="active", limit=50) or []
                        for x in cur_act:
                            if str(x.get("challenge_type")) == "daily_save_increasing":
                                if hasattr(db, "cancel_challenge_instance"):
                                    db.cancel_challenge_instance(int(x["id"]), user_id=user_id)
                    except Exception:
                        pass
                db.start_challenge(user_id, tid, s2.isoformat(), e2.isoformat())
                st.success("시작했어요! 매일 저축 기록을 남기면 달성돼요.")
                st.rerun()

            st.toggle("기존 챌린지 교체(취소 후 새로 시작)", value=False, key="replace_save_inc")

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

