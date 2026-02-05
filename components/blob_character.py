from __future__ import annotations

import base64
from pathlib import Path
from typing import Optional

import streamlit as st

#
# 동글이(감정) 이미지 렌더링 컴포넌트
#
# - 기존 레포: assets/emotions/{emotion}.png
# - 문서(대안): assets/blobs/blob_{emotion}.png
#
# 둘 중 존재하는 파일을 자동으로 사용합니다.
#


EMOTION_KEYS = ("excited", "happy", "neutral", "worried", "angry")


def _repo_root() -> Path:
    # components/ 아래 파일 기준으로 레포 루트 = 부모 폴더
    return Path(__file__).resolve().parents[1]


def _resolve_asset_path(rel_path: str) -> Path:
    """
    실행 위치가 pages/ 아래여도 경로가 깨지지 않도록
    레포 루트 기준으로도 한 번 더 찾습니다.
    """
    p = Path(rel_path)
    if p.is_file():
        return p
    return (_repo_root() / rel_path).resolve()


def _first_existing_path(*rel_paths: str) -> Optional[Path]:
    for rp in rel_paths:
        p = _resolve_asset_path(rp)
        if p.is_file():
            return p
    return None


def _png_data_uri(path: Path) -> Optional[str]:
    try:
        b = path.read_bytes()
        encoded = base64.b64encode(b).decode("ascii")
        return "data:image/png;base64," + encoded
    except Exception:
        return None


def get_blob_path(emotion: str) -> Optional[Path]:
    """
    감정 키에 해당하는 이미지 파일 Path를 반환합니다.
    """
    key = str(emotion or "").strip().lower()
    if key not in EMOTION_KEYS:
        return None

    return _first_existing_path(
        f"assets/emotions/{key}.png",
        f"assets/blobs/blob_{key}.png",
    )


def get_blob_html(emotion: str, size: int = 80, alt: str | None = None) -> str:
    """
    동글이 이미지를 인라인 HTML로 반환합니다. (st.markdown 용)

    - 이미지가 없으면 회색 원형 플레이스홀더를 반환합니다.
    """
    p = get_blob_path(emotion)
    if not p:
        return f'<div style="width:{int(size)}px;height:{int(size)}px;background:#ddd;border-radius:50%;"></div>'

    uri = _png_data_uri(p)
    if not uri:
        return f'<div style="width:{int(size)}px;height:{int(size)}px;background:#ddd;border-radius:50%;"></div>'

    alt_txt = (alt if alt is not None else str(emotion or "")).replace('"', "&quot;")
    return (
        f'<img src="{uri}" alt="{alt_txt}" '
        f'style="width:{int(size)}px;height:{int(size)}px;object-fit:contain;" />'
    )


def show_blob(emotion: str, size: int = 100, caption: str | None = None) -> None:
    """
    동글이 캐릭터 표시(센터 정렬).

    - 이미지가 없으면 안내 메시지와 플레이스홀더를 보여줍니다.
    """
    key = str(emotion or "").strip().lower()
    p = get_blob_path(key)
    if not p:
        st.markdown(
            f'<div style="text-align:center;">{get_blob_html(key, size=size)}</div>',
            unsafe_allow_html=True,
        )
        st.caption(f"이미지를 찾을 수 없어요: emotion={key!r} (assets/emotions 또는 assets/blobs 확인)")
        return

    # Streamlit 기본 이미지 렌더링(가볍고 안정적)
    st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
    st.image(str(p), width=int(size))
    if caption:
        st.caption(str(caption))
    st.markdown("</div>", unsafe_allow_html=True)

