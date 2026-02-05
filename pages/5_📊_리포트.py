import streamlit as st

from datetime import datetime

from database.db_manager import DatabaseManager
from utils.menu import render_sidebar_menu, hide_sidebar_navigation
from utils.ui import render_page_header, section_label
from components.blob_character import get_blob_html


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

    render_page_header("📊 리포트", "자녀별 소비/저축 패턴과 가족 통계를 확인해요.")

    # 기간: 이번 달 기준
    now = datetime.now()
    ym = f"{now.year}-{now.month:02d}"

    # 가족 지표
    monthly = db.get_children_behavior_stats_this_month(parent_code) if parent_code else {"monthly_total": 0, "yesterday_total": 0}
    monthly_total = int(monthly.get("monthly_total") or 0)
    yesterday_total = int(monthly.get("yesterday_total") or 0)

    section_label("가족 요약")
    with st.container(border=True):
        a, b = st.columns(2)
        with a:
            st.metric("이번달 가족 저축", f"{monthly_total:,}원")
        with b:
            st.metric("어제 저축", f"{yesterday_total:,}원")
        st.metric("자녀 수", f"{len(children)}명")

    st.divider()

    section_label("최근 6개월 저축 추이")
    rows = db.get_children_monthly_savings(parent_code) if parent_code else []
    month_map = {str(r.get("month") or "").lstrip("0"): float(r.get("total_amount") or 0) for r in rows}
    # chart labels
    chart = []
    cur_m = now.month
    for i in range(5, -1, -1):
        m = (cur_m - i - 1) % 12 + 1
        chart.append({"월": f"{m}월", "저축(원)": month_map.get(str(m), 0.0)})
    with st.container(border=True):
        st.bar_chart(chart, x="월", y="저축(원)", use_container_width=True)

    st.divider()

    section_label("카테고리별 지출(이번 달)")
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
        with st.container(border=True):
            st.bar_chart(chart2, x="카테고리", y="지출(원)", use_container_width=True)

    st.divider()

    section_label("자녀별 요약")
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
    with st.container(border=True):
        st.dataframe(summary, use_container_width=True, hide_index=True)

    st.caption("잔액은 ‘용돈 지급 - 저축 - (계획/충동)지출’로 계산한 추정치입니다.")

    st.divider()

    section_label("감정 타임라인(최근)")
    st.caption("자녀가 지출 전/후 기분을 기록하면, 패턴을 더 잘 볼 수 있어요.")
    logs = []
    try:
        logs = db.get_family_emotion_logs(parent_code, limit=80) if hasattr(db, "get_family_emotion_logs") else []
    except Exception:
        logs = []
    if not logs:
        st.caption("아직 감정 기록이 없어요.")
    else:
        ctx_map = {"pre_spend": "지출 전", "post_spend": "지출 후", "daily": "오늘"}
        with st.container(border=True):
            for e in logs[:12]:
                ts = str(e.get("created_at") or "")[:16].replace("T", " ")
                child = e.get("child_name") or e.get("child_username") or "-"
                ctx = ctx_map.get(e.get("context") or "", e.get("context") or "")
                emo = str(e.get("emotion") or "").strip()
                note = (e.get("note") or "").strip()
                st.markdown(
                    f"""
                    <div style="
                      display:flex;
                      gap:12px;
                      align-items:flex-start;
                      padding: 10px 8px;
                      border-bottom: 1px dashed rgba(17,24,39,0.08);
                    ">
                      <div style="width:44px; height:44px; display:flex; align-items:center; justify-content:center;">
                        {get_blob_html(emo, size=44)}
                      </div>
                      <div style="flex:1; min-width:0;">
                        <div style="font-weight:950; color:var(--amf-text); letter-spacing:-0.2px;">{child} · {ctx}</div>
                        <div style="margin-top:2px; font-weight:700; color:var(--amf-muted); font-size:12px;">{ts}</div>
                        {f'<div style="margin-top:6px; color:var(--amf-text); font-weight:700; font-size:13px; white-space:pre-wrap;">{note}</div>' if note else ''}
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.divider()

    st.subheader("🧯 충동구매/리스크 시그널(최근)")
    st.caption("아이가 ‘잠깐 멈추기’를 사용했거나, 충동 신호가 감지된 기록이에요.")
    sigs = []
    try:
        sigs = db.get_family_risk_signals(parent_code, limit=80) if hasattr(db, "get_family_risk_signals") else []
    except Exception:
        sigs = []
    if not sigs:
        st.caption("리스크 시그널이 아직 없어요.")
    else:
        type_map = {"impulse_stop": "멈추기 성공", "impulse_request": "충동 의심 요청", "request": "요청"}
        rows3 = []
        for s in sigs[:60]:
            ts = str(s.get("created_at") or "")[:16].replace("T", " ")
            rows3.append(
                {
                    "시간": ts,
                    "자녀": s.get("child_name") or s.get("child_username") or "-",
                    "유형": type_map.get(s.get("signal_type") or "", s.get("signal_type") or ""),
                    "점수": int(s.get("score") or 0),
                    "컨텍스트": s.get("context") or "",
                    "메모": (s.get("note") or "").strip(),
                }
            )
        st.dataframe(rows3, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()

