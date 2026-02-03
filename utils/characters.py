from __future__ import annotations


def get_character_catalog() -> list[dict]:
    """
    캐릭터 카탈로그(가벼운 1차 버전)
    - code: DB 저장용
    - name/role: UI 표기용
    - emoji/colors: 카드 스타일용
    """
    return [
        {
            "code": "biscuit_mouse",
            "name": "비스킷",
            "role": "디지털 쥐",
            "emoji": "🐭",
            "colors": ("#86EFAC", "#FDE68A"),
        },
        {
            "code": "mochika_unicorn",
            "name": "모치카",
            "role": "마법 유니콘",
            "emoji": "🦄",
            "colors": ("#FBCFE8", "#A7F3D0"),
        },
        {
            "code": "pompuff_dog",
            "name": "폼퍼프",
            "role": "퍼핀 강아지",
            "emoji": "🐶",
            "colors": ("#93C5FD", "#FBCFE8"),
        },
    ]


def get_character_by_code(code: str | None) -> dict | None:
    if not code:
        return None
    code = str(code).strip()
    for c in get_character_catalog():
        if c.get("code") == code:
            return c
    return None


def get_skin_catalog() -> list[dict]:
    """
    스킨 카탈로그(간단 버전)
    - code: "{character_code}:{skin_id}"
    - required_level: 해금 레벨
    """
    skins: list[dict] = []
    for ch in get_character_catalog():
        ccode = ch["code"]
        # 기본 스킨
        skins.append(
            {
                "code": f"{ccode}:default",
                "character_code": ccode,
                "name": "기본",
                "emoji": ch.get("emoji", "🐾"),
                "required_level": 1,
                "price": 0,
            }
        )
        # 상점 스킨(코인 구매)
        skins.append(
            {
                "code": f"{ccode}:neon",
                "character_code": ccode,
                "name": "네온",
                "emoji": "💡",
                "required_level": 4,
                "price": 120,
            }
        )
        skins.append(
            {
                "code": f"{ccode}:space",
                "character_code": ccode,
                "name": "우주",
                "emoji": "🪐",
                "required_level": 8,
                "price": 240,
            }
        )
    return skins


def get_skins_for_character(character_code: str | None) -> list[dict]:
    if not character_code:
        return []
    return [s for s in get_skin_catalog() if s.get("character_code") == character_code]


def get_skin_by_code(skin_code: str | None) -> dict | None:
    if not skin_code:
        return None
    skin_code = str(skin_code).strip()
    for s in get_skin_catalog():
        if s.get("code") == skin_code:
            return s
    return None


