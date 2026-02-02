import streamlit as st

from database.db_manager import DatabaseManager
from utils.menu import render_sidebar_menu, hide_sidebar_navigation


LESSONS = [
    {"code": "money_basic", "title": "돈이란 무엇일까?", "content": "돈은 물건이나 서비스를 살 때 사용하는 교환 수단이에요."},
    {"code": "saving", "title": "저축의 힘", "content": "저축은 미래의 목표를 위해 돈을 모으는 습관이에요."},
    {"code": "budget", "title": "예산 세우기", "content": "예산은 ‘얼마를 벌고/얼마를 쓸지’ 미리 계획하는 거예요."},
]


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

    st.title("📚 경제 교실")
    st.caption("경제를 쉽고 재미있게 배우는 공간이에요.")

    progress_rows = db.get_learning_progress(user_id)
    progress_map = {r["lesson_code"]: float(r.get("progress") or 0) for r in progress_rows}

    lesson_titles = [f"{l['title']} ({int(progress_map.get(l['code'], 0)*100)}%)" for l in LESSONS]
    idx = st.selectbox("수업 선택", list(range(len(LESSONS))), format_func=lambda i: lesson_titles[i])
    lesson = LESSONS[idx]

    st.subheader(lesson["title"])
    st.write(lesson["content"])

    st.divider()
    st.subheader("퀴즈")
    if lesson["code"] == "saving":
        q = st.radio("저축은 무엇일까요?", ["지금 다 쓰기", "나중을 위해 모으기"], index=1)
        if st.button("정답 확인", use_container_width=True):
            if q == "나중을 위해 모으기":
                st.success("정답! 저축은 미래를 위한 준비예요.")
                db.upsert_learning_progress(user_id, lesson["code"], 1.0)
                st.rerun()
            else:
                st.error("아쉬워요. 다시 생각해볼까요?")
    else:
        st.caption("이 수업의 퀴즈는 준비 중이에요.")
        if st.button("진도 50%로 저장(테스트)", use_container_width=True):
            db.upsert_learning_progress(user_id, lesson["code"], max(0.5, progress_map.get(lesson["code"], 0)))
            st.rerun()

    st.divider()
    st.subheader("내 학습 진행률")
    total = sum(progress_map.get(l["code"], 0) for l in LESSONS)
    pct = 0 if not LESSONS else total / len(LESSONS)
    st.progress(min(1.0, pct))
    st.caption(f"전체 평균 진도: {int(pct*100)}%")


if __name__ == "__main__":
    main()

