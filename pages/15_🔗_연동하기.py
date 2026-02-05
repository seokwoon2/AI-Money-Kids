import streamlit as st

from datetime import datetime, timedelta
from urllib.parse import quote as _urlquote
import streamlit.components.v1 as components

from database.db_manager import DatabaseManager
from utils.menu import render_sidebar_menu, hide_sidebar_navigation


def _guard_login() -> bool:
    if not st.session_state.get("logged_in"):
        st.switch_page("app.py")
        return False
    return True


def _qr_image_for_text(text: str) -> str:
    # 외부 QR 이미지 API(가벼운 fallback)
    return f"https://api.qrserver.com/v1/create-qr-code/?size=260x260&data={_urlquote(text)}"


def _copy_to_clipboard(text: str):
    if hasattr(st, "toast"):
        st.toast("✅ 복사했어요!", icon="📋")
    else:
        st.success("✅ 복사했어요!")
    components.html(
        f"""
        <script>
          (function(){{
            const text = {text!r};
            if (navigator.clipboard) {{
              navigator.clipboard.writeText(text);
            }}
          }})();
        </script>
        """,
        height=0,
    )


def main():
    if not _guard_login():
        return

    hide_sidebar_navigation()
    db = DatabaseManager()

    user_id = int(st.session_state.get("user_id"))
    user_name = st.session_state.get("user_name", "사용자")
    user_type = st.session_state.get("user_type", "child")

    render_sidebar_menu(user_id, user_name, user_type)

    st.markdown('<div id="amf_link_page_anchor"></div>', unsafe_allow_html=True)
    st.markdown(
        """
        <style>
        /* scope: only this page */
        div[data-testid="stVerticalBlock"]:has(#amf_link_page_anchor) h1 {
          letter-spacing: -0.02em;
        }
        div[data-testid="stVerticalBlock"]:has(#amf_link_page_anchor) .amf-link-hero {
          padding: 14px 14px;
          border-radius: 18px;
          background: linear-gradient(135deg, rgba(255,235,0,0.20), rgba(255,255,255,0.70));
          border: 1px solid rgba(17,24,39,0.08);
          box-shadow: var(--amf-shadow);
        }
        div[data-testid="stVerticalBlock"]:has(#amf_link_page_anchor) .amf-link-hero-title{
          font-size: 18px;
          font-weight: 800;
          color: #0f172a;
          margin-bottom: 4px;
        }
        div[data-testid="stVerticalBlock"]:has(#amf_link_page_anchor) .amf-link-hero-sub{
          color: rgba(15,23,42,0.72);
          font-size: 13px;
        }
        div[data-testid="stVerticalBlock"]:has(#amf_link_page_anchor) .amf-step {
          display:flex; gap:8px; flex-wrap:wrap; margin-top:10px;
        }
        div[data-testid="stVerticalBlock"]:has(#amf_link_page_anchor) .amf-step .chip{
          padding: 6px 10px;
          border-radius: 999px;
          font-size: 12px;
          border: 1px solid rgba(15,23,42,0.12);
          background: rgba(255,255,255,0.70);
          color: rgba(15,23,42,0.75);
          font-weight: 700;
        }
        div[data-testid="stVerticalBlock"]:has(#amf_link_page_anchor) .amf-step .chip.on{
          border-color: rgba(255,235,0,0.55);
          background: rgba(255,235,0,0.22);
          color: #191919;
        }
        div[data-testid="stVerticalBlock"]:has(#amf_link_page_anchor) .amf-digit-boxes{
          display:flex; gap:10px; justify-content:center; align-items:center;
          padding: 10px 0 6px 0;
        }
        div[data-testid="stVerticalBlock"]:has(#amf_link_page_anchor) .amf-digit{
          width: 44px; height: 52px;
          border-radius: 14px;
          border: 1px solid rgba(15,23,42,0.14);
          background: rgba(255,255,255,0.85);
          display:flex; align-items:center; justify-content:center;
          font-size: 22px; font-weight: 900;
          color: #0f172a;
          box-shadow: 0 10px 22px rgba(0,0,0,0.06);
        }
        div[data-testid="stVerticalBlock"]:has(#amf_link_page_anchor) .amf-prefix{
          text-align:center;
          font-weight: 900;
          color: rgba(15,23,42,0.55);
          margin-top: 2px;
        }
        /* keypad scope */
        div[data-testid="stVerticalBlock"]:has(#amf_link_keypad_anchor) button {
          height: 56px !important;
          border-radius: 16px !important;
          font-weight: 900 !important;
          font-size: 18px !important;
        }
        /* completion card */
        div[data-testid="stVerticalBlock"]:has(#amf_link_done_anchor) .amf-done-card{
          padding: 18px 16px;
          border-radius: 20px;
          background: linear-gradient(135deg, rgba(255,235,0,0.22), rgba(255,255,255,0.70));
          border: 1px solid rgba(17,24,39,0.08);
          box-shadow: var(--amf-shadow);
          text-align:center;
        }
        div[data-testid="stVerticalBlock"]:has(#amf_link_done_anchor) .amf-done-title{
          font-size: 20px; font-weight: 900; color: #0f172a;
          margin-bottom: 6px;
        }
        div[data-testid="stVerticalBlock"]:has(#amf_link_done_anchor) .amf-done-sub{
          color: rgba(15,23,42,0.74);
          font-size: 13px;
          margin-bottom: 12px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("🔗 연동하기")
    st.markdown(
        """
        <div class="amf-link-hero">
          <div class="amf-link-hero-title">부모-자녀 연결을 시작해요</div>
          <div class="amf-link-hero-sub">부모는 초대코드(MF-XXXX)를 만들고, 아이는 입력 또는 QR로 연결해요. (24시간 유효)</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    me = db.get_user_by_id(user_id) or {}

    if user_type == "parent":
        st.subheader("부모: 초대코드 만들기")
        st.caption("자녀에게 코드 또는 QR을 공유하세요. 새 코드를 만들기 전, 아직 유효한 코드가 있으면 그대로 보여줘요.")

        if "link_latest_invite" not in st.session_state:
            st.session_state["link_latest_invite"] = None

        if not st.session_state.get("link_latest_invite") and hasattr(db, "get_active_invite_code"):
            try:
                st.session_state["link_latest_invite"] = db.get_active_invite_code(user_id)
            except Exception:
                pass

        if st.button("🔗 초대코드 만들기(MF-XXXX)", use_container_width=True, type="primary"):
            inv = None
            try:
                inv = db.create_invite_code(user_id, ttl_hours=24) if hasattr(db, "create_invite_code") else None
            except Exception:
                inv = None
            if inv:
                st.session_state["link_latest_invite"] = inv
                st.rerun()
            st.error("초대코드를 만들 수 없어요. 잠시 후 다시 시도해주세요.")

        inv = st.session_state.get("link_latest_invite")
        if inv:
            code = (inv or {}).get("code") or ""
            exp = (inv or {}).get("expires_at") or ""
            with st.container(border=True):
                st.markdown(f"### {code}")
                st.caption(f"24시간 유효 · 만료: {exp}")
                c1, c2 = st.columns(2)
                if c1.button("📋 코드 복사", use_container_width=True):
                    _copy_to_clipboard(code)
                share_text = f"AI 머니프렌즈 초대코드: {code} (24시간 유효)"
                if c2.button("💬 공유문구 복사", use_container_width=True):
                    _copy_to_clipboard(share_text)
                st.image(_qr_image_for_text(code), use_container_width=True)

        st.info("카카오톡 ‘공유 버튼’은 카카오 JS 키/도메인 설정이 필요해요. 지금은 ‘공유문구 복사’로 대체합니다.")

    else:
        # 완료 상태면 축하 화면
        if st.session_state.get("link_done"):
            parent_name = st.session_state.get("link_done_parent_name", "부모님")
            st.markdown('<div id="amf_link_done_anchor"></div>', unsafe_allow_html=True)
            st.markdown(
                f"""
                <div class="amf-done-card">
                  <div class="amf-done-title">연동 완료! 🎉</div>
                  <div class="amf-done-sub"><b>{parent_name}</b>과 연결되었어요. 이제 미션을 해보자!</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.balloons()
            a1, a2 = st.columns(2)
            if a1.button("🏠 홈", use_container_width=True, type="primary"):
                st.switch_page("pages/1_🏠_대시보드.py")
            if a2.button("✅ 미션", use_container_width=True):
                st.switch_page("pages/10_✅_미션.py")
            st.markdown("---")
            if st.button("🔁 다른 코드로 다시 연동", use_container_width=True):
                st.session_state["link_done"] = False
                st.session_state["link_digits"] = ""
                st.rerun()
            return

        st.subheader("아이: 코드 입력")
        st.caption("키패드로 4자리를 입력하거나 QR을 촬영/업로드하세요.")

        # 연동 상태 안내(이미 연결되어 있을 수 있음)
        if (me or {}).get("parent_code"):
            st.info("이미 부모님과 연결된 상태예요. 다른 코드로 바꾸려면 아래에서 새 코드로 다시 연동할 수 있어요.")

        # 키패드 입력
        if "link_digits" not in st.session_state:
            st.session_state["link_digits"] = ""
        digits = str(st.session_state.get("link_digits") or "")
        digits = "".join([c for c in digits if c.isdigit()])[:4]
        st.session_state["link_digits"] = digits

        # Step chips
        step_on = 1 if len(digits) < 4 else 2
        st.markdown(
            f"""
            <div class="amf-step">
              <span class="chip {'on' if step_on==1 else ''}">1) 코드 입력</span>
              <span class="chip {'on' if step_on==2 else ''}">2) 확인</span>
              <span class="chip">3) 완료</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('<div class="amf-prefix">MF-</div>', unsafe_allow_html=True)
        st.markdown(
            "<div class='amf-digit-boxes'>"
            + "".join([f"<div class='amf-digit'>{(digits[i] if i < len(digits) else '')}</div>" for i in range(4)])
            + "</div>",
            unsafe_allow_html=True,
        )

        keypad = [
            ["1", "2", "3"],
            ["4", "5", "6"],
            ["7", "8", "9"],
            ["C", "0", "←"],
        ]
        with st.container():
            st.markdown('<div id="amf_link_keypad_anchor"></div>', unsafe_allow_html=True)
            for r_i, row in enumerate(keypad):
                cols = st.columns(3)
                for c_i, k in enumerate(row):
                    with cols[c_i]:
                        if st.button(k, use_container_width=True, key=f"link_key_{r_i}_{c_i}"):
                            if k == "C":
                                digits = ""
                            elif k == "←":
                                digits = digits[:-1]
                            else:
                                if len(digits) < 4 and k.isdigit():
                                    digits = digits + k
                            st.session_state["link_digits"] = digits
                            st.rerun()

        code = f"MF-{digits}" if len(digits) == 4 else ""

        # QR 촬영(가능한 환경)
        with st.expander("📷 QR 촬영/업로드로 입력(옵션)", expanded=False):
            img = None
            if hasattr(st, "camera_input"):
                img = st.camera_input("QR 찍기", key="link_cam")
            up = st.file_uploader("또는 QR 이미지 업로드", type=["png", "jpg", "jpeg"], key="link_up")
            if up is not None:
                img = up
            if img is not None:
                try:
                    import re
                    import requests

                    with st.spinner("QR을 읽는 중..."):
                        resp = requests.post(
                            "https://api.qrserver.com/v1/read-qr-code/",
                            files={"file": ("qr.png", img.getvalue(), "image/png")},
                            timeout=15,
                        )
                        data = resp.json()
                    txt = ""
                    try:
                        txt = (data[0].get("symbol") or [{}])[0].get("data") or ""
                    except Exception:
                        txt = ""
                    m = re.search(r"MF-\d{4}", str(txt).upper())
                    if m:
                        digits = m.group(0).split("-")[1]
                        st.session_state["link_digits"] = digits
                        st.success(f"인식됨: {m.group(0)}")
                        st.rerun()
                    else:
                        st.info("QR에서 MF-XXXX 코드를 찾지 못했어요.")
                except Exception:
                    st.info("QR 인식에 실패했어요. 키패드로 입력해주세요.")

        st.divider()
        st.subheader("연동하기")
        if not code:
            st.caption("4자리를 모두 입력하면 연결 버튼이 활성화돼요.")

        if st.button("🔗 연결하기", use_container_width=True, type="primary", disabled=not bool(code)):
            parent_name = "부모님"
            linked = None
            # 최신 원자적 함수 우선
            if hasattr(db, "link_child_with_invite_code"):
                try:
                    linked = db.link_child_with_invite_code(code, user_id)
                except Exception:
                    linked = None
            # 구버전 fallback(verify + consume만) — 가능한 경우에만
            if not linked and hasattr(db, "verify_invite_code"):
                try:
                    vr = db.verify_invite_code(code)
                except Exception:
                    vr = None
                if not vr:
                    st.error("유효하지 않거나 만료된 코드예요.")
                    return
                parent = (vr or {}).get("parent") or {}
                parent_name = (parent or {}).get("name") or parent_name
                # 여기서 실제 연결 업데이트는 link_child_with_invite_code가 없으면 보장하기 어렵기 때문에
                # 사용자에게 안내하고 종료(안전 우선)
                st.error("앱 버전이 오래되어 연동을 완료할 수 없어요. 최신 코드로 업데이트 후 다시 시도해주세요.")
                return

            if not linked:
                st.error("유효하지 않거나 만료된 코드예요.")
                return

            parent_name = linked.get("parent_name") or parent_name

            # 첫 미션/알림
            try:
                db.create_notification(user_id, "연동 완료! 🎉", f"{parent_name}과 연결되었어요.", level="success")
                db.create_notification(user_id, "첫 미션이 도착했어요! 🎁", "홈에서 오늘의 미션을 확인해볼까요?", level="success")
                if hasattr(db, "assign_daily_missions_if_needed"):
                    db.assign_daily_missions_if_needed(user_id, datetime.now().date().isoformat())
            except Exception:
                pass

            # 완료 화면으로 전환
            st.session_state["link_done"] = True
            st.session_state["link_done_parent_name"] = parent_name
            st.rerun()


if __name__ == "__main__":
    main()

