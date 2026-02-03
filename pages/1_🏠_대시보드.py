import streamlit as st

from datetime import date, datetime

from database.db_manager import DatabaseManager
from utils.menu import render_sidebar_menu, hide_sidebar_navigation


def _safe_seed_defaults(db: DatabaseManager) -> None:
    """
    Streamlit Cloud에서 db_manager.py가 구버전일 때(메서드 없음)도
    페이지가 죽지 않도록 기본 미션/배지를 직접 시드합니다.
    """
    if hasattr(db, "seed_default_missions_and_badges"):
        try:
            db.seed_default_missions_and_badges()
        except Exception:
            pass
        return

    # fallback: 직접 SQL로 시드(테이블이 있으면)
    try:
        conn = db._get_connection()  # pylint: disable=protected-access
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='mission_templates'")
        if not cur.fetchone():
            return
        cur.execute("SELECT COUNT(*) as cnt FROM mission_templates")
        if int(cur.fetchone()["cnt"] or 0) == 0:
            templates = [
                ("오늘은 저금통에 1,000원 저축하기", "저축(saving) 기록을 남겨요", "easy", 500),
                ("계획 지출 1건 기록하기", "planned_spending으로 지출을 계획해요", "normal", 300),
                ("가격 비교 해보기", "comparing_prices 활동을 해봐요", "easy", 200),
                ("충동 구매 참기", "delayed_gratification 활동을 해봐요", "hard", 700),
            ]
            cur.executemany(
                """
                INSERT INTO mission_templates (parent_code, title, description, difficulty, reward_amount, is_active)
                VALUES (NULL, ?, ?, ?, ?, 1)
                """,
                templates,
            )
            conn.commit()

        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='badges'")
        if cur.fetchone():
            cur.execute("SELECT COUNT(*) as cnt FROM badges")
            if int(cur.fetchone()["cnt"] or 0) == 0:
                badges = [
                    ("xp_10", "새싹 경제가", "활동을 10번 완료했어요", "🌱", 10),
                    ("xp_50", "성실한 저축가", "활동을 50번 완료했어요", "💎", 50),
                    ("xp_100", "금융 마스터", "활동을 100번 완료했어요", "🏆", 100),
                ]
                cur.executemany(
                    "INSERT INTO badges (code, title, description, icon, required_xp) VALUES (?, ?, ?, ?, ?)",
                    badges,
                )
                conn.commit()
    except Exception:
        pass
    finally:
        try:
            conn.close()
        except Exception:
            pass


def _safe_get_pending_requests(db: DatabaseManager, parent_code: str) -> list:
    """Cloud 구버전 DB 매니저에서도 요청 목록을 안전하게 가져오기"""
    if not parent_code:
        return []
    if hasattr(db, "get_requests_for_parent"):
        try:
            return db.get_requests_for_parent(parent_code, status="pending")
        except Exception:
            return []

    # fallback SQL
    try:
        conn = db._get_connection()  # pylint: disable=protected-access
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='requests'")
        if not cur.fetchone():
            return []
        cur.execute(
            """
            SELECT r.*, u.name as child_name, u.username as child_username
            FROM requests r
            JOIN users u ON r.child_id = u.id
            WHERE r.parent_code = ? AND r.status = 'pending'
            ORDER BY r.created_at DESC
            """,
            (parent_code,),
        )
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    except Exception:
        return []
    finally:
        try:
            conn.close()
        except Exception:
            pass


def _guard_login() -> bool:
    if not st.session_state.get("logged_in"):
        st.switch_page("app.py")
        return False
    return True


def _compute_balance(db: DatabaseManager, user_id: int) -> dict:
    behaviors = db.get_user_behaviors(user_id, limit=2000)
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

def _inject_dashboard_css():
    st.markdown(
        """
        <style>
            :root{
                --bg:#f5f6fb;
                --card:#ffffff;
                --text:#111827;
                --muted:#6b7280;
                --border:rgba(17,24,39,0.08);
                --shadow:0 18px 45px rgba(17,24,39,0.08);
                --shadow2:0 10px 24px rgba(17,24,39,0.06);
                --brand1:#667eea;
                --brand2:#764ba2;
            }

            /* page background + container width */
            .stApp { background: var(--bg) !important; }
            .block-container { max-width: 1200px !important; padding-top: 0.9rem !important; }

            /* remove default chrome for app-like feel */
            [data-testid="stToolbar"], #MainMenu, footer { display:none !important; }
            /* 헤더는 남겨서 사이드바 토글(>>)이 보이도록 */
            header { background: transparent !important; }

            /* typography */
            h1, h2, h3 { letter-spacing: -0.3px; color: var(--text); }
            .amf-kicker { color: var(--muted); font-weight: 800; font-size: 12px; }
            .amf-title { font-size: 28px; font-weight: 950; margin: 0; }
            .amf-sub { margin-top: 6px; color: var(--muted); font-weight: 800; font-size: 13px; }

            /* app bar */
            .amf-appbar {
                display:flex;
                align-items:flex-start;
                justify-content:space-between;
                gap: 12px;
                margin-bottom: 14px;
            }
            .amf-chip {
                display:inline-flex;
                align-items:center;
                gap:8px;
                padding: 7px 12px;
                border-radius: 999px;
                background: rgba(255,255,255,0.92);
                border: 1px solid var(--border);
                box-shadow: var(--shadow2);
                font-weight: 900;
                font-size: 12px;
                color: #374151;
                white-space: nowrap;
            }
            .amf-chip strong { color: var(--text); }

            /* metric cards */
            [data-testid="stMetric"]{
                background: var(--card) !important;
                border: 1px solid var(--border) !important;
                border-radius: 18px !important;
                padding: 14px 14px !important;
                box-shadow: var(--shadow2) !important;
            }
            [data-testid="stMetricLabel"] { color: var(--muted) !important; font-weight: 900 !important; }
            [data-testid="stMetricValue"] { color: var(--text) !important; font-weight: 950 !important; letter-spacing: -0.4px; }

            /* containers with border=True */
            div[data-testid="stVerticalBlockBorderWrapper"]{
                border-radius: 18px !important;
                border: 1px solid var(--border) !important;
                background: var(--card) !important;
                box-shadow: var(--shadow2) !important;
            }

            /* buttons */
            .stButton > button{
                border-radius: 14px !important;
                font-weight: 900 !important;
                padding: 10px 14px !important;
            }
            .stButton > button[kind="primary"], button[kind="primary"], button[data-testid="baseButton-primary"]{
                background: linear-gradient(135deg, var(--brand1), var(--brand2)) !important;
                border: none !important;
                color: white !important;
                box-shadow: 0 12px 26px rgba(102,126,234,0.22) !important;
            }
            .stButton > button[kind="primary"]:hover, button[kind="primary"]:hover, button[data-testid="baseButton-primary"]:hover{
                transform: translateY(-1px);
                box-shadow: 0 16px 34px rgba(102,126,234,0.30) !important;
            }

            /* info/warning/success */
            [data-testid="stAlert"]{
                border-radius: 16px !important;
                border: 1px solid var(--border) !important;
                box-shadow: var(--shadow2) !important;
            }

            /* progress bar */
            [data-testid="stProgress"] > div > div{
                background: linear-gradient(135deg, var(--brand1), var(--brand2)) !important;
            }

            /* tab list pill (used elsewhere) */
            .stTabs [data-baseweb="tab-list"]{
                background:#eef0f5;
                border-radius: 16px;
                padding: 6px;
                gap: 8px;
            }
            .stTabs [data-baseweb="tab"]{
                border-radius: 14px;
                font-weight: 900;
            }
            .stTabs [aria-selected="true"]{
                background: white;
                box-shadow: 0 10px 22px rgba(17,24,39,0.08);
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main():
    if not _guard_login():
        return

    hide_sidebar_navigation()
    db = DatabaseManager()
    _safe_seed_defaults(db)
    # ✅ 스케줄러 대체: 앱 진입 시 정기용돈 자동 실행
    try:
        db.run_due_recurring_allowances()
    except Exception:
        pass

    user_id = int(st.session_state.get("user_id"))
    user_name = st.session_state.get("user_name", "사용자")
    user = db.get_user_by_id(user_id)
    user_type = (user or {}).get("user_type", st.session_state.get("user_type", "child"))

    render_sidebar_menu(user_id, user_name, user_type)
    _inject_dashboard_css()

    # app bar (title + date + notifications)
    if hasattr(db, "get_notifications"):
        try:
            unread = db.get_notifications(user_id, unread_only=True, limit=20)
        except Exception:
            unread = []
    else:
        unread = []
    unread_count = len(unread)
    left, right = st.columns([0.68, 0.32])
    with left:
        st.markdown(
            f"""
            <div class="amf-appbar">
              <div>
                <div class="amf-kicker">AI Money Friends</div>
                <div class="amf-title">안녕하세요, {user_name}님 👋</div>
                <div class="amf-sub">오늘도 한 걸음씩 돈 관리 실력을 키워봐요</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        top0, top1, top2 = st.columns([1, 1, 1])
        with top0:
            with st.popover("☰", use_container_width=True):
                st.markdown("**메뉴**")
                items = []
                if user_type == "parent":
                    items = [
                        ("🏠 대시보드", "pages/1_🏠_대시보드.py"),
                        ("👶 자녀 관리", "pages/2_👶_자녀_관리.py"),
                        ("💵 용돈 관리", "pages/3_💵_용돈_관리.py"),
                        ("📝 요청 승인", "pages/4_📝_요청_승인.py"),
                        ("📊 리포트", "pages/5_📊_리포트.py"),
                        ("⚙️ 설정", "pages/6_⚙️_설정.py"),
                    ]
                else:
                    items = [
                        ("🏠 홈", "pages/1_🏠_대시보드.py"),
                        ("💰 내 지갑", "pages/7_💰_내_지갑.py"),
                        ("🎯 저축 목표", "pages/8_🎯_저축_목표.py"),
                        ("📝 용돈 요청", "pages/9_📝_용돈_요청.py"),
                        ("✅ 미션", "pages/10_✅_미션.py"),
                        ("🤖 AI 친구", "pages/11_🤖_AI_친구.py"),
                        ("📚 경제 교실", "pages/12_📚_경제_교실.py"),
                        ("🏆 내 성장", "pages/13_🏆_내_성장.py"),
                        ("⚙️ 설정", "pages/6_⚙️_설정.py"),
                    ]

                for label, path in items:
                    if st.button(label, use_container_width=True, key=f"dash_menu_{label}"):
                        st.switch_page(path)
        with top1:
            st.markdown(f"<div class='amf-chip'>📅 <strong>{datetime.now().strftime('%Y.%m.%d')}</strong></div>", unsafe_allow_html=True)
        with top2:
            label = f"🔔 {unread_count}" if unread_count else "🔔"
            with st.popover(label, use_container_width=True):
                st.markdown("**알림**")
                if not unread:
                    st.caption("새 알림이 없어요.")
                else:
                    for n in unread[:8]:
                        lvl = (n.get("level") or "info").lower()
                        title = n.get("title") or ""
                        body = n.get("body") or ""
                        if lvl == "success":
                            st.success(f"**{title}**\n\n{body}")
                        elif lvl == "warning":
                            st.warning(f"**{title}**\n\n{body}")
                        else:
                            st.info(f"**{title}**\n\n{body}")
                        if st.button("읽음", key=f"read_notif_{n['id']}", use_container_width=True):
                            if hasattr(db, "mark_notification_read"):
                                try:
                                    db.mark_notification_read(int(n["id"]))
                                except Exception:
                                    pass
                            st.rerun()

    st.divider()

    if user_type == "parent":
        parent_code = (user or {}).get("parent_code", "")
        children = db.get_users_by_parent_code(parent_code) if parent_code else []

        # 1) 전체 자녀 용돈 현황 요약
        total_balance = 0
        total_allowance = 0
        total_saving = 0
        total_spend = 0
        for ch in children:
            cstats = _compute_balance(db, int(ch["id"]))
            total_balance += cstats["balance"]
            total_allowance += cstats["total_allowance"]
            total_saving += cstats["total_saving"]
            total_spend += cstats["total_spend"]

        st.markdown("### 👨‍👩‍👧 가족 요약")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("연결된 자녀", f"{len(children)}명")
        with c2:
            st.metric("가족 잔액(추정)", f"{int(total_balance):,}원")
        with c3:
            st.metric("총 용돈(지급)", f"{int(total_allowance):,}원")
        with c4:
            st.metric("총 저축", f"{int(total_saving):,}원")

        st.divider()

        # 2) 이번 달 지출 통계(가족)
        now = datetime.now()
        ym = f"{now.year}-{now.month:02d}"
        month_spend = 0
        month_impulse = 0
        for ch in children:
            beh = db.get_user_behaviors(int(ch["id"]), limit=2000)
            for b in beh:
                ts = str(b.get("timestamp") or "")
                if not ts.startswith(ym):
                    continue
                if b.get("behavior_type") == "planned_spending":
                    month_spend += float(b.get("amount") or 0)
                elif b.get("behavior_type") == "impulse_buying":
                    month_impulse += float(b.get("amount") or 0)

        col_a, col_b = st.columns([1.15, 0.85])
        with col_a:
            st.subheader("📉 이번 달 지출")
            st.caption("‘계획 지출/충동 구매’ 기반의 통계예요.")
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("계획 지출", f"{int(month_spend):,}원")
            with m2:
                st.metric("충동 구매", f"{int(month_impulse):,}원")
            with m3:
                st.metric("총 지출", f"{int(month_spend + month_impulse):,}원")
        with col_b:
            st.subheader("🧯 긴급 알림")
            pending = _safe_get_pending_requests(db, parent_code)
            if not pending:
                st.success("대기 중인 요청이 없어요.")
            else:
                st.warning(f"대기 중 요청 {len(pending)}건")
                for r in pending[:3]:
                    amount = int(r.get("amount") or 0)
                    rt = "용돈" if r.get("request_type") == "allowance" else "지출"
                    st.markdown(f"- **{r.get('child_name')}** · {amount:,}원 · {rt}")
                if st.button("📝 요청 승인으로 이동", use_container_width=True):
                    st.switch_page("pages/4_📝_요청_승인.py")

        st.divider()

        # 3) 최근 미션 완료 현황(가족) - 간단: 최근 7일 완료 수
        st.subheader("✅ 최근 7일 미션 완료")
        # mission_assignments는 새로 추가된 테이블: 직접 SQL로 최근 완료 수 요약
        conn = db._get_connection()  # internal 사용(페이지 전용)
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT u.name, COUNT(a.id) as completed
                FROM mission_assignments a
                JOIN users u ON a.user_id = u.id
                WHERE u.parent_code = ?
                  AND u.user_type = 'child'
                  AND a.status = 'completed'
                  AND a.completed_at >= datetime('now', '-7 days')
                GROUP BY u.name
                ORDER BY completed DESC
                """,
                (parent_code,),
            )
            rows = cur.fetchall()
        except Exception:
            rows = []
        finally:
            conn.close()

        if not rows:
            st.caption("최근 7일 동안 완료된 미션이 아직 없어요.")
        else:
            st.dataframe(
                [{"자녀": r["name"], "최근 7일 완료": int(r["completed"] or 0)} for r in rows],
                use_container_width=True,
                hide_index=True,
            )

        st.divider()
        st.subheader("빠른 메뉴")
        q1, q2, q3 = st.columns(3)
        with q1:
            if st.button("👶 자녀 관리", use_container_width=True):
                st.switch_page("pages/2_👶_자녀_관리.py")
        with q2:
            if st.button("💵 용돈 관리", use_container_width=True):
                st.switch_page("pages/3_💵_용돈_관리.py")
        with q3:
            if st.button("📊 리포트", use_container_width=True):
                st.switch_page("pages/5_📊_리포트.py")

    else:
        # 아이용 대시보드
        cstats = _compute_balance(db, user_id)

        # hero card
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, var(--brand1), var(--brand2));
                padding: 18px 16px;
                border-radius: 20px;
                color: white;
                box-shadow: 0 18px 40px rgba(118,75,162,0.25);
            ">
                <div style="font-weight:900; opacity:0.92;">내 잔액</div>
                <div style="font-size:46px; font-weight:950; letter-spacing:-0.8px; margin-top:2px;">
                    {int(cstats["balance"]):,}원
                </div>
                <div style="margin-top:6px; opacity:0.9; font-weight:800; font-size:13px;">
                    저축 {int(cstats["total_saving"]):,}원 · 지출 {int(cstats["total_spend"]):,}원
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()

        # 진행 중인 미션(오늘)
        today = date.today().isoformat()
        db.assign_daily_missions_if_needed(user_id, today)
        missions = db.get_missions_for_user(user_id, date_str=today, active_only=True)

        left, right = st.columns([1.15, 0.85])
        with left:
            st.subheader("✅ 오늘의 미션")
            if not missions:
                st.caption("오늘의 미션이 없어요.")
            else:
                for m in missions:
                    with st.container(border=True):
                        st.markdown(f"**{m.get('title')}**")
                        if m.get("description"):
                            st.caption(m.get("description"))
                        st.caption(f"난이도: {m.get('difficulty')} · 보상: {int(m.get('reward_amount') or 0):,}원")
                        if st.button("완료!", key=f"complete_m_{m['id']}", use_container_width=True):
                            ok = db.complete_mission(int(m["id"]))
                            if ok:
                                reward = float(m.get("reward_amount") or 0)
                                if reward > 0:
                                    db.save_behavior_v2(
                                        user_id,
                                        "allowance",
                                        reward,
                                        description="미션 보상",
                                        category="미션",
                                    )
                                db.create_notification(user_id, "미션 완료!", f"보상 {int(reward):,}원을 받았어요.", level="success")
                                db.award_badges_if_needed(user_id)
                                st.balloons()
                                st.rerun()
                            else:
                                st.info("이미 완료했거나 처리할 수 없어요.")
                if st.button("📌 미션 페이지로 이동", use_container_width=True):
                    st.switch_page("pages/10_✅_미션.py")

        with right:
            st.subheader("🎯 저축 목표")
            goals = db.get_goals(user_id, active_only=True)
            if not goals:
                st.caption("아직 목표가 없어요.")
                if st.button("목표 만들기", use_container_width=True):
                    st.switch_page("pages/8_🎯_저축_목표.py")
            else:
                g = goals[0]
                progress = db.get_goal_progress(int(g["id"]))
                target = float(g.get("target_amount") or 0)
                pct = 0 if target <= 0 else min(1.0, progress / target)
                st.markdown(f"**{g.get('title')}**")
                st.progress(pct)
                st.caption(f"{int(progress):,}원 / {int(target):,}원")
                if st.button("목표 관리", use_container_width=True):
                    st.switch_page("pages/8_🎯_저축_목표.py")

        st.divider()

        # AI 친구의 오늘의 조언(룰 기반)
        st.subheader("🤖 AI 친구의 오늘의 조언")
        spend_ratio = 0 if (cstats["total_allowance"] or 0) <= 0 else (cstats["total_spend"] / cstats["total_allowance"])
        if spend_ratio > 0.6:
            tip = "이번 달에는 지출이 조금 많아요. ‘계획 지출’을 먼저 적어보면 도움이 돼요!"
        elif cstats["total_saving"] > cstats["total_spend"]:
            tip = "저축을 정말 잘하고 있어요! 목표를 하나 더 만들어볼까요?"
        else:
            tip = "오늘은 작은 미션부터 해보자! 저금통에 1,000원 넣기 어때요?"
        st.info(tip)

        st.divider()
        q1, q2, q3, q4 = st.columns(4)
        with q1:
            if st.button("💰 내 지갑", use_container_width=True):
                st.switch_page("pages/7_💰_내_지갑.py")
        with q2:
            if st.button("📝 용돈 요청", use_container_width=True):
                st.switch_page("pages/9_📝_용돈_요청.py")
        with q3:
            if st.button("🤖 AI 친구", use_container_width=True):
                st.switch_page("pages/11_🤖_AI_친구.py")
        with q4:
            if st.button("🏆 내 성장", use_container_width=True):
                st.switch_page("pages/13_🏆_내_성장.py")


if __name__ == "__main__":
    main()

