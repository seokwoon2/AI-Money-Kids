from __future__ import annotations

import streamlit as st


def inject_kakao_bank_theme() -> None:
    """
    카카오뱅크 느낌의 간단 테마 CSS(스켈레톤).

    - 기존 페이지에서 이미 개별 CSS를 강하게 주입하고 있으면,
      이 테마는 '베이스 톤' 정도로만 적용됩니다.
    """
    st.markdown(
        """
        <style>
        :root{
          --kb-yellow:#FFEB00;
          --kb-text:#111;
          --kb-muted:rgba(17,17,17,0.55);
          --kb-card:#ffffff;
          --kb-bg:#ffffff;
          --kb-border:rgba(0,0,0,0.08);
          --kb-radius:16px;
        }

        .stApp{
          background: var(--kb-bg) !important;
        }

        /* primary 버튼만 노랑 */
        .stButton > button[kind="primary"],
        button[kind="primary"]{
          background: var(--kb-yellow) !important;
          color: var(--kb-text) !important;
          border: 0 !important;
          border-radius: var(--kb-radius) !important;
          font-weight: 900 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

