import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
from database.db_manager import DatabaseManager
from services.analysis_service import AnalysisService
from services.gemini_service import GeminiService
from utils.menu import render_sidebar_menu, hide_sidebar_navigation

st.set_page_config(
    page_title="📊 부모 대시보드",
    page_icon="📊",
    layout="wide",
    menu_items=None
)

# Streamlit 기본 네비게이션 숨기기
hide_sidebar_navigation()
st.markdown("""
<style>
[data-testid="stSidebarNav"] {
    display: none !important;
}
nav[data-testid="stSidebarNav"] {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

# 로그인 확인
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("로그인이 필요합니다. 메인 페이지에서 로그인해주세요.")
    st.stop()

user_id = st.session_state.user_id
db = DatabaseManager()
analysis_service = AnalysisService()
gemini_service = GeminiService()

# 현재 사용자 정보
current_user = db.get_user_by_id(user_id)
user_type = current_user.get('user_type', 'child') if current_user else 'child'

# 부모 전용 페이지 확인
if user_type != 'parent':
    st.warning("이 페이지는 부모 전용입니다.")
    st.stop()

parent_code = current_user['parent_code']

# 페이지 제목
st.title("📊 부모 대시보드")
st.markdown("---")

# 자녀 목록 가져오기
children = db.get_users_by_parent_code(parent_code)

if not children:
    st.info("아직 등록된 자녀가 없습니다. 자녀가 회원가입하면 여기에 표시됩니다.")
    st.stop()

# 자녀 선택
child_names = [f"{child['name']} ({child['username']})" for child in children]
selected_index = st.selectbox(
    "자녀 선택",
    range(len(children)),
    format_func=lambda i: child_names[i]
)

selected_child = children[selected_index]
child_id = selected_child['id']
child_name = selected_child['name']
child_age = selected_child.get('age')

st.markdown(f"### {child_name}님의 금융습관 분석")
st.markdown("---")

# 점수 계산 및 가져오기
with st.spinner("점수를 계산하는 중..."):
    scores = analysis_service.get_latest_scores(child_id)

# 점수 표시 (게이지 차트)
col1, col2, col3 = st.columns(3)

with col1:
    # 충동성 점수 (낮을수록 좋음)
    impulsivity = scores['impulsivity']
    fig_impulsivity = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = impulsivity,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "충동성 점수<br><span style='font-size:0.8em;color:gray'>낮을수록 좋음</span>"},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 30], 'color': "lightgreen"},
                {'range': [30, 60], 'color': "yellow"},
                {'range': [60, 100], 'color': "lightcoral"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 70
            }
        }
    ))
    fig_impulsivity.update_layout(height=250)
    st.plotly_chart(fig_impulsivity, use_container_width=True)

with col2:
    # 저축성향 점수 (높을수록 좋음)
    saving_tendency = scores['saving_tendency']
    fig_saving = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = saving_tendency,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "저축성향 점수<br><span style='font-size:0.8em;color:gray'>높을수록 좋음</span>"},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkgreen"},
            'steps': [
                {'range': [0, 40], 'color': "lightcoral"},
                {'range': [40, 70], 'color': "yellow"},
                {'range': [70, 100], 'color': "lightgreen"}
            ],
            'threshold': {
                'line': {'color': "green", 'width': 4},
                'thickness': 0.75,
                'value': 70
            }
        }
    ))
    fig_saving.update_layout(height=250)
    st.plotly_chart(fig_saving, use_container_width=True)

with col3:
    # 인내심 점수 (높을수록 좋음)
    patience = scores['patience']
    fig_patience = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = patience,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "인내심 점수<br><span style='font-size:0.8em;color:gray'>높을수록 좋음</span>"},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkgreen"},
            'steps': [
                {'range': [0, 40], 'color': "lightcoral"},
                {'range': [40, 70], 'color': "yellow"},
                {'range': [70, 100], 'color': "lightgreen"}
            ],
            'threshold': {
                'line': {'color': "green", 'width': 4},
                'thickness': 0.75,
                'value': 70
            }
        }
    ))
    fig_patience.update_layout(height=250)
    st.plotly_chart(fig_patience, use_container_width=True)

st.markdown("---")

# 점수 추이 그래프
st.subheader("📈 점수 추이 (최근 30일)")

score_history = db.get_score_history(child_id, days=30)

if score_history:
    df_scores = pd.DataFrame([
        {
            '날짜': datetime.fromisoformat(score['calculated_at'].replace('Z', '+00:00')).date(),
            '충동성': score['impulsivity'],
            '저축성향': score['saving_tendency'],
            '인내심': score['patience']
        }
        for score in score_history
    ])
    
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=df_scores['날짜'],
        y=df_scores['충동성'],
        mode='lines+markers',
        name='충동성',
        line=dict(color='red', width=2)
    ))
    fig_trend.add_trace(go.Scatter(
        x=df_scores['날짜'],
        y=df_scores['저축성향'],
        mode='lines+markers',
        name='저축성향',
        line=dict(color='green', width=2)
    ))
    fig_trend.add_trace(go.Scatter(
        x=df_scores['날짜'],
        y=df_scores['인내심'],
        mode='lines+markers',
        name='인내심',
        line=dict(color='blue', width=2)
    ))
    
    fig_trend.update_layout(
        xaxis_title="날짜",
        yaxis_title="점수",
        height=400,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig_trend, use_container_width=True)
else:
    st.info("아직 충분한 데이터가 없습니다. 더 많은 활동을 하면 추이를 볼 수 있습니다.")

st.markdown("---")

# AI 코칭 인사이트
st.subheader("💡 AI 코칭 인사이트")

if st.button("🔄 코칭 메시지 새로고침", use_container_width=True):
    st.rerun()

# 최근 행동 데이터 가져오기
recent_behaviors = db.get_user_behaviors(child_id, limit=20)

with st.spinner("코칭 메시지를 생성하는 중..."):
    coaching_message = gemini_service.generate_parent_coaching(
        child_name=child_name,
        impulsivity_score=scores['impulsivity'],
        saving_tendency=scores['saving_tendency'],
        patience_score=scores['patience'],
        recent_behaviors=recent_behaviors
    )
    
    st.info(coaching_message)

st.markdown("---")

# 행동 기록 테이블
st.subheader("📋 최근 행동 기록")

behaviors = db.get_user_behaviors(child_id, limit=20)

if behaviors:
    behavior_type_kr = {
        "saving": "💰 저축",
        "planned_spending": "📝 계획적 소비",
        "impulse_buying": "⚡ 충동구매",
        "delayed_gratification": "⏰ 인내심",
        "comparing_prices": "🔍 가격 비교"
    }
    
    df_behaviors = pd.DataFrame([
        {
            '날짜': datetime.fromisoformat(b['timestamp'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M'),
            '유형': behavior_type_kr.get(b['behavior_type'], b['behavior_type']),
            '금액': f"{b['amount']:,.0f}원" if b['amount'] else "-",
            '설명': b['description'] or "-"
        }
        for b in behaviors
    ])
    
    st.dataframe(df_behaviors, use_container_width=True, hide_index=True)
else:
    st.info("아직 기록된 행동이 없습니다.")

# 사이드바 메뉴 렌더링
render_sidebar_menu(user_id, st.session_state.user_name, user_type)

# 사이드바 통계
with st.sidebar:
    st.markdown("---")
    st.markdown("### 📊 빠른 통계")
    
    if behaviors:
        saving_count = sum(1 for b in behaviors if b['behavior_type'] == 'saving')
        impulse_count = sum(1 for b in behaviors if b['behavior_type'] == 'impulse_buying')
        planned_count = sum(1 for b in behaviors if b['behavior_type'] == 'planned_spending')
        
        st.metric("💰 저축 횟수", saving_count)
        st.metric("⚡ 충동구매", impulse_count)
        st.metric("📝 계획적 소비", planned_count)
        
        total_amount = sum(b.get('amount', 0) or 0 for b in behaviors if b.get('amount'))
        if total_amount > 0:
            st.metric("💵 총 거래 금액", f"{total_amount:,.0f}원")
    
    st.markdown("---")
    st.caption(f"**부모 코드**: `{parent_code}`")
