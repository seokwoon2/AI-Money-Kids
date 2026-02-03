import streamlit as st

from database.db_manager import DatabaseManager
from utils.menu import render_sidebar_menu, hide_sidebar_navigation
from utils.characters import get_character_by_code, get_skins_for_character, get_skin_by_code


def _guard_login() -> bool:
    if not st.session_state.get("logged_in"):
        st.switch_page("app.py")
        return False
    return True


def main():
    if not _guard_login():
        return

    hide_sidebar_navigation()
    db = DatabaseManager()

    user_id = int(st.session_state.get("user_id"))
    user_name = st.session_state.get("user_name", "사용자")
    user_type = st.session_state.get("user_type", "child")

    render_sidebar_menu(user_id, user_name, user_type)

    st.title("🛍️ 상점")
    st.caption("코인으로 스킨을 구매하고 캐릭터를 꾸며요.")

    me = db.get_user_by_id(user_id) or {}
    ccode = (me.get("character_code") or "").strip()
    if not ccode:
        st.info("캐릭터가 없어요. 설정에서 먼저 캐릭터를 선택해주세요.")
        return

    ch = get_character_by_code(ccode) or {}
    coins = int(me.get("coins") or 0)
    try:
        xp = int(db.get_xp(user_id) or 0) if hasattr(db, "get_xp") else 0
    except Exception:
        xp = 0
    lvl = max(1, xp // 20 + 1)

    st.markdown(f"### {ch.get('emoji','🐾')} {ch.get('name','내 캐릭터')} · Lv.{lvl}")
    st.metric("🪙 코인", f"{coins:,}")

    unlocked = set(db.get_unlocked_skins(user_id)) if hasattr(db, "get_unlocked_skins") else set()
    skins = get_skins_for_character(ccode)

    st.subheader("🎨 스킨")
    cols = st.columns(2)
    for i, s in enumerate(skins):
        with cols[i % 2]:
            code = s.get("code")
            skin = get_skin_by_code(code) or s
            req = int(skin.get("required_level") or 1)
            price = int(skin.get("price") or 0)
            owned = (code in unlocked) or price == 0  # 기본 스킨은 항상
            locked_by_level = lvl < req

            with st.container(border=True):
                st.markdown(f"**{skin.get('emoji','🎨')} {skin.get('name','스킨')}**")
                st.caption(f"필요 레벨: Lv.{req} · 가격: {'무료' if price == 0 else f'{price:,} 코인'}")

                if price == 0:
                    if st.button("적용", use_container_width=True, key=f"apply_{code}"):
                        if hasattr(db, "update_user_character_skin_code"):
                            db.update_user_character_skin_code(user_id, code)
                            st.success("스킨을 적용했어요!")
                            st.rerun()
                else:
                    if owned:
                        if st.button("적용", use_container_width=True, key=f"apply_owned_{code}"):
                            db.update_user_character_skin_code(user_id, code)
                            st.success("스킨을 적용했어요!")
                            st.rerun()
                    else:
                        if locked_by_level:
                            st.info("레벨이 부족해요.")
                        else:
                            if st.button(f"구매 ({price:,})", use_container_width=True, key=f"buy_{code}", type="primary"):
                                ok, msg = db.purchase_skin(user_id, code, price=price, required_level=req) if hasattr(db, "purchase_skin") else (False, "구매 기능이 준비되지 않았어요.")
                                if ok:
                                    st.success(msg)
                                else:
                                    st.error(msg)
                                st.rerun()


if __name__ == "__main__":
    main()

