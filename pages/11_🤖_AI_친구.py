import streamlit as st

from database.db_manager import DatabaseManager
from utils.menu import render_sidebar_menu, hide_sidebar_navigation


FAQ = {
    "저축": "저축은 지금 쓰지 않고 나중을 위해 돈을 모으는 거예요. 목표를 정하면 더 쉬워요!",
    "이자": "이자는 은행에 돈을 맡기면 은행이 고마워서 주는 ‘보너스 돈’이라고 생각하면 돼요.",
    "예산": "예산은 ‘이번 달에 어디에 얼마를 쓸지’ 미리 계획하는 표예요.",
    "충동구매": "충동구매는 계획 없이 갑자기 사고 싶어서 사는 거예요. 10분만 기다리면 줄어들 수 있어요!",
}


def _guard_login() -> bool:
    if not st.session_state.get("logged_in"):
        st.switch_page("app.py")
        return False
    return True


def _reply(text: str) -> str:
    t = (text or "").strip()
    if not t:
        return "무엇을 도와줄까?"
    for k, v in FAQ.items():
        if k in t:
            return v
    if "추천" in t or "조언" in t:
        return "오늘은 ‘하루에 1,000원’ 같은 작은 저축부터 해보자! 그리고 지출은 ‘계획 지출’로 적어보면 좋아."
    if "퀴즈" in t:
        return "퀴즈! ‘저축’은 (1) 지금 쓰기 (2) 나중을 위해 모으기 중 뭐일까?"
    return "좋은 질문이야! 더 자세히 말해주면 내가 더 잘 도와줄게. 예: ‘간식에 돈을 너무 써요’ 같은 상황도 좋아."


def main():
    if not _guard_login():
        return

    hide_sidebar_navigation()
    db = DatabaseManager()

    user_id = int(st.session_state.get("user_id"))
    user_name = st.session_state.get("user_name", "사용자")
    user_type = st.session_state.get("user_type", "child")

    render_sidebar_menu(user_id, user_name, user_type)

    st.title("🤖 AI 친구")
    st.caption("경제 용어, 저축 조언, 퀴즈까지! 매일 조금씩 똑똑해져요.")

    conv_id = db.get_or_create_today_conversation(user_id)
    history = db.get_conversation_messages(conv_id, limit=50)

    for m in history:
        role = m.get("role")
        content = m.get("content", "")
        with st.chat_message("user" if role == "user" else "assistant"):
            st.markdown(content)

    prompt = st.chat_input("경제 질문을 해보세요 (예: 이자, 저축, 충동구매)")
    if prompt:
        db.save_message(conv_id, "user", prompt)
        answer = _reply(prompt)
        db.save_message(conv_id, "assistant", answer)
        st.rerun()


if __name__ == "__main__":
    main()

