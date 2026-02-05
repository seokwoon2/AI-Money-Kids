from __future__ import annotations

import streamlit as st


def render_footer() -> None:
    """
    하단 푸터(스켈레톤).
    """
    st.markdown(
        """
        <div style="
            margin-top: 28px;
            padding: 18px 12px;
            border-top: 1px solid rgba(0,0,0,0.08);
            text-align: center;
            color: rgba(0,0,0,0.55);
            font-size: 12px;
            font-weight: 700;
        ">
            © AI Money Friends
        </div>
        """,
        unsafe_allow_html=True,
    )

