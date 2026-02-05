import streamlit as st

from database.db_manager import DatabaseManager
from utils.menu import render_sidebar_menu, hide_sidebar_navigation
from datetime import datetime, timedelta
import time
from utils.money_format import format_korean_won
from pathlib import Path


STOP_EMOTION_ITEMS = [
    ("excited", "신남", "assets/emotions/excited.png"),
    ("happy", "좋아", "assets/emotions/happy.png"),
    ("neutral", "보통", "assets/emotions/neutral.png"),
    ("worried", "걱정", "assets/emotions/worried.png"),
    ("angry", "화남", "assets/emotions/angry.png"),
]


def _resolve_asset_path(rel_path: str) -> str:
    p = Path(rel_path)
    if p.is_file():
        return str(p)
    return str((Path(__file__).resolve().parents[1] / rel_path).resolve())


def _guard_child(db: DatabaseManager):
    if not st.session_state.get("logged_in"):
        st.switch_page("app.py")
        return None
    user_type = st.session_state.get("user_type", "child")
    if user_type != "child":
        st.error("아이 계정에서만 사용할 수 있어요.")
        st.stop()
    user_id = int(st.session_state.get("user_id"))
    child = db.get_user_by_id(user_id)
    return child


def main():
    hide_sidebar_navigation()
    db = DatabaseManager()

    child = _guard_child(db)
    user_id = int(st.session_state.get("user_id"))
    user_name = st.session_state.get("user_name", "사용자")

    render_sidebar_menu(user_id, user_name, "child")

    # 전역 디자인 토큰/CSS는 utils/menu.py에서 주입됩니다.

    st.title("📝 용돈/지출 요청")
    st.caption("부모님께 용돈을 요청하거나 지출 승인을 요청할 수 있어요.")

    parent_code = (child or {}).get("parent_code", "")
    if not parent_code:
        st.error("부모 코드가 없어서 요청을 보낼 수 없어요. 부모님에게 코드를 확인해달라고 해주세요.")
        return

    request_type = st.selectbox("요청 종류", ["💵 용돈 요청", "🧾 지출 승인 요청"], key="req_type")
    amount = st.number_input("금액(원)", min_value=100, step=100, value=1000, key="req_amount")
    # ✅ 입력 금액 한글 표시(사용자 요청)
    st.caption(f"입력: **{int(amount):,}원** · 한글: **{format_korean_won(amount)}**")
    category = st.selectbox("카테고리", ["간식", "장난감", "학용품", "저축", "기타"], key="req_category")
    reason = st.text_input("이유", placeholder="예: 친구 생일 선물 사고 싶어요", key="req_reason")

    def _send_request(rtype: str, stop_used: bool, risk_score: int, emotion: str | None, note: str | None):
        # 감정 로그(지출 전) 저장
        try:
            if emotion:
                db.create_emotion_log(user_id, context="pre_spend", emotion=emotion, note=note or None)
        except Exception:
            pass

        # 리스크 시그널 저장
        try:
            stype = "impulse_stop" if stop_used else ("impulse_request" if rtype == "spend" else "request")
            db.create_risk_signal(
                user_id,
                signal_type=stype,
                score=int(risk_score or 0),
                context=f"{rtype}:{category}",
                note=(note or reason or "").strip()[:300] or None,
            )
        except Exception:
            pass

        # 실제 요청 생성
        rid = db.create_request(user_id, parent_code, rtype, float(amount), category=category, reason=reason or None)
        parent = db.get_parent_by_code(parent_code)
        if parent:
            db.create_notification(int(parent["id"]), "새 요청이 도착했어요", f"{user_name}의 요청: {int(amount):,}원", level="info")
        st.success("요청을 보냈어요!")
        st.rerun()

    if "용돈" in request_type:
        if st.button("요청 보내기", use_container_width=True, type="primary", key="send_allowance_req"):
            if not reason:
                st.info("이유를 간단히 적어주면 부모님이 더 잘 이해해요.")
            _send_request("allowance", stop_used=False, risk_score=0, emotion=None, note=None)
    else:
        # ✅ 지출 요청: '잠깐 멈추기' 개입
        # ✅ 잔액(추정) 표시 + 초과 요청 방지(0원 아래 지출 방지)
        try:
            beh = db.get_user_behaviors(user_id, limit=5000)
            total_allow = sum((b.get("amount") or 0) for b in beh if b.get("behavior_type") == "allowance")
            total_save = sum((b.get("amount") or 0) for b in beh if b.get("behavior_type") == "saving")
            total_spend = sum((b.get("amount") or 0) for b in beh if b.get("behavior_type") in ("planned_spending", "impulse_buying"))
            balance = float(total_allow - total_save - total_spend)
        except Exception:
            balance = 0.0
        st.caption(f"현재 잔액(추정): **{int(balance):,}원**")
        if float(amount or 0) > float(balance or 0):
            st.warning("잔액보다 큰 지출은 요청할 수 없어요. 용돈을 먼저 요청하거나 금액을 줄여주세요.")

        st.divider()
        st.subheader("🛑 잠깐 멈추기 (충동구매 방지)")
        st.caption("요청 보내기 전 10초만! 지금 기분과 이유를 확인해봐요.")

        # ✅ 감정 선택: 이모지 대신 동글이 PNG(키 저장)
        if "stop_emotion" not in st.session_state:
            st.session_state["stop_emotion"] = None
        st.markdown("**지금 기분은 어때?**")
        cols = st.columns(5)
        for i, (emo_key, emo_label, emo_img) in enumerate(STOP_EMOTION_ITEMS):
            with cols[i]:
                img_path = _resolve_asset_path(emo_img)
                if Path(img_path).is_file():
                    st.image(img_path, width=44)
                else:
                    st.markdown("<div style='height:44px'></div>", unsafe_allow_html=True)
                if st.button(
                    emo_label,
                    key=f"stop_emo_btn_{emo_key}",
                    use_container_width=True,
                    type="primary" if st.session_state.get("stop_emotion") == emo_key else "secondary",
                ):
                    st.session_state["stop_emotion"] = emo_key
                    st.rerun()
        e = st.session_state.get("stop_emotion")
        why = st.selectbox(
            "왜 사고 싶어?",
            ["그냥 갖고 싶어", "친구가 있어서", "스트레스/화가 나서", "배고파서/심심해서", "꼭 필요해서", "기타"],
            key="stop_why",
        )
        note = st.text_input("한 줄 메모(선택)", placeholder="예: 오늘 기분이 안 좋아서…", key="stop_note")

        # 간단 리스크 점수(휴리스틱)
        score = 0
        if category in ("간식", "장난감"):
            score += 35
        if float(amount or 0) >= 5000:
            score += 25
        if float(amount or 0) >= 10000:
            score += 15
        if e in ("excited", "angry"):
            score += 20
        if why in ("스트레스/화가 나서", "배고파서/심심해서", "그냥 갖고 싶어"):
            score += 20
        if not (reason or "").strip():
            score += 10
        score = min(100, score)

        if score >= 70:
            st.warning(f"지금은 충동구매일 가능성이 높아요. (시그널 점수 {score}/100)")
        elif score >= 50:
            st.info(f"잠깐만 더 생각해보면 좋아요. (시그널 점수 {score}/100)")
        else:
            st.success(f"좋아요! 그래도 한 번만 확인하고 요청 보내요. (시그널 점수 {score}/100)")

        with st.expander("대체 행동 추천", expanded=True):
            st.markdown(
                """
                - **30초 쉬기**: 물 한 모금 마시고, 깊게 숨 쉬기  
                - **내일 다시**: 장바구니(메모)에 적고 내일 다시 보기  
                - **작게 시작**: 같은 카테고리에서 더 싼 선택지 찾기  
                - **목표 생각**: 저축 목표가 있으면 ‘목표’에 더 가까운지 확인하기
                """
            )

        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ 잠깐 멈추기 성공(오늘은 안 사기)", use_container_width=True, key="do_stop", type="primary"):
                # 10초 카운트다운(호흡 가이드)
                st.info("🧘 10초만 천천히 숨 쉬어볼까? (들숨 4초 · 날숨 6초)")
                bar = st.progress(0)
                msg = st.empty()
                for i in range(10, 0, -1):
                    bar.progress(int((10 - i) * 10))
                    msg.markdown(f"**{i}초** 남았어요…")
                    time.sleep(1)
                bar.progress(100)
                msg.markdown("**좋아! 이제 결정해보자.**")

                remind = st.checkbox("내일 다시 생각하라고 알려줘(리마인더)", value=True, key="stop_remind")

                # 멈추기 기록 + 코인 보상
                try:
                    if e:
                        db.create_emotion_log(user_id, context="pre_spend", emotion=str(e), note=(note or why))
                except Exception:
                    pass
                try:
                    db.create_risk_signal(user_id, signal_type="impulse_stop", score=score, context=f"spend:{category}", note=(note or why))
                except Exception:
                    pass
                try:
                    # 멈추면 코인 보상(10)
                    if hasattr(db, "add_coins"):
                        db.add_coins(user_id, 10)
                    db.create_notification(user_id, "멈추기 성공! 🛑", "코인 10개를 받았어요 🪙", level="success")
                    if remind and hasattr(db, "create_reminder"):
                        due = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
                        db.create_reminder(
                            user_id,
                            "내일 다시 생각해볼까? 🌤️",
                            "어제는 ‘잠깐 멈추기’에 성공했어! 오늘은 어떤 선택을 하고 싶어?",
                            due_at=due,
                        )
                except Exception:
                    pass
                if hasattr(st, "toast"):
                    st.toast("🪙 코인 +10 (멈추기 성공!)", icon="🛑")
                st.success("좋아! 오늘은 한 번 참아봤어. 내일 다시 생각해도 늦지 않아.")
        with c2:
            send_disabled = float(amount or 0) > float(balance or 0)
            if st.button("👉 그래도 부모님께 요청 보내기", use_container_width=True, key="send_spend_req", disabled=send_disabled):
                _send_request("spend", stop_used=False, risk_score=score, emotion=(str(e) if e else None), note=(note or why))

    st.divider()
    st.subheader("내 요청 히스토리")
    history = db.get_requests_for_child(user_id, limit=30)
    if not history:
        st.caption("아직 요청한 기록이 없어요.")
    else:
        rows = []
        for r in history:
            rows.append(
                {
                    "날짜": r.get("created_at"),
                    "종류": "용돈" if r.get("request_type") == "allowance" else "지출",
                    "금액": int(r.get("amount") or 0),
                    "상태": r.get("status"),
                    "카테고리": r.get("category") or "",
                    "이유": r.get("reason") or "",
                }
            )
        st.dataframe(rows, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()

