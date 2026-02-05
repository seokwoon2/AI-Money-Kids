from __future__ import annotations

import streamlit as st


def render_page_header(title: str, subtitle: str | None = None, kicker: str = "AI Money Friends") -> None:
    """
    전 페이지 공통 상단 헤더(카드형).
    - utils/menu.py의 전역 토큰(--amf-*)을 사용합니다.
    """
    t = str(title or "").strip()
    sub = (str(subtitle).strip() if subtitle is not None else "")
    k = str(kicker or "").strip()

    st.markdown(
        f"""
        <div style="
            background: var(--amf-card);
            border: 1px solid var(--amf-border);
            border-radius: var(--amf-radius-xl);
            padding: 16px 18px;
            box-shadow: var(--amf-shadow);
            margin-bottom: 12px;
        ">
          <div style="
            font-size: 12px;
            font-weight: 900;
            color: var(--amf-muted);
            letter-spacing: 0.6px;
            text-transform: uppercase;
            margin-bottom: 6px;
          ">{k}</div>
          <div style="
            font-size: 22px;
            font-weight: 950;
            color: var(--amf-text);
            letter-spacing: -0.4px;
            line-height: 1.2;
          ">{t}</div>
          {f'<div style="margin-top:6px; font-size:13px; font-weight:700; color: var(--amf-muted); line-height:1.45;">{sub}</div>' if sub else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_label(label: str) -> None:
    """섹션 라벨(작게, 두꺼운 톤)"""
    st.markdown(
        f"""
        <div style="
            font-size: 12px;
            font-weight: 950;
            color: var(--amf-muted);
            letter-spacing: 0.4px;
            text-transform: uppercase;
            margin: 10px 2px 8px 2px;
        ">{str(label or '').strip()}</div>
        """,
        unsafe_allow_html=True,
    )

