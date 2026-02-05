import streamlit as st

# 브랜드 컬러(Part 1 문서 기준)
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
    # 감정 색상
    "emotion_excited": "#FFD93D",
    "emotion_happy": "#6BCF7E",
    "emotion_neutral": "#B8AED9",
    "emotion_worried": "#FF9F43",
    "emotion_angry": "#EE5A6F",
}


def get_base_styles():
    """기본 CSS 스타일"""
    return f"""
    <style>
    /* 전역 리셋 */
    * {{
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }}

    /* 기본 폰트 */
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }}

    /* Streamlit 기본 스타일 제거 */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}

    /* 여백 조정 */
    .block-container {{
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        max-width: 1200px;
    }}

    /* 버튼 스타일 */
    .stButton > button {{
        width: 100%;
        height: 56px;
        border-radius: 12px;
        font-size: 17px;
        font-weight: 700;
        border: none;
        cursor: pointer;
        transition: all 0.2s ease;
    }}

    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }}

    /* 프라이머리 버튼 */
    .stButton.primary > button {{
        background: {COLORS['secondary']};
        color: {COLORS['black']};
    }}

    /* 입력 필드 */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {{
        border-radius: 12px;
        border: 1px solid {COLORS['gray_2']};
        padding: 12px 16px;
        font-size: 15px;
        height: 56px;
    }}

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {{
        border-color: {COLORS['primary']};
        box-shadow: 0 0 0 2px rgba(139, 126, 200, 0.1);
    }}

    /* 카드 스타일 */
    .card {{
        background: white;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        margin-bottom: 16px;
    }}

    /* 그라데이션 배경 */
    .gradient-bg {{
        background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['primary_dark']} 100%);
        border-radius: 16px;
        padding: 24px;
        color: white;
    }}

    /* 숫자 강조 */
    .number-highlight {{
        font-size: 28px;
        font-weight: 700;
        color: {COLORS['black']};
        line-height: 1.2;
    }}

    /* 작은 텍스트 */
    .small-text {{
        font-size: 13px;
        color: {COLORS['gray_4']};
    }}

    /* 뱃지 */
    .badge {{
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
    }}

    .badge.success {{
        background: #F6FFED;
        color: {COLORS['success']};
    }}

    .badge.danger {{
        background: #FFF1F0;
        color: {COLORS['danger']};
    }}

    .badge.warning {{
        background: #FFFBE6;
        color: {COLORS['warning']};
    }}

    /* 반응형 */
    @media (max-width: 768px) {{
        .block-container {{
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }}

        .card {{
            padding: 16px;
        }}

        .number-highlight {{
            font-size: 24px;
        }}
    }}
    </style>
    """


def inject_styles():
    """스타일 주입"""
    st.markdown(get_base_styles(), unsafe_allow_html=True)

