import streamlit as st

from datetime import datetime
from urllib.parse import quote as _urlquote
import streamlit.components.v1 as components

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

    user_id = int(st.session_state.get("user_id"))
    user_name = st.session_state.get("user_name", "사용자")
    user_type = st.session_state.get("user_type", "child")

    render_sidebar_menu(user_id, user_name, user_type)

    if user_type != "parent":
        st.error("부모님만 접근할 수 있어요.")
        st.stop()

    parent = db.get_user_by_id(user_id)
    parent_code = (parent or {}).get("parent_code", "")
    children = db.get_users_by_parent_code(parent_code) if parent_code else []

    st.title("👶 자녀 관리")
    st.caption("자녀 계정 연결/현황/기록을 한 곳에서 관리해요.")

    # ✅ 모바일 우선: 3열 대신 2열(2줄)
    c1, c2 = st.columns(2)
    with c1:
        st.metric("연결된 자녀", f"{len(children)}명")
    with c2:
        st.metric("오늘", datetime.now().strftime("%Y.%m.%d"))
    st.metric("부모 코드", parent_code or "없음")

    st.divider()

    # ✅ 실사용 UX: 자녀가 있어도 항상 "자녀 초대(코드/QR)" 제공 (기본은 접힘)
    if parent_code:
        full_code = (parent_code or "").strip().upper()
        short_code = full_code[-6:] if len(full_code) >= 6 else full_code

        with st.expander("👶 자녀 초대하기 (코드/QR)", expanded=(len(children) == 0)):
            left, right = st.columns([1.25, 0.75])
            with left:
                st.markdown(
                    f"""
                    <div style="
                        background: linear-gradient(135deg, #667eea, #764ba2);
                        padding: 18px 16px;
                        border-radius: 16px;
                        color: white;
                        box-shadow: 0 16px 32px rgba(102,126,234,0.20);
                    ">
                        <div style="font-weight:900; opacity:0.9;">자녀에게 아래 코드를 알려주세요</div>
                        <div style="
                            margin-top:10px;
                            background: rgba(255,255,255,0.95);
                            color:#111827;
                            padding: 12px 14px;
                            border-radius: 12px;
                            font-size: 32px;
                            font-weight: 950;
                            letter-spacing: 4px;
                            text-align:center;
                        ">{full_code}</div>
                        <div style="margin-top:10px; font-size:13px; font-weight:800; opacity:0.92;">
                            축약 6자리 코드: <span style="background:rgba(255,255,255,0.18); padding:4px 8px; border-radius:999px;">{short_code}</span>
                        </div>
                        <div style="margin-top:8px; font-size:12px; font-weight:800; opacity:0.85;">
                            ※ 자녀 회원가입 화면에서 8자리(전체) 또는 6자리(축약)로 입력할 수 있어요.
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # ✅ 복사 버튼(실사용 UX): Streamlit 버튼 + 토스트 + (클릭 시에만) JS 복사
                copy_col1, copy_col2 = st.columns(2)
                with copy_col1:
                    copy_full_clicked = st.button(
                        "📋 전체 코드 복사",
                        use_container_width=True,
                        key="copy_invite_full_btn",
                    )
                with copy_col2:
                    copy_short_clicked = st.button(
                        "📋 6자리 복사",
                        use_container_width=True,
                        key="copy_invite_short_btn",
                    )

                to_copy = None
                if copy_full_clicked:
                    to_copy = full_code
                if copy_short_clicked:
                    to_copy = short_code

                if to_copy:
                    # st.toast가 없는 환경도 고려
                    if hasattr(st, "toast"):
                        st.toast("✅ 복사했어요!", icon="📋")
                    else:
                        st.success("✅ 복사했어요!")
                    components.html(
                        f"""
                        <script>
                          (function(){{
                            const text = {to_copy!r};
                            if (navigator.clipboard) {{
                              navigator.clipboard.writeText(text);
                            }}
                          }})();
                        </script>
                        """,
                        height=0,
                    )

                st.caption("복사가 안 되면 `전체 8자리 코드 보기`에서 복사 아이콘을 눌러주세요.")
                with st.expander("전체 8자리 코드 보기", expanded=False):
                    st.code(full_code, language=None)

            with right:
                st.caption("QR 코드(초대용)")
                try:
                    # qrcode가 있으면 로컬 생성, 없으면 외부 QR 이미지로 fallback
                    try:
                        import qrcode  # type: ignore

                        qr = qrcode.QRCode(
                            version=None,
                            error_correction=getattr(qrcode.constants, "ERROR_CORRECT_M", None),
                            box_size=8,
                            border=2,
                        )
                        qr.add_data(full_code)
                        qr.make(fit=True)
                        img = qr.make_image(fill_color="black", back_color="white")
                        try:
                            img = img.convert("RGB")
                        except Exception:
                            pass
                        st.image(img, use_container_width=True)
                    except Exception:
                        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=220x220&data={_urlquote(full_code)}"
                        st.image(qr_url, use_container_width=True)

                    st.caption("QR을 스캔한 뒤, 자녀 회원가입 화면에서 코드를 입력하면 연결돼요.")
                    with st.expander("QR이 안 나올 때(점검)", expanded=False):
                        st.caption("권장: `requirements.txt`에 아래 항목이 포함되어 있어야 해요.")
                        st.code("qrcode[pil]>=7.4.2", language=None)
                except Exception:
                    st.caption("QR 표시 중 문제가 발생했어요. 잠시 후 다시 시도해주세요.")

    if not children:
        st.info("아직 연결된 자녀가 없어요. 자녀가 회원가입 시 ‘부모 초대 코드’를 입력하면 자동으로 연결돼요.")
        if not parent_code:
            st.warning("부모 코드가 없어요. (부모 계정 생성 시 자동 생성됩니다)")
            return
        return

    # ===== 자녀 카드 목록(모바일/PC 공통) =====
    st.subheader(f"👶 연결된 자녀 ({len(children)}명)")
    st.caption("카드를 눌러 자녀를 선택하거나, 바로 용돈 관리로 이동할 수 있어요.")

    # 완료 미션 수(있으면) 한 번에 조회
    completed_map = {}
    try:
        conn = db._get_connection()  # pylint: disable=protected-access
        cur = conn.cursor()
        ids = [int(c["id"]) for c in children]
        if ids:
            placeholders = ",".join(["?"] * len(ids))
            cur.execute(
                f"""
                SELECT user_id, COUNT(*) as cnt
                FROM mission_assignments
                WHERE status = 'completed' AND user_id IN ({placeholders})
                GROUP BY user_id
                """,
                tuple(ids),
            )
            for r in cur.fetchall():
                completed_map[int(r["user_id"])] = int(r["cnt"] or 0)
    except Exception:
        completed_map = {}
    finally:
        try:
            conn.close()
        except Exception:
            pass

    cols = st.columns(2)
    for idx, c in enumerate(children):
        cid = int(c["id"])
        with cols[idx % 2]:
            # 잔액(추정)
            beh = db.get_user_behaviors(cid, limit=2000)
            total_allowance = sum((b.get("amount") or 0) for b in beh if b.get("behavior_type") == "allowance")
            total_saving = sum((b.get("amount") or 0) for b in beh if b.get("behavior_type") == "saving")
            total_spend = sum(
                (b.get("amount") or 0)
                for b in beh
                if b.get("behavior_type") in ("planned_spending", "impulse_buying")
            )
            balance = total_allowance - total_saving - total_spend

            created_at = str(c.get("created_at") or "")[:10]
            done = int(completed_map.get(cid, 0))

            with st.container(border=True):
                st.markdown(f"### 👶 {c.get('name')}")
                st.caption(f"{c.get('username')} · 가입일 {created_at or '-'}")
                st.metric("현재 잔액(추정)", f"{int(balance):,}원")
                st.caption(f"✅ 완료 미션: **{done}개**")

                b1, b2 = st.columns(2)
                with b1:
                    if st.button("관리", key=f"pick_{cid}", use_container_width=True):
                        st.session_state["selected_child_id"] = cid
                        st.rerun()
                with b2:
                    if st.button("💵 용돈 주기", key=f"give_{cid}", use_container_width=True):
                        st.session_state["allowance_target_child_id"] = cid
                        st.switch_page("pages/3_💵_용돈_관리.py")

    st.divider()

    child_label_to_id = {f"{c['name']} ({c['username']})": c["id"] for c in children}
    labels = list(child_label_to_id.keys())
    selected_child_id = st.session_state.get("selected_child_id")
    default_idx = 0
    if selected_child_id:
        for i, lbl in enumerate(labels):
            if int(child_label_to_id[lbl]) == int(selected_child_id):
                default_idx = i
                break
    selected_label = st.selectbox("자녀 선택", labels, index=default_idx, key="child_manage_select")
    child_id = int(child_label_to_id[selected_label])
    child = db.get_user_by_id(child_id)

    behaviors = db.get_user_behaviors(child_id, limit=2000)
    total_allowance = sum((b.get("amount") or 0) for b in behaviors if b.get("behavior_type") == "allowance")
    total_saving = sum((b.get("amount") or 0) for b in behaviors if b.get("behavior_type") == "saving")
    total_spend = sum(
        (b.get("amount") or 0)
        for b in behaviors
        if b.get("behavior_type") in ("planned_spending", "impulse_buying")
    )
    balance = total_allowance - total_saving - total_spend
    stats = db.get_child_stats(child_id)

    # ✅ 모바일 우선: 4열 → 2열(2줄)
    m1, m2 = st.columns(2)
    with m1:
        st.metric("잔액(추정)", f"{int(balance):,}원")
    with m2:
        st.metric("총 용돈(지급)", f"{int(total_allowance):,}원")
    m3, m4 = st.columns(2)
    with m3:
        st.metric("총 저축", f"{int(stats.get('total_savings') or 0):,}원")
    with m4:
        st.metric("활동 수", f"{int(stats.get('activity_count') or 0)}개")

    st.divider()

    st.subheader("관리")
    a1, a2 = st.columns(2)
    with a1:
        with st.form("rename_child"):
            new_name = st.text_input("자녀 이름 변경", value=child.get("name", ""))
            submit_rename = st.form_submit_button("이름 변경", use_container_width=True)
        if submit_rename:
            if not new_name.strip():
                st.error("이름을 입력하세요.")
            else:
                ok = db.update_user_name(child_id, new_name.strip())
                st.success("이름을 변경했어요." if ok else "변경에 실패했어요.")
                st.rerun()

    with a2:
        with st.form("reset_child_password"):
            st.caption("비밀번호 재설정(부모용)")
            new_pw = st.text_input("새 비밀번호", type="password", placeholder="4자 이상")
            submit_pw = st.form_submit_button("비밀번호 재설정", use_container_width=True)
        if submit_pw:
            if not new_pw or len(new_pw) < 4:
                st.error("비밀번호는 최소 4자 이상이어야 해요.")
            else:
                ok = db.update_user_password(child_id, new_pw)
                st.success("비밀번호를 재설정했어요." if ok else "재설정에 실패했어요.")

    st.divider()
    st.subheader("최근 기록")
    if not behaviors:
        st.caption("아직 기록이 없어요.")
    else:
        recent = behaviors[:20]
        st.dataframe(
            [
                {
                    "일시": r.get("timestamp"),
                    "유형": r.get("behavior_type"),
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
    b1, b2 = st.columns(2)
    with b1:
        if st.button("💵 용돈 관리로 이동", use_container_width=True):
            st.switch_page("pages/3_💵_용돈_관리.py")
    with b2:
        if st.button("🏠 홈", use_container_width=True):
            st.switch_page("pages/1_🏠_대시보드.py")


if __name__ == "__main__":
    main()

