from __future__ import annotations


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

    parts: list[str] = []
    units = [
        (10**12, "조"),
        (10**8, "억"),
        (10**4, "만"),
        (1, ""),
    ]
    rest = n
    for base, label in units:
        if rest < base:
            continue
        q, rest = divmod(rest, base)
        if q <= 0:
            continue
        if label:
            parts.append(f"{q}{label}")
        else:
            parts.append(f"{q:,}")

    # 1만/1억/1조 처럼 딱 떨어지는 경우 "원" 붙임
    out = " ".join(parts).strip()
    if out.endswith(("만", "억", "조")):
        return out + "원"
    return out + "원"

