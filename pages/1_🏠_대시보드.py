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

            /* 상단 액션(팝오버 버튼)이 입력창처럼 커지지 않게 */
            button[aria-haspopup="dialog"]{
                width: auto !important;
                min-width: 44px !important;
                border-radius: 999px !important;
                padding: 7px 12px !important;
                font-weight: 900 !important;
                background: rgba(255,255,255,0.92) !important;
                border: 1px solid var(--border) !important;
                box-shadow: var(--shadow2) !important;
            }
            button[aria-haspopup="dialog"]:hover{
                transform: translateY(-1px);
                box-shadow: var(--shadow) !important;
            }

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

            /* 빈 상태 카드 */
            .amf-empty {
                background: var(--card);
                border: 1px solid var(--border);
                border-radius: 18px;
                padding: 16px;
                box-shadow: var(--shadow2);
            }
            .amf-empty h3{
                margin: 0 0 6px 0;
                font-size: 16px;
                font-weight: 950;
                color: var(--text);
            }
            .amf-empty p{
                margin: 0;
                color: var(--muted);
                font-weight: 800;
                font-size: 13px;
                line-height: 1.45;
            }

            /* 아이 홈 hero */
            .amf-hero{
                background: linear-gradient(135deg, var(--brand1), var(--brand2));
                padding: 18px 16px;
                border-radius: 20px;
                color: white;
                box-shadow: 0 18px 40px rgba(118,75,162,0.25);
            }
            .amf-hero-label{ font-weight: 900; opacity: 0.92; }
            .amf-hero-value{
                font-size: 46px;
                font-weight: 950;
                letter-spacing: -0.8px;
                margin-top: 2px;
                line-height: 1.05;
            }
            .amf-hero-sub{
                margin-top: 6px;
                opacity: 0.9;
                font-weight: 800;
                font-size: 13px;
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

            /* ✅ Mobile-first tweaks */
            @media (max-width: 768px){
                .block-container { padding-top: 0.6rem !important; padding-left: 0.9rem !important; padding-right: 0.9rem !important; }
                .amf-title { font-size: 22px; }
                .amf-sub { font-size: 12px; }
                .amf-chip { font-size: 11px; padding: 6px 10px; }
                button[aria-haspopup="dialog"]{ padding: 6px 10px !important; }
                [data-testid="stMetric"]{ padding: 12px 12px !important; }
                [data-testid="stMetricValue"]{ font-size: 22px !important; }
                .amf-hero-value{ font-size: 34px; }
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
    user_type = str(user_type or "").strip().lower()
    if user_type in ("부모", "부모님", "parent", "guardian"):
        user_type = "parent"
    elif user_type in ("아이", "자녀", "child", "kid"):
        user_type = "child"
    elif user_type not in ("parent", "child"):
        user_type = "child"

    render_sidebar_menu(user_id, user_name, user_type)
    _inject_dashboard_css()

    # ✅ 레벨업 대형 연출 카드(한 번만 표시)
    ev = st.session_state.pop("levelup_event", None)
    if ev:
        before_lv = int(ev.get("before", 0) or 0)
        after_lv = int(ev.get("after", 0) or 0)
        coins_gained = int(ev.get("coins_gained", 0) or 0)
        skins = ev.get("skins_unlocked") or []
        st.markdown(
            f"""
            <div style="
              background: linear-gradient(135deg, #667eea, #764ba2);
              padding: 16px 16px;
              border-radius: 18px;
              color: white;
              box-shadow: 0 18px 40px rgba(118,75,162,0.25);
              margin-bottom: 12px;
            ">
              <div style="font-weight:950; font-size:18px;">🎉 레벨업!</div>
              <div style="margin-top:6px; font-weight:900; font-size:14px; opacity:0.95;">
                Lv.{before_lv} → Lv.{after_lv}
              </div>
              <div style="margin-top:10px; font-weight:900; font-size:13px; opacity:0.92;">
                🪙 코인 +{coins_gained}
                {(' · 🎨 스킨 해금 ' + str(len(skins)) + '개') if skins else ''}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # app bar (title)
    # ✅ 모바일 우선: 상단을 2줄 구조로(타이틀/액션) 고정
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

    st.divider()

    if user_type == "parent":
        parent_code = (user or {}).get("parent_code", "")
        children = db.get_users_by_parent_code(parent_code) if parent_code else []

        now = datetime.now()
        ym = f"{now.year}-{now.month:02d}"

        # 1) 전체 자녀 용돈 현황 요약 + (자녀별) 이번 달 통계 캐시
        total_balance = 0
        total_allowance = 0
        total_saving = 0
        total_spend = 0
        month_allowance = 0.0
        month_saving = 0.0
        month_spend = 0.0
        month_impulse = 0.0
        child_cards = []
        for ch in children:
            cid = int(ch["id"])
            cstats = _compute_balance(db, cid)
            total_balance += cstats["balance"]
            total_allowance += cstats["total_allowance"]
            total_saving += cstats["total_saving"]
            total_spend += cstats["total_spend"]

            cm_allow = 0.0
            cm_save = 0.0
            cm_spend = 0.0
            cm_impulse = 0.0
            for b in cstats["behaviors"]:
                ts = str(b.get("timestamp") or "")
                if not ts.startswith(ym):
                    continue
                t = b.get("behavior_type")
                amt = float(b.get("amount") or 0)
                if t == "allowance":
                    cm_allow += amt
                elif t == "saving":
                    cm_save += amt
                elif t == "planned_spending":
                    cm_spend += amt
                elif t == "impulse_buying":
                    cm_impulse += amt
            month_allowance += cm_allow
            month_saving += cm_save
            month_spend += cm_spend
            month_impulse += cm_impulse

            child_cards.append(
                {
                    "id": cid,
                    "name": ch.get("name") or ch.get("username") or f"ID {cid}",
                    "username": ch.get("username") or "",
                    "balance": float(cstats["balance"]),
                    "month_allowance": float(cm_allow),
                    "month_saving": float(cm_save),
                    "month_spend": float(cm_spend),
                    "month_impulse": float(cm_impulse),
                    "behaviors": cstats["behaviors"],
                }
            )

        st.markdown("### 👨‍👩‍👧 가족 요약")
        r1c1, r1c2 = st.columns(2)
        with r1c1:
            st.metric("연결된 자녀", f"{len(children)}명")
        with r1c2:
            st.metric("가족 잔액(추정)", f"{int(total_balance):,}원")
        r2c1, r2c2 = st.columns(2)
        with r2c1:
            st.metric("총 용돈(지급)", f"{int(total_allowance):,}원")
        with r2c2:
            st.metric("총 저축", f"{int(total_saving):,}원")

        st.divider()

        # 자녀가 없으면 안내/다음 액션을 먼저 보여주고 아래 섹션은 생략
        if len(children) == 0:
            st.markdown(
                """
                <div class="amf-empty">
                  <h3>아직 연결된 자녀가 없어요</h3>
                  <p>자녀가 가입할 때 부모 코드를 입력하면 자동으로 연결됩니다.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("#### 부모 코드")
            st.code(parent_code or "부모 코드 없음", language=None)
            a1, a2 = st.columns(2)
            with a1:
                if st.button("👶 자녀 관리 열기", use_container_width=True):
                    st.switch_page("pages/2_👶_자녀_관리.py")
            with a2:
                if st.button("💵 용돈 관리 열기", use_container_width=True):
                    st.switch_page("pages/3_💵_용돈_관리.py")
            return

        # ✅ 모바일 스크롤 줄이기: 탭으로 정리
        tab_overview, tab_children, tab_timeline, tab_missions = st.tabs(["요약", "자녀", "타임라인", "미션"])

        with tab_overview:
            col_a, col_b = st.columns([1.1, 0.9])
            with col_a:
                st.subheader("📉 이번 달 지출/저축")
                st.caption("‘계획 지출/충동 구매’ 기반의 통계예요.")
                m1, m2 = st.columns(2)
                with m1:
                    st.metric("계획 지출", f"{int(month_spend):,}원")
                with m2:
                    st.metric("충동 구매", f"{int(month_impulse):,}원")
                st.metric("총 지출", f"{int(month_spend + month_impulse):,}원")

                st.divider()
                x1, x2 = st.columns(2)
                with x1:
                    st.metric("이번 달 용돈(지급)", f"{int(month_allowance):,}원")
                with x2:
                    st.metric("이번 달 저축", f"{int(month_saving):,}원")
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
                    if st.button("📝 요청 승인으로 이동", use_container_width=True, key="go_req_from_dash"):
                        st.switch_page("pages/4_📝_요청_승인.py")

        with tab_children:
            st.subheader("👶 자녀별 현황")
            st.caption("자녀를 선택해서 바로 관리하거나, 용돈 지급으로 이동할 수 있어요.")
            cols = st.columns(2)
            for i, c in enumerate(child_cards):
                with cols[i % 2]:
                    with st.container(border=True):
                        st.markdown(f"**{c['name']}**")
                        if c["username"]:
                            st.caption(c["username"])
                        st.metric("잔액(추정)", f"{int(c['balance']):,}원")
                        a1, a2 = st.columns(2)
                        with a1:
                            st.caption(f"이번 달 용돈: **{int(c['month_allowance']):,}원**")
                        with a2:
                            st.caption(f"이번 달 저축: **{int(c['month_saving']):,}원**")
                        s1, s2 = st.columns(2)
                        with s1:
                            st.caption(f"계획 지출: **{int(c['month_spend']):,}원**")
                        with s2:
                            st.caption(f"충동 구매: **{int(c['month_impulse']):,}원**")

                        b1, b2 = st.columns(2)
                        with b1:
                            if st.button("👶 관리", key=f"dash_child_manage_{c['id']}", use_container_width=True):
                                st.session_state["selected_child_id"] = int(c["id"])
                                st.switch_page("pages/2_👶_자녀_관리.py")
                        with b2:
                            if st.button("💵 용돈 주기", key=f"dash_child_give_{c['id']}", use_container_width=True):
                                st.session_state["allowance_target_child_id"] = int(c["id"])
                                st.switch_page("pages/3_💵_용돈_관리.py")

        with tab_timeline:
            st.subheader("🕒 최근 가족 활동")
            timeline = []
            for c in child_cards:
                cname = c["name"]
                for b in c["behaviors"][:40]:
                    ts = str(b.get("timestamp") or "")
                    btype = b.get("behavior_type") or ""
                    amt = float(b.get("amount") or 0)
                    cat = (b.get("category") or "").strip()
                    desc = (b.get("description") or "").strip()
                    if btype == "allowance":
                        label = "💵 용돈"
                        signed = f"+{int(amt):,}원"
                    elif btype == "saving":
                        label = "🏦 저축"
                        signed = f"-{int(amt):,}원"
                    elif btype == "planned_spending":
                        label = "🧾 계획지출"
                        signed = f"-{int(amt):,}원"
                    elif btype == "impulse_buying":
                        label = "🛍️ 충동구매"
                        signed = f"-{int(amt):,}원"
                    else:
                        label = btype
                        signed = f"{int(amt):,}원" if amt else "-"
                    timeline.append(
                        {
                            "ts": ts,
                            "자녀": cname,
                            "유형": label,
                            "금액": signed,
                            "카테고리": cat,
                            "내용": desc,
                        }
                    )
            timeline.sort(key=lambda x: x.get("ts") or "", reverse=True)
            if not timeline:
                st.caption("아직 기록이 없어요.")
            else:
                for row in timeline[:10]:
                    tshort = (row.get("ts") or "")[:16]
                    line = f"**{row['자녀']}** · {tshort} · {row['유형']} · **{row['금액']}**"
                    meta = " · ".join([v for v in [row.get("카테고리") or "", row.get("내용") or ""] if v]).strip()
                    with st.container(border=True):
                        st.markdown(line)
                        if meta:
                            st.caption(meta)

        with tab_missions:
            st.subheader("✅ 미션 완료(가족)")
            rows = []
            month_missions = 0
            try:
                conn = db._get_connection()  # pylint: disable=protected-access
                cur = conn.cursor()
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='mission_assignments'")
                has_m = bool(cur.fetchone())
                if has_m:
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
                    cur.execute(
                        """
                        SELECT COUNT(*) as cnt
                        FROM mission_assignments a
                        JOIN users u ON a.user_id = u.id
                        WHERE u.parent_code = ?
                          AND u.user_type = 'child'
                          AND a.status = 'completed'
                          AND strftime('%Y-%m', a.completed_at) = ?
                        """,
                        (parent_code, ym),
                    )
                    month_missions = int((cur.fetchone() or {}).get("cnt") or 0)
            except Exception:
                rows = []
                month_missions = 0
            finally:
                try:
                    conn.close()
                except Exception:
                    pass

            if month_missions == 0:
                # fallback: 보상 기록(용돈/미션 카테고리)로 대략 추정
                try:
                    est = 0
                    for c in child_cards:
                        for b in c["behaviors"][:500]:
                            ts = str(b.get("timestamp") or "")
                            if not ts.startswith(ym):
                                continue
                            if b.get("behavior_type") == "allowance" and (b.get("category") or "").strip() == "미션":
                                est += 1
                    month_missions = est
                except Exception:
                    month_missions = 0

            st.metric("이번 달 가족 미션 완료(합계)", f"{month_missions}개")
            if not rows:
                st.caption("최근 7일 동안 완료된 미션이 아직 없어요.")
            else:
                st.dataframe(
                    [{"자녀": r["name"], "최근 7일 완료": int(r["completed"] or 0)} for r in rows],
                    use_container_width=True,
                    hide_index=True,
                )

        st.subheader("빠른 메뉴")
        q1, q2 = st.columns(2)
        with q1:
            if st.button("👶 자녀 관리", use_container_width=True):
                st.switch_page("pages/2_👶_자녀_관리.py")
        with q2:
            if st.button("💵 용돈 관리", use_container_width=True):
                st.switch_page("pages/3_💵_용돈_관리.py")
        if st.button("📊 리포트", use_container_width=True):
            st.switch_page("pages/5_📊_리포트.py")

    else:
        # 아이용 홈
        cstats = _compute_balance(db, user_id)
        me = db.get_user_by_id(user_id) or {}
        try:
            from utils.characters import get_character_by_code, get_skin_by_code
        except Exception:
            get_character_by_code = lambda _c: None  # type: ignore
            get_skin_by_code = lambda _c: None  # type: ignore
        my_char = get_character_by_code(me.get("character_code"))
        my_skin = get_skin_by_code(me.get("character_skin_code"))
        xp = 0
        try:
            xp = int(db.get_xp(user_id) or 0) if hasattr(db, "get_xp") else 0
        except Exception:
            xp = 0
        # 레벨 계산(가벼운 규칙): 20xp마다 1레벨
        lvl = max(1, xp // 20 + 1)
        into = xp % 20
        pct = into / 20.0 if 20 else 0.0

        if my_char:
            with st.container(border=True):
                nick = (me.get("character_nickname") or my_char.get("name") or "").strip()
                coins = int(me.get("coins") or 0)
                skin_label = ""
                if my_skin:
                    skin_label = f" · 스킨 {my_skin.get('emoji','🎨')} {my_skin.get('name','')}"
                st.markdown(f"### {my_char.get('emoji','🐾')} 내 캐릭터 · **{nick}**")
                st.caption(f"{my_char.get('role','')} · 레벨 {lvl} · XP {xp}{skin_label} · 🪙 {coins}")
                st.progress(pct)
        else:
            st.caption("내 캐릭터가 아직 없어요. 설정에서 선택할 수 있어요.")

        # 감정 기록(소비 전/후/오늘 기분)
        st.subheader("😊 감정 기록")
        st.caption("돈 쓰기 전/후 기분을 남기면, 머니프렌즈가 더 잘 도와줘요.")
        emotions = ["😄", "🙂", "😐", "😟", "😡", "🤩", "😴"]
        tab_pre, tab_post, tab_daily = st.tabs(["🛑 지출 전", "🛍️ 지출 후", "🌤️ 오늘 기분"])

        def _emotion_form(context: str, title: str, placeholder: str):
            with st.form(f"emotion_{context}"):
                picked = st.radio(
                    title,
                    options=emotions,
                    horizontal=True,
                    label_visibility="visible",
                )
                note = st.text_input("한 줄 메모(선택)", placeholder=placeholder)
                submitted = st.form_submit_button("기록하기", use_container_width=True, type="primary")
            if submitted:
                try:
                    db.create_emotion_log(user_id, context=context, emotion=picked, note=(note or "").strip() or None)
                    if hasattr(st, "toast"):
                        st.toast("✅ 기록했어요!", icon="😊")
                    else:
                        st.success("✅ 기록했어요!")
                    st.rerun()
                except Exception:
                    st.error("기록에 실패했어요. 잠시 후 다시 시도해주세요.")

        with tab_pre:
            _emotion_form("pre_spend", "지금 기분은 어때?", "예: 갖고 싶지만 참기 어려워…")
        with tab_post:
            _emotion_form("post_spend", "사고 나서 기분은 어때?", "예: 샀는데 좀 후회돼…")
        with tab_daily:
            _emotion_form("daily", "오늘 기분은 어때?", "예: 오늘은 기분이 좋아!")

        recent_emotions = []
        try:
            recent_emotions = db.get_emotion_logs(user_id, limit=8)
        except Exception:
            recent_emotions = []
        if recent_emotions:
            with st.expander("최근 감정 기록", expanded=False):
                for e in recent_emotions[:8]:
                    ts = str(e.get("created_at") or "")[:16].replace("T", " ")
                    ctx = e.get("context") or ""
                    ctx_kr = {"pre_spend": "지출 전", "post_spend": "지출 후", "daily": "오늘"}.get(ctx, ctx)
                    emo = e.get("emotion") or ""
                    note = (e.get("note") or "").strip()
                    line = f"{emo} **{ctx_kr}** · {ts}"
                    st.markdown(line)
                    if note:
                        st.caption(note)

        # hero card (모바일 대응을 위해 클래스 기반 스타일)
        st.markdown(
            f"""
            <div class="amf-hero">
                <div class="amf-hero-label">내 잔액</div>
                <div class="amf-hero-value">{int(cstats["balance"]):,}원</div>
                <div class="amf-hero-sub">저축 {int(cstats["total_saving"]):,}원 · 지출 {int(cstats["total_spend"]):,}원</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()

        # 이번 달 요약
        now = datetime.now()
        ym = f"{now.year}-{now.month:02d}"
        m_allow = 0.0
        m_save = 0.0
        m_spend = 0.0
        for b in cstats["behaviors"]:
            ts = str(b.get("timestamp") or "")
            if not ts.startswith(ym):
                continue
            t = b.get("behavior_type")
            amt = float(b.get("amount") or 0)
            if t == "allowance":
                m_allow += amt
            elif t == "saving":
                m_save += amt
            elif t in ("planned_spending", "impulse_buying"):
                m_spend += amt
        st.subheader("📅 이번 달 요약")
        y1, y2 = st.columns(2)
        with y1:
            st.metric("받은 용돈", f"{int(m_allow):,}원")
        with y2:
            st.metric("저축", f"{int(m_save):,}원")
        st.metric("지출", f"{int(m_spend):,}원")

        # 진행 중인 미션(오늘)
        today = date.today().isoformat()
        db.assign_daily_missions_if_needed(user_id, today)
        missions = db.get_missions_for_user(user_id, date_str=today, active_only=True)

        # ✅ 모바일 우선: 2컬럼 대신 세로 스택
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
                        # XP/레벨업 토스트(애니메이션 느낌)
                        xp_before = 0
                        lvl_before = 1
                        try:
                            xp_before = int(db.get_xp(user_id) or 0) if hasattr(db, "get_xp") else 0
                            lvl_before = max(1, xp_before // 20 + 1)
                        except Exception:
                            pass
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
                            # 레벨업 보상 처리
                            xp_after = xp_before
                            lvl_after = lvl_before
                            try:
                                xp_after = int(db.get_xp(user_id) or 0) if hasattr(db, "get_xp") else xp_before
                                lvl_after = max(1, xp_after // 20 + 1)
                            except Exception:
                                pass
                            gained_xp = max(0, xp_after - xp_before)
                            reward_info = {}
                            try:
                                reward_info = db.grant_level_rewards_if_needed(user_id) if hasattr(db, "grant_level_rewards_if_needed") else {}
                            except Exception:
                                reward_info = {}
                            coins_gained = int((reward_info or {}).get("coins_gained") or 0)
                            skins_unlocked = (reward_info or {}).get("skins_unlocked") or []

                            if hasattr(st, "toast"):
                                st.toast(f"✨ XP +{gained_xp}", icon="🧠")
                                if lvl_after > lvl_before:
                                    st.toast(f"🎉 레벨업! Lv.{lvl_before} → Lv.{lvl_after}", icon="⬆️")
                                if coins_gained:
                                    st.toast(f"🪙 코인 +{coins_gained}", icon="🪙")
                                if skins_unlocked:
                                    st.toast("🎨 새 스킨이 해금됐어요!", icon="🎨")
                            if lvl_after > lvl_before:
                                st.session_state["levelup_event"] = {
                                    "before": lvl_before,
                                    "after": lvl_after,
                                    "coins_gained": coins_gained,
                                    "skins_unlocked": skins_unlocked,
                                }
                            if lvl_after > lvl_before:
                                st.balloons()
                            st.rerun()
                        else:
                            st.info("이미 완료했거나 처리할 수 없어요.")
        if st.button("📌 미션 페이지로 이동", use_container_width=True):
            st.switch_page("pages/10_✅_미션.py")

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

        # 최근 활동(내 기록)
        st.subheader("🕒 최근 활동")
        recent = cstats["behaviors"][:10]
        if not recent:
            st.caption("아직 기록이 없어요.")
        else:
            for b in recent:
                ts = str(b.get("timestamp") or "")[:16]
                t = b.get("behavior_type") or ""
                amt = float(b.get("amount") or 0)
                cat = (b.get("category") or "").strip()
                desc = (b.get("description") or "").strip()
                if t == "allowance":
                    label = "💵 용돈"
                    signed = f"+{int(amt):,}원"
                elif t == "saving":
                    label = "🏦 저축"
                    signed = f"-{int(amt):,}원"
                elif t == "planned_spending":
                    label = "🧾 계획지출"
                    signed = f"-{int(amt):,}원"
                elif t == "impulse_buying":
                    label = "🛍️ 충동구매"
                    signed = f"-{int(amt):,}원"
                else:
                    label = t
                    signed = f"{int(amt):,}원" if amt else "-"
                with st.container(border=True):
                    st.markdown(f"{ts} · {label} · **{signed}**")
                    meta = " · ".join([v for v in [cat, desc] if v]).strip()
                    if meta:
                        st.caption(meta)

        st.divider()
        q1, q2 = st.columns(2)
        with q1:
            if st.button("💰 내 지갑", use_container_width=True):
                st.switch_page("pages/7_💰_내_지갑.py")
        with q2:
            if st.button("📝 용돈 요청", use_container_width=True):
                st.switch_page("pages/9_📝_용돈_요청.py")
        q3, q4 = st.columns(2)
        with q3:
            if st.button("🤖 AI 친구", use_container_width=True):
                st.switch_page("pages/11_🤖_AI_친구.py")
        with q4:
            if st.button("🏆 내 성장", use_container_width=True):
                st.switch_page("pages/13_🏆_내_성장.py")


if __name__ == "__main__":
    main()

