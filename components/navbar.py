from __future__ import annotations

import streamlit as st


def render_navbar(title: str = "AI Money Friends", subtitle: str | None = None) -> None:
    """
    간단한 상단 네비게이션 바(스켈레톤).
    기존 페이지에 바로 넣어도 깨지지 않도록 최소 구현만 제공합니다.
    """
    st.markdown(
        f"""
        <div style="
            display:flex;
            align-items:center;
            justify-content:space-between;
            padding: 14px 16px;
            border-radius: 16px;
            border: 1px solid rgba(0,0,0,0.08);
            background: white;
            box-shadow: 0 2px 10px rgba(0,0,0,0.04);
            margin-bottom: 14px;
        ">
          <div>
            <div style="font-weight:900; font-size:16px; letter-spacing:-0.2px;">{title}</div>
            {f'<div style="margin-top:2px; font-weight:700; font-size:12px; color:rgba(0,0,0,0.55);">{subtitle}</div>' if subtitle else ''}
          </div>
          <div style="font-size:12px; font-weight:800; color:rgba(0,0,0,0.55);">
            beta
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

