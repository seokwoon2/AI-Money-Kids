import streamlit as st

from datetime import date, datetime
from pathlib import Path

from database.db_manager import DatabaseManager
from utils.menu import render_sidebar_menu, hide_sidebar_navigation


def _resolve_asset_path(rel_path: str) -> str:
    """
    pages/ 아래 파일에서 실행되더라도 assets 경로가 깨지지 않게
    레포 루트 기준으로 한 번 더 해석합니다.
    """
    p = Path(rel_path)
    if p.is_file():
        return str(p)
    return str((Path(__file__).resolve().parents[1] / rel_path).resolve())


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
                ("오늘은 저금통에 1,000원 저축하기", "저축 기록을 남겨요", "easy", 500),
                ("계획 지출 1건 기록하기", "계획 소비로 지출을 계획해요", "normal", 300),
                ("가격 비교 해보기", "가격 비교 활동을 해봐요", "easy", 200),
                ("충동 구매 참기", "충동구매를 잠깐 참아봐요", "hard", 700),
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


def _ko_mission_desc(desc: str | None) -> str:
    """DB에 영문 키워드가 남아있어도 화면은 한글로 보이게"""
    if not desc:
        return ""
    s = str(desc)
    s = s.replace("planned_spending으로", "계획 소비로")
    s = s.replace("comparing_prices 활동", "가격 비교 활동")
    s = s.replace("delayed_gratification 활동", "참기 활동")
    s = s.replace("impulse_buying", "충동 소비")
    s = s.replace("저축(saving)", "저축")
    for k, v in {
        "planned_spending": "계획 소비",
        "saving": "저축",
        "comparing_prices": "가격 비교",
        "delayed_gratification": "참기",
    }.items():
        s = s.replace(k, v)
    return " ".join(s.split()).strip()

def _inject_dashboard_css():
    st.markdown(
        """
        <style>
            /* 전역 디자인 토큰은 utils/menu.py에서 주입됩니다. */

            /* page background + container width */
            .stApp { background: var(--amf-bg) !important; }
            .block-container { max-width: 1200px !important; padding-top: 0.9rem !important; }

            /* remove default chrome for app-like feel */
            [data-testid="stToolbar"], #MainMenu, footer { display:none !important; }
            /* 헤더는 남겨서 사이드바 토글(>>)이 보이도록 */
            header { background: transparent !important; }

            /* typography */
            h1, h2, h3 { letter-spacing: -0.3px; color: var(--amf-text); }
            .amf-kicker { color: var(--amf-muted); font-weight: 700; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; }
            .amf-title { font-size: 28px; font-weight: 900; margin: 0; color: var(--amf-text); }
            .amf-sub { margin-top: 6px; color: var(--amf-muted); font-weight: 600; font-size: 13px; }

            /* app bar - 카드형으로 변경 */
            .amf-appbar {
                background: var(--amf-card);
                border: 1px solid var(--amf-border);
                border-radius: var(--amf-radius-lg);
                padding: 16px 18px;
                margin-bottom: 16px;
                box-shadow: var(--amf-shadow);
            }
            .amf-appbar-content {
                display: flex;
                flex-direction: column;
                gap: 4px;
            }
            .amf-chip {
                display:inline-flex;
                align-items:center;
                gap:8px;
                padding: 6px 12px;
                border-radius: var(--amf-radius);
                background: var(--amf-card);
                border: 1px solid var(--amf-border);
                box-shadow: var(--amf-shadow);
                font-weight: 700;
                font-size: 12px;
                color: var(--amf-muted);
                white-space: nowrap;
            }
            .amf-chip strong { color: var(--amf-text); }

            /* 상단 액션(팝오버 버튼) - 작고 자연스럽게 */
            button[aria-haspopup="dialog"]{
                width: auto !important;
                min-width: 40px !important;
                border-radius: var(--amf-radius) !important;
                padding: 6px 12px !important;
                font-weight: 700 !important;
                font-size: 13px !important;
                background: var(--amf-card) !important;
                border: 1px solid var(--amf-border) !important;
                box-shadow: var(--amf-shadow) !important;
                transition: all 0.2s ease !important;
            }
            button[aria-haspopup="dialog"]:hover{
                transform: translateY(-1px);
                box-shadow: var(--amf-shadow-hover) !important;
            }

            /* metric cards - 카드형 UI */
            [data-testid="stMetric"]{
                background: var(--amf-card) !important;
                border: 1px solid var(--amf-border) !important;
                border-radius: var(--amf-radius-lg) !important;
                padding: 14px 14px !important;
                box-shadow: var(--amf-shadow) !important;
            }
            [data-testid="stMetricLabel"] { color: var(--amf-muted) !important; font-weight: 700 !important; font-size: 12px !important; }
            [data-testid="stMetricValue"] { color: var(--amf-text) !important; font-weight: 900 !important; letter-spacing: -0.4px; }

            /* containers with border=True - 카드형 UI */
            div[data-testid="stVerticalBlockBorderWrapper"]{
                border-radius: var(--amf-radius-lg) !important;
                border: 1px solid var(--amf-border) !important;
                background: var(--amf-card) !important;
                box-shadow: var(--amf-shadow) !important;
            }

            /* buttons - 작고 자연스럽게, 웹 폼 느낌 제거 */
            .stButton > button{
                border-radius: var(--amf-radius) !important;
                font-weight: 600 !important;
                font-size: 13px !important;
                padding: 7px 14px !important;
                transition: all 0.2s ease !important;
                border: 1px solid var(--amf-border) !important;
                background: var(--amf-card) !important;
                color: var(--amf-text) !important;
                box-shadow: var(--amf-shadow) !important;
            }
            .stButton > button:hover {
                transform: translateY(-1px) !important;
                box-shadow: var(--amf-shadow-hover) !important;
                border-color: var(--amf-accent) !important;
            }
            /* Primary 버튼 - 포인트 컬러만 사용 */
            .stButton > button[kind="primary"], 
            button[kind="primary"], 
            button[data-testid="baseButton-primary"]{
                background: var(--amf-accent) !important;
                border: none !important;
                color: var(--amf-text) !important;
                box-shadow: var(--amf-shadow) !important;
            }
            .stButton > button[kind="primary"]:hover, 
            button[kind="primary"]:hover, 
            button[data-testid="baseButton-primary"]:hover{
                background: var(--amf-accent-hover) !important;
                transform: translateY(-1px) !important;
                box-shadow: var(--amf-shadow-hover) !important;
            }
            /* Secondary 버튼 - 더 자연스럽게 */
            .stButton > button[kind="secondary"],
            button[kind="secondary"] {
                background: var(--amf-bg) !important;
                border: 1px solid var(--amf-border) !important;
                color: var(--amf-text) !important;
            }
            .stButton > button[kind="secondary"]:hover,
            button[kind="secondary"]:hover {
                background: var(--amf-card) !important;
                border-color: var(--amf-accent) !important;
            }

            /* info/warning/success */
            [data-testid="stAlert"]{
                border-radius: var(--amf-radius-lg) !important;
                border: 1px solid var(--amf-border) !important;
                box-shadow: var(--amf-shadow) !important;
            }

            /* progress bar */
            [data-testid="stProgress"] > div > div{
                background: var(--amf-accent) !important;
            }

            /* 빈 상태 카드 */
            .amf-empty {
                background: var(--amf-card);
                border: 1px solid var(--amf-border);
                border-radius: var(--amf-radius-lg);
                padding: 16px;
                box-shadow: var(--amf-shadow);
            }
            .amf-empty h3{
                margin: 0 0 6px 0;
                font-size: 16px;
                font-weight: 900;
                color: var(--amf-text);
            }
            .amf-empty p{
                margin: 0;
                color: var(--amf-muted);
                font-weight: 600;
                font-size: 13px;
                line-height: 1.45;
            }

            /* 아이 홈 hero - 카드형 */
            .amf-hero{
                background: var(--amf-card);
                border: 1px solid var(--amf-border);
                padding: 18px 16px;
                border-radius: var(--amf-radius-xl);
                color: var(--amf-text);
                box-shadow: var(--amf-shadow);
            }
            .amf-hero-label{ 
                font-weight: 700; 
                color: var(--amf-muted);
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            .amf-hero-value{
                font-size: 42px;
                font-weight: 900;
                letter-spacing: -0.8px;
                margin-top: 4px;
                line-height: 1.05;
                color: var(--amf-text);
            }
            .amf-hero-sub{
                margin-top: 8px;
                color: var(--amf-muted);
                font-weight: 600;
                font-size: 13px;
            }

            /* tab list pill (used elsewhere) */
            .stTabs [data-baseweb="tab-list"]{
                background: var(--amf-bg);
                border-radius: var(--amf-radius);
                padding: 4px;
                gap: 4px;
            }
            .stTabs [data-baseweb="tab"]{
                border-radius: var(--amf-radius);
                font-weight: 700;
                font-size: 13px;
            }
            .stTabs [aria-selected="true"]{
                background: var(--amf-card);
                box-shadow: var(--amf-shadow);
            }

            /* 여백 최소화 - 전면 개편 */
            .block-container { padding-top: 0.5rem !important; padding-bottom: 0.5rem !important; }
            div[data-testid="stVerticalBlock"] > div { gap: 0.5rem !important; }
            div[data-testid="stVerticalBlockBorderWrapper"] { margin-bottom: 0.75rem !important; }
            
            /* 섹션 간격 최소화 */
            h1, h2, h3 { margin-top: 0.5rem !important; margin-bottom: 0.5rem !important; }
            .stSubheader { margin-top: 0.75rem !important; margin-bottom: 0.5rem !important; }
            
            /* 버튼 크기 작게 */
            .stButton > button {
                padding: 6px 12px !important;
                font-size: 12px !important;
                min-height: 32px !important;
            }
            
            /* 메트릭 카드 여백 최소화 */
            [data-testid="stMetric"] { padding: 10px 12px !important; }
            [data-testid="stMetricValue"] { font-size: 20px !important; }
            [data-testid="stMetricLabel"] { font-size: 11px !important; }
            
            /* ✅ Mobile-first tweaks */
            @media (max-width: 768px){
                .block-container { padding-top: 0.4rem !important; padding-left: 0.8rem !important; padding-right: 0.8rem !important; }
                .amf-title { font-size: 20px; }
                .amf-sub { font-size: 11px; }
                .amf-chip { font-size: 10px; padding: 5px 9px; }
                button[aria-haspopup="dialog"]{ padding: 5px 9px !important; }
                [data-testid="stMetric"]{ padding: 8px 10px !important; }
                [data-testid="stMetricValue"]{ font-size: 18px !important; }
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
              background: linear-gradient(135deg, rgba(255,235,0,0.95), rgba(255,235,0,0.55));
              padding: 16px 16px;
              border-radius: 18px;
              color: #191919;
              box-shadow: 0 18px 40px rgba(17,24,39,0.10);
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

    # app bar (title) - 카드형으로 변경
    if user_type == "child":
        st.markdown(
            f"""
            <div class="amf-appbar">
              <div class="amf-appbar-content">
                <div class="amf-kicker">AI Money Friends</div>
                <div class="amf-title">안녕하세요, {user_name}님 👋</div>
                <div class="amf-sub">오늘도 한 걸음씩 돈 관리 실력을 키워봐요</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        # 부모님용은 기존 스타일 유지
        st.markdown(
            f"""
            <div class="amf-appbar">
              <div class="amf-appbar-content">
                <div class="amf-kicker">AI Money Friends</div>
                <div class="amf-title">안녕하세요, {user_name}님 👋</div>
                <div class="amf-sub">가족의 금융 활동을 한눈에 확인하세요</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

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

        # 감정 기록 - 리디자인(칩 + 하단 미니 CTA, 카카오뱅크 톤)
        st.markdown('<div id="amf_emotion_dash_anchor"></div>', unsafe_allow_html=True)
        st.markdown(
            """
            <style>
            /* scope: dashboard emotion */
            div[data-testid="stVerticalBlock"]:has(#amf_emotion_dash_anchor) .amf-emo-wrap{
                background: var(--amf-card);
                border: 1px solid var(--amf-border);
                border-radius: var(--amf-radius-lg);
                padding: 18px 18px 14px 18px;
                box-shadow: var(--amf-shadow);
            }
            div[data-testid="stVerticalBlock"]:has(#amf_emotion_dash_anchor) .amf-emo-title{
                font-size: 15px;
                font-weight: 900;
                color: var(--amf-text);
                letter-spacing: -0.2px;
                margin-bottom: 4px;
            }
            div[data-testid="stVerticalBlock"]:has(#amf_emotion_dash_anchor) .amf-emo-sub{
                font-size: 12px;
                font-weight: 600;
                color: var(--amf-muted);
                line-height: 1.45;
                margin-bottom: 12px;
            }

            /* segmented (type) */
            div[data-testid="stVerticalBlock"]:has(#amf_emotion_dash_anchor) div[data-testid="stSegmentedControl"]{
                margin: 0 !important;
            }
            div[data-testid="stVerticalBlock"]:has(#amf_emotion_dash_anchor) div[data-testid="stSegmentedControl"] button{
                height: 36px !important;
                border-radius: 999px !important;
                font-weight: 800 !important;
                font-size: 13px !important;
            }

            /* chips row */
            div[data-testid="stVerticalBlock"]:has(#amf_emotion_dash_anchor) .amf-chiprow{
                display:flex;
                flex-wrap:wrap;
                gap: 8px;
                margin-top: 10px;
                margin-bottom: 10px;
            }
            div[data-testid="stVerticalBlock"]:has(#amf_emotion_dash_anchor) .amf-chiprow .stButton > button{
                border-radius: 999px !important;
                padding: 7px 12px !important;
                font-size: 13px !important;
                font-weight: 800 !important;
                min-height: 34px !important;
            }

            /* memo */
            div[data-testid="stVerticalBlock"]:has(#amf_emotion_dash_anchor) textarea{
                min-height: 84px !important;
                border-radius: 14px !important;
                border: 1px solid var(--amf-border) !important;
                box-shadow: none !important;
                font-size: 13px !important;
            }

            /* sticky mini cta */
            div[data-testid="stVerticalBlock"]:has(#amf_emotion_dash_anchor) .amf-sticky{
                position: sticky;
                bottom: 10px;
                margin-top: 10px;
                padding-top: 10px;
                background: linear-gradient(to top, rgba(246,247,249,0.95), rgba(246,247,249,0.0));
            }
            div[data-testid="stVerticalBlock"]:has(#amf_emotion_dash_anchor) .amf-sticky .stButton > button[kind="primary"]{
                height: 44px !important;
                border-radius: 14px !important;
                font-weight: 900 !important;
                font-size: 14px !important;
                box-shadow: none !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        # 상태
        if "emotion_type_dash" not in st.session_state:
            st.session_state["emotion_type_dash"] = "지출 전"
        if "emotion_selected_dash" not in st.session_state:
            st.session_state["emotion_selected_dash"] = None

        type_options = ["지출 전", "지출 후", "오늘 기분"]
        type_to_context = {"지출 전": "pre_spend", "지출 후": "post_spend", "오늘 기분": "daily"}
        type_to_msg = {
            "지출 전": "지금 기분을 먼저 체크해볼까?",
            "지출 후": "사고 나서 기분이 어때?",
            "오늘 기분": "오늘 하루는 어땠어?",
        }
        emotion_items = [
            ("excited", "신남", "assets/emotions/excited.png"),
            ("happy", "좋아", "assets/emotions/happy.png"),
            ("neutral", "보통", "assets/emotions/neutral.png"),
            ("worried", "걱정", "assets/emotions/worried.png"),
            ("angry", "화남", "assets/emotions/angry.png"),
        ]
        emotion_key_to_label = {k: v for (k, v, _p) in emotion_items}

        with st.container(border=True):
            picked_type = (
                st.segmented_control(
                    "타입",
                    options=type_options,
                    default=st.session_state["emotion_type_dash"],
                    label_visibility="collapsed",
                    key="emotion_type_dash_seg",
                )
                if hasattr(st, "segmented_control")
                else st.radio(
                    "타입",
                    options=type_options,
                    horizontal=True,
                    label_visibility="collapsed",
                    key="emotion_type_dash_radio",
                )
            )
            st.session_state["emotion_type_dash"] = picked_type or st.session_state["emotion_type_dash"]

            st.markdown(
                f"""
                <div class="amf-emo-wrap">
                  <div class="amf-emo-title">{type_to_msg.get(st.session_state["emotion_type_dash"], "지금 기분은 어때?")}</div>
                  <div class="amf-emo-sub">짧게 남기면, AI 돈 친구가 더 잘 도와줘요.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
            st.markdown("<div style='font-weight:900; font-size:14px;'>어떤 기분이었나요?</div>", unsafe_allow_html=True)
            st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

            # 칩 버튼(네이티브)
            st.markdown('<div class="amf-chiprow">', unsafe_allow_html=True)
            cols = st.columns(5)
            for i, (emo_key, emo_label, emo_img) in enumerate(emotion_items):
                with cols[i]:
                    img_path = _resolve_asset_path(emo_img)
                    if Path(img_path).is_file():
                        st.image(img_path, width=44)
                    else:
                        # 이미지가 없거나 경로가 깨졌을 때도 UI가 비지 않게 최소 표시
                        st.markdown("<div style='height:44px'></div>", unsafe_allow_html=True)
                    if st.button(
                        emo_label,
                        key=f"emo_chip_dash_{i}",
                        use_container_width=True,
                        type="primary" if st.session_state["emotion_selected_dash"] == emo_key else "secondary",
                    ):
                        st.session_state["emotion_selected_dash"] = emo_key
                        st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

            memo = st.text_area(
                "메모",
                value=st.session_state.get("emotion_memo_dash", ""),
                placeholder="오늘의 감정을 자유롭게 기록해보세요",
                label_visibility="collapsed",
                key="emotion_memo_dash",
            )

            # 하단 미니 CTA
            st.markdown('<div class="amf-sticky">', unsafe_allow_html=True)
            if st.button("기록하기", key="emo_save_dash", use_container_width=True, type="primary"):
                emo = st.session_state.get("emotion_selected_dash")
                if not emo:
                    st.warning("감정을 먼저 선택해줘!")
                else:
                    try:
                        db.create_emotion_log(
                            user_id,
                            context=type_to_context.get(st.session_state["emotion_type_dash"], "daily"),
                            emotion=str(emo),
                            note=(memo or "").strip() or None,
                        )
                        if hasattr(st, "toast"):
                            st.toast("✅ 기록했어!", icon="😊")
                        else:
                            st.success("✅ 기록했어!")
                        st.session_state["emotion_selected_dash"] = None
                        st.session_state["emotion_memo_dash"] = ""
                        st.rerun()
                    except Exception:
                        st.error("기록에 실패했어. 잠시 후 다시 해볼래?")
            st.markdown("</div>", unsafe_allow_html=True)

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
                    emo_key = e.get("emotion") or ""
                    emo = emotion_key_to_label.get(str(emo_key), str(emo_key))
                    note = (e.get("note") or "").strip()
                    line = f"{emo} **{ctx_kr}** · {ts}"
                    st.markdown(line)
                    if note:
                        st.caption(note)

        # hero card - 전면 개편: 카드형, 여백 최소화
        with st.container(border=True):
            st.markdown(
                f"""
                <div style="padding: 4px 0;">
                    <div style="font-size: 11px; font-weight: 700; color: var(--amf-muted); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px;">내 잔액</div>
                    <div style="font-size: 36px; font-weight: 900; color: var(--amf-text); letter-spacing: -0.8px; line-height: 1.05; margin-bottom: 8px;">{int(cstats["balance"]):,}원</div>
                    <div style="font-size: 12px; color: var(--amf-muted); font-weight: 600;">저축 {int(cstats["total_saving"]):,}원 · 지출 {int(cstats["total_spend"]):,}원</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # 이번 달 요약 - 카드형, 여백 최소화
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
        
        with st.container(border=True):
            st.markdown('<div style="font-size: 13px; font-weight: 700; color: var(--amf-text); margin-bottom: 12px;">이번 달 요약</div>', unsafe_allow_html=True)
            y1, y2, y3 = st.columns(3)
            with y1:
                st.metric("받은 용돈", f"{int(m_allow):,}원", delta=None)
            with y2:
                st.metric("저축", f"{int(m_save):,}원", delta=None)
            with y3:
                st.metric("지출", f"{int(m_spend):,}원", delta=None)

        # 진행 중인 미션(오늘)
        today = date.today().isoformat()
        db.assign_daily_missions_if_needed(user_id, today)
        missions = db.get_missions_for_user(user_id, date_str=today, active_only=True)

        # 오늘의 미션 - 카드형, 여백 최소화
        with st.container(border=True):
            st.markdown('<div style="font-size: 13px; font-weight: 700; color: var(--amf-text); margin-bottom: 12px;">✅ 오늘의 미션</div>', unsafe_allow_html=True)
            if not missions:
                st.caption("오늘의 미션이 없어요.")
            else:
                for m in missions:
                    with st.container(border=True):
                        st.markdown(f"**{m.get('title')}**")
                        if m.get("description"):
                            st.caption(_ko_mission_desc(m.get("description")))
                        st.caption(f"난이도: {m.get('difficulty')} · 보상: {int(m.get('reward_amount') or 0):,}원")
                        if st.button("완료!", key=f"complete_m_{m['id']}", use_container_width=True, type="primary"):
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
                                db.create_notification(
                                    user_id,
                                    "미션 완료!",
                                    f"보상 {int(reward):,}원을 받았어요.",
                                    level="success",
                                )
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
                                    reward_info = (
                                        db.grant_level_rewards_if_needed(user_id)
                                        if hasattr(db, "grant_level_rewards_if_needed")
                                        else {}
                                    )
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

