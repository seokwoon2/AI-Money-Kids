from __future__ import annotations

import streamlit as st


# 브랜드/테마 컬러(문서 초안 + 기존 앱 톤을 적당히 혼합)
COLORS = {
    "primary": "#8B7EC8",
    "primary_dark": "#6B5B95",
    "primary_light": "#B8AED9",
    "secondary": "#FFEB00",
    "success": "#52C41A",
    "danger": "#FF4D4F",
    "warning": "#FAAD14",
    "info": "#1890FF",
    "gray_1": "#F9F9F9",
    "gray_2": "#E8E8E8",
    "gray_3": "#999999",
    "gray_4": "#666666",
    "white": "#FFFFFF",
    "black": "#191919",
    # 감정 컬러
    "emotion_excited": "#FFD93D",
    "emotion_happy": "#6BCF7E",
    "emotion_neutral": "#B8AED9",
    "emotion_worried": "#FF9F43",
    "emotion_angry": "#EE5A6F",
}


def get_base_styles() -> str:
    """
    전역 CSS 스타일 문자열을 반환합니다.
    (필요한 페이지에서만 inject_styles()를 호출해 적용하세요.)
    """
    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }}

    /* 기본 크롬 숨김(페이지별로 원하면 주석 해제해서 사용) */
    /* #MainMenu {{visibility: hidden;}}
       footer {{visibility: hidden;}}
       header {{visibility: hidden;}} */

    .block-container {{
        max-width: 1200px;
        padding-top: 1.2rem !important;
        padding-bottom: 1.8rem !important;
    }}

    /* 기본 버튼 */
    .stButton > button {{
        width: 100%;
        border-radius: 12px !important;
        font-size: 15px !important;
        font-weight: 700 !important;
        border: 1px solid {COLORS["gray_2"]} !important;
        background: white !important;
        color: {COLORS["black"]} !important;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }}
    .stButton > button:hover {{
        transform: translateY(-1px);
        box-shadow: 0 6px 16px rgba(0,0,0,0.08);
    }}

    /* 입력 필드 */
    .stTextInput input, .stTextArea textarea {{
        border-radius: 12px !important;
        border: 1px solid {COLORS["gray_2"]} !important;
    }}
    </style>
    """


def inject_styles() -> None:
    """현재 페이지에 공통 스타일을 주입합니다."""
    st.markdown(get_base_styles(), unsafe_allow_html=True)

