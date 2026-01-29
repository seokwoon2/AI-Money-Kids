import streamlit as st
from datetime import date, datetime
from database.db_manager import DatabaseManager
from utils.auth import generate_parent_code, validate_parent_code
from utils.menu import hide_sidebar_navigation

def calculate_age(birth_date: date) -> int:
    """생년월일로부터 만나이 계산"""
    today = date.today()
    age = today.year - birth_date.year
    # 생일이 아직 지나지 않았으면 1살 빼기
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1
    return age

# 페이지 설정
st.set_page_config(
    page_title="AI Money Friends",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items=None  # 기본 메뉴 숨기기
)

# 세션 상태 초기화
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = None
if 'show_password_reset' not in st.session_state:
    st.session_state.show_password_reset = False
if 'show_username_find' not in st.session_state:
    st.session_state.show_username_find = False
if 'show_found_usernames' not in st.session_state:
    st.session_state.show_found_usernames = False
if 'found_usernames' not in st.session_state:
    st.session_state.found_usernames = []
if 'find_name_input' not in st.session_state:
    st.session_state.find_name_input = ""
if 'find_parent_code_input' not in st.session_state:
    st.session_state.find_parent_code_input = ""
if 'generated_parent_code' not in st.session_state:
    st.session_state.generated_parent_code = ""
if 'code_generated' not in st.session_state:
    st.session_state.code_generated = False
if 'verified_user_id' not in st.session_state:
    st.session_state.verified_user_id = None
if 'saved_username' not in st.session_state:
    st.session_state.saved_username = ""
if 'remember_username' not in st.session_state:
    st.session_state.remember_username = False
if 'auto_login' not in st.session_state:
    st.session_state.auto_login = False
if 'login_username_value' not in st.session_state:
    st.session_state.login_username_value = ""
if 'show_login_success' not in st.session_state:
    st.session_state.show_login_success = True

db = DatabaseManager()

def login_page():
    """로그인/회원가입 페이지"""
    # 로그인하지 않았을 때 사이드바 네비게이션 숨기기
    hide_sidebar_navigation()
    
    # 사이드바 비우기
    with st.sidebar:
        st.markdown("""
        <style>
        [data-testid="stSidebarNav"] {
            display: none !important;
        }
        nav[data-testid="stSidebarNav"] {
            display: none !important;
        }
        /* 상단 여백 제거 */
        [data-testid="stSidebarContent"] {
            padding-top: 0 !important;
        }
        </style>
        """, unsafe_allow_html=True)
        st.markdown("### 💰 AI Money Friends")
        st.markdown("로그인하여 서비스를 이용하세요.")
    
    # 타이틀 섹션 (글자 크기 축소 및 줄바꿈 최적화)
    st.markdown("""
        <style>
        /* 로그인 페이지 배경 및 카드 스타일 */
        .stApp {
            background: linear-gradient(135deg, #f6f8ff 0%, #f1f4ff 100%);
        }
        
        div[data-testid="stExpander"] {
            border: none !important;
            box-shadow: 0 10px 25px rgba(0,0,0,0.05) !important;
            background-color: white !important;
            border-radius: 20px !important;
        }
        
        /* 탭 스타일 커스텀 */
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
            background-color: transparent;
        }
        
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: #f8f9fa;
            border-radius: 10px 10px 0 0;
            gap: 1px;
            padding: 10px 20px;
            font-weight: 700;
            color: #718096;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: white !important;
            color: #6366f1 !important;
            border-bottom: 3px solid #6366f1 !important;
        }

        /* 입력 필드 둥글게 */
        .stTextInput input {
            border-radius: 12px !important;
            padding: 12px 15px !important;
            border: 1px solid #e2e8f0 !important;
        }
        
        /* 버튼 스타일 */
        .stButton > button {
            border-radius: 15px !important;
            padding: 10px 24px !important;
            font-weight: 700 !important;
            transition: all 0.3s ease !important;
        }
        
        /* 메인 타이틀 디자인 */
        .login-header {
            text-align: center;
            padding: 40px 0;
        }
        .login-logo-container {
            display: flex;
            justify-content: center;
            margin-bottom: 15px;
        }
        .login-logo-circle {
            width: 80px;
            height: 80px;
            background: white;
            border-radius: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 45px;
            box-shadow: 0 10px 20px rgba(99, 102, 241, 0.15);
            border: 1px solid #eef2ff;
        }
        .login-title {
            font-size: 2.8rem;
            font-weight: 900;
            letter-spacing: -1px;
            color: #1a202c;
            margin-bottom: 8px;
        }
        .login-title span {
            background: linear-gradient(90deg, #6366f1, #8b5cf6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .login-subtitle {
            color: #718096;
            font-size: 1.1rem;
            font-weight: 500;
            letter-spacing: -0.5px;
        }
        </style>
        
        <div class="login-header">
            <div class="login-logo-container">
                <div class="login-logo-circle">🤖</div>
            </div>
            <h1 class="login-title">AI <span>Money Friends</span></h1>
            <p class="login-subtitle">우리 아이를 위한 가장 똑똑한 금융 첫걸음</p>
        </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔐 로그인", "📝 회원가입"])
    
    with tab1:
        st.markdown("""
            <div style='text-align: center; margin-bottom: 20px;'>
                <h3 style='color: #2d3748; margin-bottom: 5px;'>환영합니다! 👋</h3>
                <p style='color: #718096; font-size: 0.9rem;'>로그인 유형을 선택하고 정보를 입력해주세요.</p>
            </div>
        """, unsafe_allow_html=True)
        
        # 로그인 유형 선택 추가
        login_type = st.radio(
            "로그인 유형",
            ["👨‍👩‍👧 부모님 로그인", "👶 우리 아이 로그인"],
            key="login_user_type_radio",
            horizontal=True,
            label_visibility="collapsed"
        )
        login_type_value = 'parent' if "부모님" in login_type else 'child'
        
        # 페이지 로드 시마다 localStorage 값을 읽어와서 쿠키에 동기화
        st.markdown("""
        <script>
        (function() {
            try {
                const savedUsername = localStorage.getItem('saved_username');
                const rememberUsername = localStorage.getItem('remember_username') === 'true';
                const autoLogin = localStorage.getItem('auto_login') === 'true';
                
                if (savedUsername) {
                    document.cookie = `st_saved_username=${encodeURIComponent(savedUsername)}; path=/; max-age=31536000`;
                } else {
                    document.cookie = `st_saved_username=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT`;
                }
                if (rememberUsername) {
                    document.cookie = `st_remember_username=true; path=/; max-age=31536000`;
                } else {
                    document.cookie = `st_remember_username=false; path=/; max-age=31536000`;
                }
                if (autoLogin) {
                    document.cookie = `st_auto_login=true; path=/; max-age=31536000`;
                } else {
                    document.cookie = `st_auto_login=false; path=/; max-age=31536000`;
                }
            } catch(e) {
                console.error('localStorage 읽기 오류:', e);
            }
        })();
        </script>
        """, unsafe_allow_html=True)
        
        # 쿠키에서 localStorage 값 읽기
        try:
            cookies = st.cookies
            if 'st_saved_username' in cookies and cookies['st_saved_username']:
                st.session_state.saved_username = cookies['st_saved_username']
            else:
                st.session_state.saved_username = ""
            if 'st_remember_username' in cookies:
                st.session_state.remember_username = cookies['st_remember_username'] == 'true'
            else:
                st.session_state.remember_username = False
            if 'st_auto_login' in cookies:
                st.session_state.auto_login = cookies['st_auto_login'] == 'true'
            else:
                st.session_state.auto_login = False
        except:
            pass
        
        saved_username_value = st.session_state.get('saved_username', '')
        initial_username = st.session_state.get('login_username_value', '') or saved_username_value
        
        with st.form("login_form", clear_on_submit=False):
            form_username = st.text_input("사용자명", key="login_username_form", value=initial_username)
            form_password = st.text_input("비밀번호", type="password", key="login_password_form", value="")
            
            col_check1, col_check2 = st.columns(2)
            with col_check1:
                remember_default = st.session_state.get('remember_username', False)
                remember_username = st.checkbox("💾 아이디 저장", value=remember_default, key="remember_username_check")
            with col_check2:
                auto_default = st.session_state.get('auto_login', False)
                auto_login = st.checkbox("🚀 자동 로그인", value=auto_default, key="auto_login_check")
            
            login_clicked = st.form_submit_button("로그인", type="primary", use_container_width=True)
        
        if login_clicked:
            username = form_username
            password = form_password
            if not username:
                st.warning("⚠️ 사용자명을 입력해주세요.")
            elif not password:
                st.warning("⚠️ 비밀번호를 입력해주세요.")
            else:
                st.session_state.login_username_value = username
                user = db.get_user_by_username(username)
                if user and db.verify_password(password, user['password_hash']):
                    if user['user_type'] != login_type_value:
                        type_kr = "부모님" if user['user_type'] == 'parent' else "아이"
                        st.error(f"❌ 이 계정은 **{type_kr}** 계정입니다. 로그인 유형을 확인해주세요.")
                    else:
                        st.session_state.logged_in = True
                        st.session_state.user_id = user['id']
                        st.session_state.user_name = user['name']
                        st.session_state.show_login_success = True
                        st.session_state.login_username_value = ""
                        
                        if remember_username:
                            st.session_state.saved_username = username
                            st.session_state.remember_username = True
                            st.markdown(f"<script>localStorage.setItem('saved_username', '{username}'); localStorage.setItem('remember_username', 'true');</script>", unsafe_allow_html=True)
                        else:
                            st.session_state.saved_username = ""
                            st.session_state.remember_username = False
                            st.markdown("<script>localStorage.removeItem('saved_username'); localStorage.removeItem('remember_username');</script>", unsafe_allow_html=True)
                        
                        st.session_state.auto_login = auto_login
                        if auto_login:
                            st.markdown("<script>localStorage.setItem('auto_login', 'true');</script>", unsafe_allow_html=True)
                        else:
                            st.markdown("<script>localStorage.removeItem('auto_login');</script>", unsafe_allow_html=True)
                        
                        st.rerun()
                else:
                    st.error("❌ 사용자명 또는 비밀번호가 올바르지 않습니다.")
        
        col_find1, col_find2 = st.columns(2)
        with col_find1:
            if st.button("🔍 아이디 찾기", use_container_width=True, key="find_username"):
                st.session_state.show_username_find = True
                st.session_state.show_password_reset = False
                st.rerun()
        with col_find2:
            if st.button("🔑 비밀번호 찾기", use_container_width=True, key="find_password"):
                st.session_state.show_password_reset = True
                st.session_state.show_username_find = False
                st.rerun()

def main_page():
    """로그인 후 메인 대시보드 페이지 - 유형별 분기"""
    from utils.menu import render_sidebar_menu, hide_sidebar_navigation
    hide_sidebar_navigation()
    
    user = db.get_user_by_id(st.session_state.user_id)
    user_type = user.get('user_type', 'child') if user else 'child'
    render_sidebar_menu(st.session_state.user_id, st.session_state.user_name, user_type)
    
    if user_type == 'parent':
        parent_dashboard(st.session_state.user_name)
    else:
        child_dashboard(st.session_state.user_name)

    if st.session_state.get('show_login_success', False):
        st.balloons()
        st.session_state.show_login_success = False

def parent_dashboard(user_name):
    """부모용 대시보드 - Style B (전문적인 분석형)"""
    user = db.get_user_by_id(st.session_state.user_id)
    parent_code = user['parent_code'] if user else ""
    children = db.get_users_by_parent_code(parent_code)
    
    monthly_stats = db.get_children_behavior_stats_this_month(parent_code)
    savings_history = db.get_children_monthly_savings(parent_code)
    
    current_month = datetime.now().month
    months = []
    monthly_savings = []
    for i in range(5, -1, -1):
        m = (current_month - i - 1) % 12 + 1
        months.append(f"{m}월")
        found = False
        for row in savings_history:
            if int(row['month']) == m:
                monthly_savings.append(row['total_amount'] / 1000)
                found = True
                break
        if not found:
            monthly_savings.append(0)

    st.markdown("""
    <style>
    .main { background-color: #f0f2f6 !important; }
    .parent-header { padding: 20px 0; margin-bottom: 20px; }
    .parent-header h1 { font-size: 28px; font-weight: 700; color: #1a202c; }
    .parent-card { background-color: white; border-radius: 20px; padding: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); height: 100%; border: 1px solid #edf2f7; }
    .card-label { font-size: 18px; font-weight: 700; color: #2d3748; margin-bottom: 20px; display: flex; align-items: center; gap: 10px; }
    .child-item { display: flex; align-items: center; padding: 12px 0; border-bottom: 1px solid #f7fafc; }
    .child-avatar { width: 45px; height: 45px; background-color: #edf2ff; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 20px; margin-right: 15px; }
    .child-info { flex: 1; }
    .child-name { font-weight: 700; color: #4a5568; }
    .child-amount { font-weight: 800; color: #1a202c; text-align: right; }
    .stat-row { display: flex; justify-content: space-between; margin-top: 15px; padding-top: 15px; border-top: 1px solid #f1f4ff; }
    .stat-item { text-align: center; flex: 1; }
    .stat-val { font-size: 18px; font-weight: 800; color: #1a202c; }
    .stat-lbl { font-size: 12px; color: #a0aec0; margin-top: 4px; }
    .tip-item { background-color: #f8faff; border-radius: 12px; padding: 12px 15px; margin-bottom: 10px; font-size: 14px; color: #4a5568; border-left: 4px solid #6366f1; }
    .chart-container { height: 150px; display: flex; align-items: flex-end; justify-content: space-around; padding: 10px 0; gap: 5px; }
    .chart-bar { background: #6366f1; width: 30px; border-radius: 5px 5px 0 0; position: relative; transition: height 0.5s ease; }
    .chart-bar:hover { background: #4f46e5; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f'<div class="parent-header"><h1>안녕하세요, {user_name}님 👋</h1></div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1.2, 1, 0.8])
    
    with col1:
        bars_html = ""
        labels_html = ""
        max_val = max(monthly_savings) if monthly_savings and max(monthly_savings) > 0 else 100
        for m, v in zip(months, monthly_savings):
            height = (v / max_val) * 100
            bars_html += f'<div class="chart-bar" style="height: {height}%;" title="{int(v*1000):,}원"></div>'
            labels_html += f'<div style="width: 30px; text-align: center;">{m}</div>'

        monthly_total = monthly_stats.get('monthly_total', 0) or 0
        yesterday_total = monthly_stats.get('yesterday_total', 0) or 0
        
        st.markdown(f"""
        <div class="parent-card">
            <div class="card-label">📈 이번 달 가족 저축액 <span style="margin-left:auto; background:#6366f1; color:white; font-size:11px; padding:2px 8px; border-radius:10px;">자세히 보기</span></div>
            <div class="chart-container">{bars_html}</div>
            <div style="display: flex; justify-content: space-around; font-size: 10px; color: #a0aec0; margin-bottom: 15px;">{labels_html}</div>
            <div class="stat-row">
                <div class="stat-item"><div class="stat-val">{int(monthly_total):,}원</div><div class="stat-lbl">이번달 총 저축</div></div>
                <div class="stat-item"><div class="stat-val">{int(yesterday_total):,}원</div><div class="stat-lbl">어제 저축</div></div>
                <div class="stat-item"><div class="stat-val">0원</div><div class="stat-lbl">목표 잔액</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        children_html = ""
        if not children:
            children_html = """
            <div style="text-align:center; padding: 40px 0; color: #a0aec0;">
                <div style="font-size: 40px; margin-bottom: 10px;">👶</div>
                등록된 자녀가 없습니다.<br>자녀 계정으로 가입 시<br>부모 코드를 입력해주세요!
            </div>
            """
        else:
            for child in children:
                child_stats = db.get_child_stats(child['id'])
                total_savings = child_stats.get('total_savings', 0) or 0
                activity_count = child_stats.get('activity_count', 0) or 0
                children_html += f"""
                <div class="child-item">
                    <div class="child-avatar">{"👦" if child.get('age', 0) > 7 else "👶"}</div>
                    <div class="child-info"><div class="child-name">{child['name']}</div></div>
                    <div class="child-amount">{int(total_savings):,}원<br><span style="font-size:11px; color:#a0aec0; font-weight:400;">{activity_count}개 활동 완료</span></div>
                </div>
                """
        
        st.markdown(f"""
        <div class="parent-card">
            <div class="card-label">👦 자녀 용돈 현황</div>
            {children_html}
            <div style="margin-top:20px;">
                <button style="width:100%; padding:10px; border-radius:10px; border:1px solid #edf2f7; background:white; color:#4a5568; font-weight:700; cursor:pointer;">총 용돈 보기</button>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="parent-card" style="text-align:center;">
            <div class="card-label">🏆 AI 금융 퀴즈 & 미션</div>
            <div style="margin: 20px auto; width:100px; height:100px; border-radius:50%; border:8px solid #eef2ff; border-top:8px solid #6366f1; display:flex; align-items:center; justify-content:center; font-size:30px;">⭐</div>
            <div style="font-weight:700; color:#4a5568; margin-bottom:5px;">이번 주 0% 완료</div>
            <div style="width:100%; height:8px; background:#eef2ff; border-radius:4px; overflow:hidden;">
                <div style="width:0%; height:100%; background:#6366f1;"></div>
            </div>
            <p style="font-size: 12px; color: #a0aec0; margin-top: 10px;">아직 진행한 미션이 없습니다.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col4, col5, col6 = st.columns([1.2, 1, 0.8])

    with col4:
        st.markdown("""
        <div class="parent-card">
            <div class="card-label">📊 금융 성장 리포트 <span style="margin-left:auto; background:#6366f1; color:white; font-size:11px; padding:2px 8px; border-radius:10px;">리포트 보기</span></div>
            <div style="height: 150px; display:flex; justify-content: center; align-items: center;"><p style="color: #a0aec0; font-size: 14px;">충분한 데이터가 쌓이면 리포트가 생성됩니다.</p></div>
            <div style="display:flex; justify-content:space-around; margin-top:10px;">
                <div style="text-align:center;"><div style="font-size:20px;">🥇</div><div style="font-size:10px; color:#a0aec0;">저축왕</div></div>
                <div style="text-align:center;"><div style="font-size:20px;">🥈</div><div style="font-size:10px; color:#a0aec0;">계획왕</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col5:
        st.markdown("""
        <div class="parent-card">
            <div class="card-label">💡 부모님 코칭 팁</div>
            <div class="tip-item">부모님 코칭팁은 아이의 소비 습관을 분석하여 제공됩니다.</div>
            <div class="tip-item">이번 주에는 '기다림의 가치'에 대해 대화해보는 건 어떨까요?</div>
        </div>
        """, unsafe_allow_html=True)

    with col6:
        st.markdown("""
        <div class="parent-card">
            <div class="card-label">⚙️ 설정 및 알림</div>
            <div style="font-size:14px; color:#4a5568; margin-bottom:20px;">알림 설정: 켜짐<br>주간 리포트: 매주 월요일</div>
            <button style="width:100%; padding:12px; border-radius:12px; border:none; background:#6366f1; color:white; font-weight:700; cursor:pointer;">코칭하기</button>
        </div>
        """, unsafe_allow_html=True)

def child_dashboard(user_name):
    """아이용 대시보드 - Style A (친근하고 귀여운 카드형)"""
    st.markdown("""
    <style>
    .main { background-color: #fcfdfe !important; }
    .dashboard-header { display: flex; align-items: center; gap: 20px; margin-bottom: 40px; padding: 20px 0; }
    .mascot-piggy { font-size: 80px; animation: swing 3s ease-in-out infinite; }
    @keyframes swing { 0%, 100% { transform: rotate(-5deg); } 50% { transform: rotate(5deg); } }
    .welcome-msg h1 { font-size: 38px; font-weight: 900; color: #1a202c; margin: 0; }
    .dash-card { border-radius: 35px; padding: 25px; position: relative; overflow: hidden; min-height: 200px; box-shadow: 0 10px 20px rgba(0,0,0,0.05); border: 4px solid white; transition: all 0.3s ease; margin-bottom: 20px; }
    .dash-card:hover { transform: translateY(-8px); box-shadow: 0 15px 30px rgba(0,0,0,0.1); }
    .card-title { font-size: 22px; font-weight: 800; display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
    .card-subtitle { font-size: 14px; font-weight: 600; opacity: 0.8; margin-bottom: 5px; }
    .card-mint { background-color: #C1F0D5; color: #1E4D2B; }
    .card-yellow { background-color: #FFE5A5; color: #7F6000; }
    .card-coral { background-color: #FFB3B3; color: #661A1A; }
    .card-lavender { background-color: #D9D1F2; color: #3D2B66; }
    .progress-bar-bg { background: rgba(255,255,255,0.4); border-radius: 15px; height: 14px; margin: 12px 0; position: relative; }
    .progress-bar-fill { background: currentColor; height: 100%; border-radius: 15px; transition: width 1s ease-in-out; }
    .badge-label { background: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 700; display: inline-block; }
    .card-mascot { position: absolute; right: 15px; bottom: 10px; font-size: 60px; opacity: 0.9; }
    @media (max-width: 768px) { .dashboard-header { flex-direction: column; text-align: center; } }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f'<div class="dashboard-header"><div class="mascot-piggy">🐷</div><div class="welcome-msg"><h1>안녕, {user_name}아! 👋</h1><p style="font-size: 17px; color: #555; font-weight: 600; margin-top:5px;">오늘도 재미있게 돈 공부 해볼까? ✨</p></div></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""<div class="dash-card card-mint"><div class="card-title">💰 내 저축함</div><div class="badge-label" style="background:#fff385; color:#7F6000; position:absolute; top:25px; right:25px;">저축왕 진행 중! 👑</div><div style="margin-top:20px;"><div class="card-subtitle">저축왕 성취도 (75%)</div><div class="progress-bar-bg"><div class="progress-bar-fill" style="width: 75%;"></div></div><h2 style="margin:5px 0; font-size: 34px; font-weight:900;">45,000원</h2><p style="margin:0; font-size:14px; font-weight:700; opacity:0.8;">🌱 목표: 60,000원</p></div><div class="card-mascot">🍯</div></div>""", unsafe_allow_html=True)
        if st.button("거래 기록 보기 📋", key="main_history", use_container_width=True):
            from utils.menu import add_to_recent
            add_to_recent("거래 내역", "pages/9_💵_용돈_관리.py", "💵")
            st.switch_page("pages/9_💵_용돈_관리.py")
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""<div class="dash-card card-coral"><div class="card-title">❓ 오늘의 퀴즈</div><p style="font-size: 18px; font-weight:700; margin-top:20px;">매일매일 지식이 쑥쑥!</p><div class="badge-label" style="margin-top:5px;">새로운 미션 도착! ✨</div><div class="card-mascot">❓</div></div>""", unsafe_allow_html=True)
        if st.button("지금 도전! 🚀", key="main_quiz", use_container_width=True):
            from utils.menu import add_to_recent
            add_to_recent("오늘의 퀴즈", "pages/7_🎯_금융_미션.py", "🎯")
            st.switch_page("pages/7_🎯_금융_미션.py")

    with col2:
        st.markdown("""<div class="dash-card card-yellow"><div class="card-title">📖 오늘의 학습</div><div class="badge-label" style="background:#C5B4E3; color:#3D2B66; position:absolute; top:25px; right:25px;">꿈꾸기 가이드 📖</div><div style="margin-top:20px;"><div class="card-subtitle">오늘의 목표 (40%)</div><div class="progress-bar-bg"><div class="progress-bar-fill" style="width: 40%;"></div></div><p style="margin:0; font-weight:700; font-size:16px;">3/5 완료</p><p style="margin:5px 0 0 0; font-size:14px; opacity:0.8;">꿈을 이루는 저축법 배우기</p></div><div class="card-mascot">🤖</div></div>""", unsafe_allow_html=True)
        if st.button("학습 계속하기 📚", key="main_study", use_container_width=True):
            from utils.menu import add_to_recent
            add_to_recent("금융 스토리", "pages/8_📖_금융_스토리.py", "📖")
            st.switch_page("pages/8_📖_금융_스토리.py")
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""<div class="dash-card card-lavender"><div class="card-title">🎯 나의 목표</div><div style="margin-top:20px;"><div class="card-subtitle">자전거 사기 (10%)</div><div class="progress-bar-bg"><div class="progress-bar-fill" style="width: 10%;"></div></div><p style="margin:0; font-weight:700; font-size:16px;">"새 자전거 사기" 🚲</p><p style="margin:5px 0 0 0; font-size:14px; font-weight:700;">남은 금액: 54,000원</p></div><div class="card-mascot">🎯</div></div>""", unsafe_allow_html=True)
        if st.button("목표 관리하기 🧸", key="main_goal", use_container_width=True):
            from utils.menu import add_to_recent
            add_to_recent("거래 내역", "pages/9_💵_용돈_관리.py", "💵")
            st.switch_page("pages/9_💵_용돈_관리.py")

# 메인 로직
if st.session_state.logged_in:
    main_page()
else:
    login_page()
