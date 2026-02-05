import streamlit as st

import base64
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Optional

from utils.menu import render_sidebar_menu, hide_sidebar_navigation
from utils.db import get_db


EMOTION_ASSETS = {
    "excited": "assets/emotions/excited.png",
    "happy": "assets/emotions/happy.png",
    "neutral": "assets/emotions/neutral.png",
    "worried": "assets/emotions/worried.png",
    "angry": "assets/emotions/angry.png",
}

# 로컬 파일이 없을 때만 사용하는 폴백(기존 디자인 리소스)
EMOTION_REMOTE_FALLBACKS = {
    "excited": "https://www.genspark.ai/api/files/s/HJIiPUqW?cache_control=3600",
    "happy": "https://www.genspark.ai/api/files/s/o8zRj6rJ?cache_control=3600",
    "neutral": "https://www.genspark.ai/api/files/s/iwSejoix?cache_control=3600",
    "worried": "https://www.genspark.ai/api/files/s/Yvgb7hPR?cache_control=3600",
    "angry": "https://www.genspark.ai/api/files/s/56HvDG9j?cache_control=3600",
}

EMOTION_LABELS = {
    "excited": "신남",
    "happy": "좋아",
    "neutral": "보통",
    "worried": "걱정",
    "angry": "화남",
}

TYPE_LABELS = ["지출 전", "저축", "오늘 기분"]


def _resolve_asset_path(rel_path: str) -> Path:
    p = Path(rel_path)
    if p.is_file():
        return p
    # pages/ 아래에서 실행될 수도 있어서, 레포 루트를 기준으로 한 번 더 시도
    return (Path(__file__).resolve().parents[1] / rel_path).resolve()


def _try_make_png_data_uri(rel_path: str) -> Optional[str]:
    try:
        p = _resolve_asset_path(rel_path)
        if not p.is_file():
            return None
        encoded = base64.b64encode(p.read_bytes()).decode("ascii")
        return "data:image/png;base64," + encoded
    except Exception:
        return None


def _guard_login() -> bool:
    if "logged_in" not in st.session_state or not st.session_state.logged_in:
        st.warning("⚠️ 로그인이 필요합니다.")
        return False
    if not st.session_state.get("user_id"):
        st.warning("⚠️ 사용자 정보가 없어요. 다시 로그인해주세요.")
        return False
    return True


def _inject_page_css():
    # ✅ f-string 금지 (CSS의 { }가 파이썬 포맷으로 해석될 수 있음)
    css = """
    /* ===== 감정 기록: 카카오뱅크 스타일(페이지 스코프) ===== */
    div[data-testid="stAppViewContainer"]:has(#amf_emotion_page_anchor) {
        background: white;
    }

    div[data-testid="stAppViewContainer"]:has(#amf_emotion_page_anchor) .block-container{
        padding-top: 18px !important;
        padding-bottom: 26px !important;
        padding-left: 22px !important;
        padding-right: 22px !important;
        max-width: 860px !important;
    }

    /* 헤더 */
    div[data-testid="stVerticalBlock"]:has(#amf_emotion_header_anchor){
        margin-bottom: 10px !important;
    }
    div[data-testid="stVerticalBlock"]:has(#amf_emotion_header_anchor) .amf-emo-title{
        font-size: 20px;
        font-weight: 900;
        color: #111;
        letter-spacing: -0.2px;
        line-height: 1.2;
        text-align: center;
        padding: 4px 0;
    }
    div[data-testid="stVerticalBlock"]:has(#amf_emotion_header_anchor) .stButton > button{
        height: 40px !important;
        width: 44px !important;
        padding: 0 !important;
        border-radius: 10px !important;
        border: 1px solid #E5E7EB !important;
        background: white !important;
        color: #111 !important;
        font-weight: 900 !important;
        box-shadow: none !important;
    }

    /* 통계 섹션 */
    .amf-stat-wrap{
        background: #F9F9F9;
        border-radius: 16px;
        padding: 16px 14px;
        margin-top: 6px;
        margin-bottom: 14px;
    }
    .amf-stat-scroll{
        display: flex;
        gap: 12px;
        overflow-x: auto;
        padding-bottom: 6px;
        scroll-snap-type: x mandatory;
    }
    .amf-stat-scroll::-webkit-scrollbar{ height: 6px; }
    .amf-stat-scroll::-webkit-scrollbar-thumb{ background: #E5E7EB; border-radius: 999px; }
    .amf-stat-card{
        flex: 0 0 auto;
        width: 160px;
        background: white;
        border: 1px solid #EDEDED;
        border-radius: 16px;
        padding: 14px 14px 12px 14px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        scroll-snap-align: start;
    }
    .amf-stat-num{
        font-size: 28px;
        font-weight: 900;
        letter-spacing: -0.4px;
        color: #111;
        line-height: 1.1;
    }
    .amf-stat-label{
        margin-top: 6px;
        font-size: 12px;
        font-weight: 700;
        color: #6B7280;
    }

    /* 타입 탭(라디오를 탭처럼) */
    div[data-testid="stVerticalBlock"]:has(#amf_type_tabs_anchor) div[role="radiogroup"]{
        display: flex !important;
        gap: 18px !important;
        border-bottom: 1px solid #E5E7EB !important;
        padding-bottom: 8px !important;
        margin-top: 4px !important;
        margin-bottom: 8px !important;
        overflow-x: auto !important;
    }
    div[data-testid="stVerticalBlock"]:has(#amf_type_tabs_anchor) div[role="radiogroup"] > label{
        margin: 0 !important;
        padding: 0 !important;
        min-height: auto !important;
    }
    div[data-testid="stVerticalBlock"]:has(#amf_type_tabs_anchor) div[role="radiogroup"] > label > div{
        padding: 0 !important;
    }
    div[data-testid="stVerticalBlock"]:has(#amf_type_tabs_anchor) div[role="radiogroup"] span{
        font-size: 14px !important;
        font-weight: 800 !important;
        color: #9CA3AF !important;
    }
    div[data-testid="stVerticalBlock"]:has(#amf_type_tabs_anchor) label:has(input:checked) span{
        color: #111 !important;
        font-weight: 900 !important;
    }
    div[data-testid="stVerticalBlock"]:has(#amf_type_tabs_anchor) label:has(input:checked){
        position: relative;
    }
    div[data-testid="stVerticalBlock"]:has(#amf_type_tabs_anchor) label:has(input:checked)::after{
        content: "";
        position: absolute;
        left: 0;
        right: 0;
        bottom: -9px;
        height: 2px;
        background: #111;
        border-radius: 999px;
    }

    /* 감정 카드(라디오를 카드 버튼처럼) */
    div[data-testid="stVerticalBlock"]:has(#amf_emotion_cards_anchor) div[role="radiogroup"]{
        display: flex !important;
        gap: 12px !important;
        overflow-x: auto !important;
        padding: 2px 2px 10px 2px !important;
        margin-top: 8px !important;
    }
    div[data-testid="stVerticalBlock"]:has(#amf_emotion_cards_anchor) div[role="radiogroup"]::-webkit-scrollbar{ height: 6px; }
    div[data-testid="stVerticalBlock"]:has(#amf_emotion_cards_anchor) div[role="radiogroup"]::-webkit-scrollbar-thumb{ background: #E5E7EB; border-radius: 999px; }

    /* 기본 라디오 동그라미 숨기기 */
    div[data-testid="stVerticalBlock"]:has(#amf_emotion_cards_anchor) input[type="radio"]{
        position: absolute !important;
        opacity: 0 !important;
        pointer-events: none !important;
        width: 0 !important;
        height: 0 !important;
    }

    div[data-testid="stVerticalBlock"]:has(#amf_emotion_cards_anchor) div[role="radiogroup"] > label{
        flex: 0 0 auto !important;
        width: 72px !important;
        height: 92px !important;
        border-radius: 16px !important;
        border: 1px solid #E5E7EB !important;
        background: white !important;
        box-shadow: 0 1px 6px rgba(0,0,0,0.03) !important;
        margin: 0 !important;
        padding: 0 !important;
        overflow: hidden !important;
        position: relative !important;
    }

    /* 라디오 내부 레이아웃 정리 */
    div[data-testid="stVerticalBlock"]:has(#amf_emotion_cards_anchor) div[role="radiogroup"] > label > div{
        height: 100% !important;
        width: 100% !important;
        padding: 10px 8px 10px 8px !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: flex-end !important;
        gap: 6px !important;
        background-repeat: no-repeat !important;
        background-position: center 10px !important;
        background-size: 52px 52px !important;
    }
    div[data-testid="stVerticalBlock"]:has(#amf_emotion_cards_anchor) div[role="radiogroup"] > label span{
        font-size: 12px !important;
        font-weight: 900 !important;
        color: #111 !important;
        letter-spacing: -0.2px !important;
    }
    div[data-testid="stVerticalBlock"]:has(#amf_emotion_cards_anchor) label:has(input:checked){
        border: 2px solid #111 !important;
        box-shadow: none !important;
    }

    /* 감정 이미지 매핑(옵션 순서 고정) */
    div[data-testid="stVerticalBlock"]:has(#amf_emotion_cards_anchor) div[role="radiogroup"] > label:nth-child(1) > div{ background-image: url("__URI_EXCITED__"); }
    div[data-testid="stVerticalBlock"]:has(#amf_emotion_cards_anchor) div[role="radiogroup"] > label:nth-child(2) > div{ background-image: url("__URI_HAPPY__"); }
    div[data-testid="stVerticalBlock"]:has(#amf_emotion_cards_anchor) div[role="radiogroup"] > label:nth-child(3) > div{ background-image: url("__URI_NEUTRAL__"); }
    div[data-testid="stVerticalBlock"]:has(#amf_emotion_cards_anchor) div[role="radiogroup"] > label:nth-child(4) > div{ background-image: url("__URI_WORRIED__"); }
    div[data-testid="stVerticalBlock"]:has(#amf_emotion_cards_anchor) div[role="radiogroup"] > label:nth-child(5) > div{ background-image: url("__URI_ANGRY__"); }

    /* 메모 입력 */
    div[data-testid="stVerticalBlock"]:has(#amf_memo_anchor) textarea{
        min-height: 100px !important;
        border-radius: 14px !important;
        border: 1px solid #E5E7EB !important;
        box-shadow: none !important;
        padding: 12px 12px !important;
        font-size: 14px !important;
        color: #111 !important;
    }
    div[data-testid="stVerticalBlock"]:has(#amf_memo_anchor) textarea::placeholder{
        color: #9CA3AF !important;
        font-weight: 600 !important;
    }

    /* CTA 버튼 (노랑은 이 버튼만) */
    div[data-testid="stVerticalBlock"]:has(#amf_cta_anchor) .stButton > button[kind="primary"]{
        background: #FFEB00 !important;
        color: #111 !important;
        border: 0 !important;
        border-radius: 16px !important;
        height: 56px !important;
        font-size: 17px !important;
        font-weight: 900 !important;
        box-shadow: none !important;
    }
    div[data-testid="stVerticalBlock"]:has(#amf_cta_anchor) .stButton > button[kind="primary"]:hover{
        filter: brightness(0.98) !important;
    }

    /* 최근 기록 카드 */
    .amf-recent-item{
        background: #F9F9F9;
        border: 1px solid #EFEFEF;
        border-radius: 12px;
        padding: 12px 12px;
        margin-bottom: 10px;
    }
    .amf-recent-top{
        font-weight: 900;
        color: #111;
        font-size: 14px;
        letter-spacing: -0.2px;
    }
    .amf-recent-sub{
        margin-top: 2px;
        color: #6B7280;
        font-weight: 700;
        font-size: 12px;
    }
    .amf-recent-note{
        margin-top: 8px;
        color: #111;
        font-size: 13px;
        line-height: 1.4;
        white-space: pre-wrap;
        word-break: break-word;
    }
    """

    # 로컬 감정 이미지 5개를 data URI로 주입(배포 환경에서도 안전)
    excited_uri = _try_make_png_data_uri(EMOTION_ASSETS["excited"]) or EMOTION_REMOTE_FALLBACKS["excited"]
    happy_uri = _try_make_png_data_uri(EMOTION_ASSETS["happy"]) or EMOTION_REMOTE_FALLBACKS["happy"]
    neutral_uri = _try_make_png_data_uri(EMOTION_ASSETS["neutral"]) or EMOTION_REMOTE_FALLBACKS["neutral"]
    worried_uri = _try_make_png_data_uri(EMOTION_ASSETS["worried"]) or EMOTION_REMOTE_FALLBACKS["worried"]
    angry_uri = _try_make_png_data_uri(EMOTION_ASSETS["angry"]) or EMOTION_REMOTE_FALLBACKS["angry"]

    css = (
        css.replace("__URI_EXCITED__", excited_uri)
        .replace("__URI_HAPPY__", happy_uri)
        .replace("__URI_NEUTRAL__", neutral_uri)
        .replace("__URI_WORRIED__", worried_uri)
        .replace("__URI_ANGRY__", angry_uri)
    )
    st.markdown('<div id="amf_emotion_page_anchor"></div>', unsafe_allow_html=True)
    st.markdown("<style>\n" + css + "\n</style>", unsafe_allow_html=True)


def _compute_streak(records: list[dict]) -> int:
    """최근 기록부터 역순으로 날짜 체크, 하루 이상 빈틈 나면 중단"""
    uniq_dates: list[date] = []
    for r in records:
        dt = r.get("created_at")
        if not isinstance(dt, datetime):
            continue
        d = dt.date()
        if not uniq_dates or uniq_dates[-1] != d:
            uniq_dates.append(d)
    if not uniq_dates:
        return 0
    streak = 1
    expected = uniq_dates[0] - timedelta(days=1)
    for d in uniq_dates[1:]:
        if d == expected:
            streak += 1
            expected = expected - timedelta(days=1)
        elif d < expected:
            break
    return streak


def main():
    st.set_page_config(page_title="감정 기록", page_icon="😊", layout="wide")

    if not _guard_login():
        st.stop()

    _inject_page_css()

    hide_sidebar_navigation()

    user_id = int(st.session_state.get("user_id"))
    user_name = st.session_state.get("user_name", "사용자")
    user_type = st.session_state.get("user_type", "child")

    db = get_db()
    render_sidebar_menu(user_id, user_name, user_type)

    # ===== HEADER =====
    st.markdown('<div id="amf_emotion_header_anchor"></div>', unsafe_allow_html=True)
    h1, h2, h3 = st.columns([0.14, 0.72, 0.14], vertical_alignment="center")
    with h1:
        if st.button("←", key="emo_back_btn"):
            # "뒤로가기"는 실제 히스토리가 없어서 기본은 대시보드로 이동
            try:
                st.switch_page("pages/1_🏠_대시보드.py")
            except Exception:
                st.switch_page("app.py")
    with h2:
        st.markdown('<div class="amf-emo-title">감정 기록</div>', unsafe_allow_html=True)
    with h3:
        st.write("")

    # ===== STATISTICS =====
    week_ago = datetime.now() - timedelta(days=7)
    week_count = db.emotions.count_documents({"user_id": user_id, "created_at": {"$gte": week_ago}})
    positive_count = db.emotions.count_documents(
        {"user_id": user_id, "emotion": {"$in": ["excited", "happy"]}, "created_at": {"$gte": week_ago}}
    )
    total_records = db.emotions.count_documents({"user_id": user_id})
    level = (int(total_records or 0) // 10) + 1
    _streak_src = list(db.emotions.find({"user_id": user_id}).sort("created_at", -1).limit(120))
    streak = _compute_streak(_streak_src)
    st.markdown(
        """
        <div class="amf-stat-wrap">
          <div class="amf-stat-scroll">
            <div class="amf-stat-card">
              <div class="amf-stat-num">{week_count}</div>
              <div class="amf-stat-label">이번 주</div>
            </div>
            <div class="amf-stat-card">
              <div class="amf-stat-num">{positive_count}</div>
              <div class="amf-stat-label">긍정</div>
            </div>
            <div class="amf-stat-card">
              <div class="amf-stat-num">{streak}일</div>
              <div class="amf-stat-label">연속</div>
            </div>
            <div class="amf-stat-card">
              <div class="amf-stat-num">Lv.{level}</div>
              <div class="amf-stat-label">레벨</div>
            </div>
          </div>
        </div>
        """.format(week_count=int(week_count or 0), positive_count=int(positive_count or 0), streak=int(streak or 0), level=int(level or 1)),
        unsafe_allow_html=True,
    )

    # ===== TYPE SELECTOR =====
    st.markdown('<div id="amf_type_tabs_anchor"></div>', unsafe_allow_html=True)
    selected_type = st.radio(
        "타입",
        options=TYPE_LABELS,
        horizontal=True,
        label_visibility="collapsed",
        key="emotion_selected_type",
    )

    st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

    # ===== EMOTION BUTTONS =====
    st.markdown("<div style='font-size:16px; font-weight:900; color:#111;'>어떤 기분이었나요?</div>", unsafe_allow_html=True)
    st.markdown('<div id="amf_emotion_cards_anchor"></div>', unsafe_allow_html=True)

    emotion_options = ["excited", "happy", "neutral", "worried", "angry"]
    try:
        selected_emotion = st.radio(
            "감정 선택",
            options=emotion_options,
            format_func=lambda k: EMOTION_LABELS.get(k, k),
            horizontal=True,
            index=None,
            label_visibility="collapsed",
            key="emotion_selected_emotion",
        )
    except TypeError:
        # 구버전 Streamlit 호환( index=None 미지원 시 )
        selected_emotion = st.radio(
            "감정 선택",
            options=emotion_options,
            format_func=lambda k: EMOTION_LABELS.get(k, k),
            horizontal=True,
            label_visibility="collapsed",
            key="emotion_selected_emotion",
        )

    # ===== MEMO INPUT =====
    st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
    st.markdown('<div id="amf_memo_anchor"></div>', unsafe_allow_html=True)
    memo_text = st.text_area(
        "메모",
        value="",
        height=100,
        placeholder="오늘의 감정을 자유롭게 기록해보세요",
        label_visibility="collapsed",
        key="emotion_memo_text",
    )

    # ===== CTA BUTTON =====
    st.markdown('<div id="amf_cta_anchor"></div>', unsafe_allow_html=True)
    if st.button("기록하기", type="primary", use_container_width=True):
        if not selected_emotion:
            st.error("❌ 감정을 선택해주세요!")
        else:
            emotion_doc = {
                "user_id": user_id,
                "type": str(selected_type),
                "emotion": str(selected_emotion),
                "memo": memo_text,
                "created_at": datetime.now(),
            }
            db.emotions.insert_one(emotion_doc)
            st.success("✅ 감정이 기록되었습니다!")
            st.balloons()
            st.rerun()

    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

    # ===== RECENT RECORDS =====
    st.subheader("📝 최근 감정 기록")
    recent = list(db.emotions.find({"user_id": user_id}).sort("created_at", -1).limit(10))
    if not recent:
        st.caption("아직 기록이 없어요. 첫 감정을 남겨볼까요?")
        return

    for r in recent:
        emo_key = r.get("emotion", "")
        emo_label = EMOTION_LABELS.get(emo_key, emo_key or "-")
        type_label = r.get("type") or "-"
        dt = r.get("created_at") if isinstance(r.get("created_at"), datetime) else None
        created = dt.strftime("%m/%d %H:%M") if dt else "-"
        note = (r.get("memo") or "").strip()

        st.markdown(
            """
            <div class="amf-recent-item">
              <div class="amf-recent-top">{emo} · {typ}</div>
              <div class="amf-recent-sub">{created}</div>
              {note_block}
            </div>
            """.format(
                emo=emo_label,
                typ=type_label,
                created=created,
                note_block=(
                    '<div class="amf-recent-note">{}</div>'.format(note.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
                    if note
                    else ""
                ),
            ),
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()

