from __future__ import annotations

import re

from database.db_manager import DatabaseManager


def validate_username(username: str) -> tuple[bool, str]:
    """
    아이디 유효성 검사(+ 중복 체크)
    - 4자 이상
    - 영문/숫자/언더스코어(_)만 허용
    - DB(users.username) 중복 방지
    """
    u = str(username or "").strip()
    if len(u) < 4:
        return False, "아이디는 4자 이상이어야 합니다"
    if not re.fullmatch(r"[a-zA-Z0-9_]+", u):
        return False, "영문, 숫자, 언더스코어(_)만 사용 가능합니다"

    try:
        db = DatabaseManager()
        existing = db.get_user_by_username(u) if hasattr(db, "get_user_by_username") else None
        if existing:
            return False, "이미 사용 중인 아이디입니다"
    except Exception:
        # DB 접근 실패 시에는 화면에서만 '형식' 통과로 처리하고,
        # 가입 완료 시 insert 시점에서 다시 한 번 충돌을 막습니다.
        pass

    return True, "사용 가능한 아이디입니다 ✓"


def validate_password(password: str) -> tuple[int, str]:
    """
    비밀번호 강도 검사
    return: (strength 0~2, text)
    - <6: 0(너무 짧아요)
    - 6~7: 1(보통)
    - 8+ 이면서 대문자+숫자 포함: 2(강함)
    - 그 외: 1(보통)
    """
    p = str(password or "")
    if len(p) < 6:
        return 0, "너무 짧아요"
    if len(p) < 8:
        return 1, "보통"
    has_upper = bool(re.search(r"[A-Z]", p))
    has_digit = bool(re.search(r"\d", p))
    if has_upper and has_digit:
        return 2, "강함"
    return 1, "보통"

