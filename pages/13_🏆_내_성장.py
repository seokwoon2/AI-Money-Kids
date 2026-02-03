import streamlit as st

import pandas as pd
import plotly.express as px

from datetime import datetime
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


def _level_from_xp(xp: int) -> tuple[int, int, int]:
    # 간단 레벨: 0~9 = Lv1, 10~29=Lv2, 30~59=Lv3, 60~99=Lv4, ...
    thresholds = [0, 10, 30, 60, 100, 150, 220]
    level = 1
    for i, t in enumerate(thresholds):
        if xp >= t:
            level = i + 1
    next_t = thresholds[level] if level < len(thresholds) else thresholds[-1] + 100
    prev_t = thresholds[level - 1] if level - 1 < len(thresholds) else thresholds[-1]
    return level, prev_t, next_t


def main():
    if not _guard_child():
        return

    hide_sidebar_navigation()
    db = DatabaseManager()

    user_id = int(st.session_state.get("user_id"))
    user_name = st.session_state.get("user_name", "사용자")
    render_sidebar_menu(user_id, user_name, "child")

    db.award_badges_if_needed(user_id)

    st.title("🏆 내 성장")
    st.caption("활동/미션을 완료할수록 레벨이 오르고 배지를 모을 수 있어요.")

    xp = db.get_xp(user_id)
    level, prev_t, next_t = _level_from_xp(xp)
    prog = 0 if next_t == prev_t else min(1.0, (xp - prev_t) / (next_t - prev_t))

    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,#111827,#374151); color:white; border-radius:18px; padding:18px 16px;">
            <div style="font-weight:900; opacity:0.9;">Lv.{level} · {user_name}</div>
            <div style="font-size:34px; font-weight:900; letter-spacing:-0.6px; margin-top:4px;">
                XP {xp}
            </div>
            <div style="margin-top:8px;">다음 레벨까지 {max(0, next_t - xp)} XP</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(prog)

    st.divider()
    st.subheader("한눈에 보기(원형 그래프)")

    # 기간 선택(기본: 30일)
    period_label = st.segmented_control(
        "기간",
        options=["7일", "30일", "90일"],
        default="30일",
        key="growth_period",
    )
    days = 30
    if period_label == "7일":
        days = 7
    elif period_label == "90일":
        days = 90

    # 데이터 로드
    try:
        conn = db._get_connection()  # pylint: disable=protected-access
        behaviors = pd.read_sql_query(
            """
            SELECT behavior_type, amount, category, timestamp
            FROM behaviors
            WHERE user_id = ?
              AND datetime(timestamp) >= datetime('now', ?)
            """,
            conn,
            params=(int(user_id), f"-{int(days)} day"),
        )
        emotions = pd.read_sql_query(
            """
            SELECT emotion, context, created_at
            FROM emotion_logs
            WHERE user_id = ?
              AND datetime(created_at) >= datetime('now', ?)
            """,
            conn,
            params=(int(user_id), f"-{int(days)} day"),
        )
        conn.close()
    except Exception:
        try:
            conn.close()
        except Exception:
            pass
        behaviors = pd.DataFrame(columns=["behavior_type", "amount", "category", "timestamp"])
        emotions = pd.DataFrame(columns=["emotion", "context", "created_at"])

    behaviors["amount"] = pd.to_numeric(behaviors.get("amount"), errors="coerce").fillna(0)

    # 소비/저축(금액) 도넛
    saving_total = float(behaviors.loc[behaviors["behavior_type"] == "saving", "amount"].sum() or 0)
    spending_types = ["planned_spending", "impulse_buying"]
    spending_total = float(behaviors.loc[behaviors["behavior_type"].isin(spending_types), "amount"].sum() or 0)

    donut1 = pd.DataFrame(
        [
            {"구분": "저축", "금액": max(0.0, saving_total)},
            {"구분": "소비", "금액": max(0.0, spending_total)},
        ]
    )

    # 소비 유형(금액) 도넛: planned vs impulse (금액 기준)
    spend_by_type = (
        behaviors.loc[behaviors["behavior_type"].isin(spending_types)]
        .groupby("behavior_type", as_index=False)["amount"]
        .sum()
    )
    if not spend_by_type.empty:
        spend_by_type["유형"] = spend_by_type["behavior_type"].map(
            {"planned_spending": "계획 소비", "impulse_buying": "충동 소비"}
        ).fillna(spend_by_type["behavior_type"])
        donut2 = spend_by_type.rename(columns={"amount": "금액"})[["유형", "금액"]]
    else:
        donut2 = pd.DataFrame(columns=["유형", "금액"])

    # 기분(감정 빈도) 도넛: daily 우선, 없으면 전체 context
    emo_src = emotions.copy()
    if not emo_src.empty and (emo_src["context"] == "daily").any():
        emo_src = emo_src.loc[emo_src["context"] == "daily"]
    emo_counts = (
        emo_src.groupby("emotion", as_index=False)
        .size()
        .rename(columns={"emotion": "기분", "size": "횟수"})
        .sort_values("횟수", ascending=False)
    )
    if len(emo_counts) > 6:
        top = emo_counts.head(6).copy()
        other_cnt = int(emo_counts["횟수"].sum() - top["횟수"].sum())
        emo_counts = pd.concat([top, pd.DataFrame([{"기분": "기타", "횟수": other_cnt}])], ignore_index=True)

    layout_mode = st.session_state.get("layout_mode", "auto")
    cols = st.columns(1 if layout_mode == "mobile" else 3)

    def _render_donut(fig, title: str):
        fig.update_traces(textinfo="percent+label", textposition="inside")
        fig.update_layout(
            title={"text": title, "x": 0.0, "xanchor": "left"},
            margin=dict(l=6, r=6, t=46, b=6),
            showlegend=False,
            height=260 if layout_mode == "mobile" else 280,
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with cols[0]:
        if float(donut1["금액"].sum() or 0) <= 0:
            st.caption("최근 기간에 소비/저축 기록이 없어요.")
        else:
            fig1 = px.pie(
                donut1,
                names="구분",
                values="금액",
                hole=0.62,
                color="구분",
                color_discrete_map={"저축": "#10B981", "소비": "#EF4444"},
            )
            _render_donut(fig1, f"소비 vs 저축(금액) · 최근 {days}일")

    with cols[1 if len(cols) > 1 else 0]:
        if donut2.empty or float(donut2["금액"].sum() or 0) <= 0:
            st.caption("최근 기간에 소비 유형 데이터가 부족해요.")
        else:
            fig2 = px.pie(
                donut2,
                names="유형",
                values="금액",
                hole=0.62,
                color="유형",
                color_discrete_map={"계획 소비": "#3B82F6", "충동 소비": "#F59E0B"},
            )
            _render_donut(fig2, f"소비 유형(금액) · 최근 {days}일")

    with cols[2 if len(cols) > 2 else 0]:
        if emo_counts.empty or int(emo_counts["횟수"].sum() or 0) <= 0:
            st.caption("최근 기간에 기분 기록이 없어요.")
        else:
            fig3 = px.pie(
                emo_counts,
                names="기분",
                values="횟수",
                hole=0.62,
            )
            _render_donut(fig3, f"기분 분포(횟수) · 최근 {days}일")

    st.divider()
    st.subheader("배지")
    badges = db.get_user_badges(user_id)
    if not badges:
        st.caption("아직 배지가 없어요. 미션을 완료해보자!")
    else:
        for b in badges[:20]:
            icon = b.get("icon") or "🏅"
            st.markdown(f"- {icon} **{b.get('title')}** · {b.get('description')}")

    st.divider()
    st.subheader("추천 액션")
    # ✅ 모바일 우선: 3열 → 2열 + 단일
    c1, c2 = st.columns(2)
    with c1:
        if st.button("✅ 미션 하러 가기", use_container_width=True):
            st.switch_page("pages/10_✅_미션.py")
    with c2:
        if st.button("🎯 목표 저축하기", use_container_width=True):
            st.switch_page("pages/8_🎯_저축_목표.py")
    if st.button("📚 경제 교실", use_container_width=True):
        st.switch_page("pages/12_📚_경제_교실.py")


if __name__ == "__main__":
    main()

