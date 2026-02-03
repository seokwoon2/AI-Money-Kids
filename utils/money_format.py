from __future__ import annotations


def _under_10000_to_korean(n: int) -> str:
    """
    0~9999를 '천/백/십' 단위로 표현(아라비아 숫자 사용, 1은 생략)
    예) 1000 -> '천', 2500 -> '2천5백', 1010 -> '천십', 15 -> '십5'
    """
    n = int(n)
    if n <= 0:
        return "0"
    thousands = n // 1000
    hundreds = (n % 1000) // 100
    tens = (n % 100) // 10
    ones = n % 10
    out = ""
    if thousands:
        out += ("" if thousands == 1 else str(thousands)) + "천"
    if hundreds:
        out += ("" if hundreds == 1 else str(hundreds)) + "백"
    if tens:
        out += ("" if tens == 1 else str(tens)) + "십"
    if ones:
        out += str(ones)
    return out or "0"


def format_korean_won(amount: float | int) -> str:
    """
    금액을 한국식 단위로 간단 표기.
    예) 10000 -> '1만원', 100000 -> '10만원', 123456 -> '12만 3,456원'
    """
    try:
        n = int(round(float(amount)))
    except Exception:
        return "-"

    if n == 0:
        return "0원"
    if n < 0:
        return f"-{format_korean_won(-n)}"

    # 1만 미만은 '천/백/십' 표기로 읽기 좋게
    if n < 10_000:
        return _under_10000_to_korean(n) + "원"

    parts: list[str] = []
    units = [
        (10**12, "조"),
        (10**8, "억"),
        (10**4, "만"),
    ]
    rest = n
    for base, label in units:
        if rest < base:
            continue
        q, rest = divmod(rest, base)
        if q <= 0:
            continue
        parts.append(f"{q}{label}")

    # 나머지(1만 미만)는 '천/백/십' 표기
    if rest:
        parts.append(_under_10000_to_korean(rest))

    # 1만/1억/1조 처럼 딱 떨어지는 경우 "원" 붙임
    out = " ".join(parts).strip()
    if out.endswith(("만", "억", "조")):
        return out + "원"
    return out + "원"

