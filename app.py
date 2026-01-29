import streamlit as st
from datetime import date, datetime
from database.db_manager import DatabaseManager
from utils.auth import generate_parent_code, validate_parent_code
from utils.menu import hide_sidebar_navigation
from services.oauth_service import OAuthService

# OAuth 서비스 지연 초기화 (Streamlit 초기화 후에만 접근)
def get_oauth_service():
    """OAuth 서비스 인스턴스 가져오기 (지연 초기화)"""
    if 'oauth_service' not in st.session_state:
        try:
            st.session_state.oauth_service = OAuthService()
        except Exception as e:
            # 초기화 실패 시 빈 서비스 객체 생성 (버튼은 표시되도록)
            class EmptyOAuthService:
                def __init__(self):
                    self.client_id = None
                    self.redirect_uri = None
                def get_kakao_login_url(self):
                    return "#"
            st.session_state.oauth_service = EmptyOAuthService()
    return st.session_state.oauth_service

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
if 'show_signup' not in st.session_state:
    st.session_state.show_signup = False

db = DatabaseManager()

def login_page():
    """깔끔하고 직관적인 로그인 페이지 - 소셜 로그인 우선"""
    # 0. OAuth 콜백 처리
    query_params = st.query_params
    if "code" in query_params:
        code = query_params["code"]
        oauth_service = get_oauth_service()
        if oauth_service:
            with st.spinner("카카오 로그인 중... 🐷"):
                access_token = oauth_service.get_kakao_token(code)
            
            if access_token:
                user_info = oauth_service.get_kakao_user_info(access_token)
                
                if user_info:
                    # 카카오 로그인 성공
                    st.session_state.logged_in = True
                    st.session_state.user_id = f"kakao_{user_info['id']}"
                    st.session_state.user_name = user_info.get('name') or user_info.get('properties', {}).get('nickname', '사용자')
                    st.session_state.user_info = user_info
                    st.session_state.access_token = access_token
                    st.session_state.show_login_success = True
                    
                    st.success(f"🎉 환영합니다, {st.session_state.user_name}님!")
                    st.balloons()
                    
                    # 쿼리 파라미터 제거를 위해 리다이렉트
                    st.query_params.clear()
                    import time
                    time.sleep(1)
                    st.rerun()

    # 사이드바 숨기기
    hide_sidebar_navigation()
    
    # CSS 스타일
    st.markdown("""
        <style>
        /* 전체 배경 */
        .stApp {
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        }
        
        /* 소셜 로그인 버튼 스타일 */
        .social-btn {
            display: block;
            width: 100%;
            padding: 16px 20px;
            margin: 12px 0;
            border: none;
            border-radius: 12px;
            font-size: 16px;
            font-weight: bold;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            text-decoration: none;
            color: white;
        }
        .kakao-btn {
            background-color: #FEE500;
            color: #000000;
        }
        .kakao-btn:hover {
            background-color: #FFEB00;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(254, 229, 0, 0.4);
        }
        .google-btn {
            background-color: #4285F4;
            color: white;
            opacity: 0.6;
            cursor: not-allowed;
        }
        .naver-btn {
            background-color: #03C75A;
            color: white;
            opacity: 0.6;
            cursor: not-allowed;
        }
        
        /* 구분선 */
        .divider {
            text-align: center;
            margin: 30px 0;
            color: #999;
            position: relative;
            font-size: 14px;
        }
        .divider::before,
        .divider::after {
            content: '';
            position: absolute;
            top: 50%;
            width: 40%;
            height: 1px;
            background: #ddd;
        }
        .divider::before { left: 0; }
        .divider::after { right: 0; }
        
        /* 입력 필드 스타일 */
        .stTextInput input {
            border-radius: 10px !important;
            padding: 12px 16px !important;
            border: 2px solid #e2e8f0 !important;
            background-color: white !important;
            font-size: 15px !important;
        }
        .stTextInput input:focus {
            border-color: #3b82f6 !important;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
        }
        
        /* 라디오 버튼 스타일 */
        div[data-testid="stRadio"] label {
            font-weight: 600 !important;
            color: #475569 !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # 중앙 정렬 레이아웃
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # 로고 및 제목
        st.markdown("""
            <div style='text-align: center; padding: 40px 0 30px 0;'>
                <div style='font-size: 70px; margin-bottom: 15px;'>🐷</div>
                <h1 style='color: #FF69B4; margin: 0; font-size: 2.5rem; font-weight: 800;'>AI Money Friends</h1>
                <p style='color: #64748b; font-size: 16px; margin: 10px 0 0 0;'>
                    아이들의 경제 교육 친구
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        # 빠른 로그인 제목
        st.markdown("<h3 style='text-align: center; color: #1e293b; margin: 30px 0 20px 0; font-size: 1.3rem;'>빠른 로그인</h3>", unsafe_allow_html=True)
        
        # =====================
        # 소셜 로그인 버튼
        # =====================
        
        # 카카오 로그인
        oauth_service = get_oauth_service()
        if oauth_service and oauth_service.client_id:
            try:
                kakao_login_url = oauth_service.get_kakao_login_url()
                st.markdown(f"""
                    <a href="{kakao_login_url}" target="_self" class="social-btn kakao-btn" style="display: block; text-decoration: none;">
                        🟡 카카오로 3초 만에 시작하기
                    </a>
                """, unsafe_allow_html=True)
            except Exception:
                st.markdown("""
                    <div class="social-btn kakao-btn" style="opacity: 0.6; cursor: not-allowed;">
                        🟡 카카오로 3초 만에 시작하기 (준비 중)
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div class="social-btn kakao-btn" style="opacity: 0.6; cursor: not-allowed;">
                    🟡 카카오로 3초 만에 시작하기 (준비 중)
                </div>
            """, unsafe_allow_html=True)
        
        # 구글 로그인 (준비 중)
        st.markdown("""
            <div class="social-btn google-btn">
                🔵 구글로 시작하기 (준비 중)
            </div>
        """, unsafe_allow_html=True)
        
        # 네이버 로그인 (준비 중)
        st.markdown("""
            <div class="social-btn naver-btn">
                🟢 네이버로 시작하기 (준비 중)
            </div>
        """, unsafe_allow_html=True)
        
        # 구분선
        st.markdown("<div class='divider'>또는</div>", unsafe_allow_html=True)
        
        # =====================
        # 아이디 로그인 폼
        # =====================
        st.markdown("<h3 style='text-align: center; color: #1e293b; margin: 20px 0; font-size: 1.2rem;'>👤 아이디로 로그인</h3>", unsafe_allow_html=True)
        
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("아이디", placeholder="아이디를 입력하세요", key="login_username")
            password = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요", key="login_password")
            
            # 사용자 유형 선택
            user_type = st.radio(
                "누구신가요?",
                ["⚪ 부모님이에요", "⚪ 아이예요"],
                key="login_user_type_radio",
                horizontal=True
            )
            
            # 아이인 경우 나이 표시 (선택사항)
            user_age_display = None
            if "아이" in user_type:
                user_age_display = st.number_input("나이 (만)", min_value=5, max_value=18, value=10, key="login_age")
            
            # 로그인 버튼
            submitted = st.form_submit_button("🚀 로그인하기", type="primary", use_container_width=True)
            
            if submitted:
                if username and password:
                    with st.spinner("로그인 중..."):
                        user_type_value = 'parent' if '부모' in user_type else 'child'
                        user = db.get_user_by_username(username)
                        
                        if user and db.verify_password(password, user['password_hash']):
                            if user['user_type'] != user_type_value:
                                type_kr = "부모님" if user['user_type'] == 'parent' else "아이"
                                st.error(f"❌ 이 계정은 **{type_kr}** 계정입니다.")
                            else:
                                # 로그인 성공
                                st.session_state.logged_in = True
                                st.session_state.user_id = user['id']
                                st.session_state.user_name = user['name']
                                st.session_state.show_login_success = True
                                
                                st.success(f"🎉 환영합니다, {user['name']}님!")
                                st.balloons()
                                import time
                                time.sleep(1)
                                st.rerun()
                        else:
                            st.error("❌ 아이디나 비밀번호가 틀렸습니다.")
                else:
                    st.warning("⚠️ 아이디와 비밀번호를 모두 입력해주세요.")
        
        # 회원가입 링크
        st.markdown("""
            <div style='text-align: center; margin-top: 30px; padding: 20px 0;'>
                <p style='color: #64748b; font-size: 15px;'>
                    🆕 처음이신가요?
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        # 회원가입 버튼
        if st.button("📝 회원가입하기", use_container_width=True, key="signup_btn_main"):
            st.session_state.show_signup = True
            st.rerun()
        
        # 회원가입 섹션
        if st.session_state.get('show_signup', False):
            st.markdown("---")
            st.markdown("### 📝 회원가입")
            
            # 사용자 타입 선택
            signup_user_type = st.radio(
                "어떤 계정을 만들까요?",
                ["👨‍👩‍👧 부모님", "👶 아이"],
                key="signup_user_type",
                horizontal=True
            )
            signup_user_type_value = 'parent' if "부모님" in signup_user_type else 'child'
            
            col1, col2 = st.columns(2)
            with col1:
                signup_username = st.text_input("아이디", key="signup_username", placeholder="사용할 아이디")
                signup_password = st.text_input("비밀번호", type="password", key="signup_password", placeholder="비밀번호 (4자 이상)")
                
                if signup_password:
                    strength = 0
                    if len(signup_password) >= 4: strength += 1
                    if any(c.isdigit() for c in signup_password): strength += 1
                    if any(c.isupper() for c in signup_password) or len(signup_password) >= 8: strength += 1
                    
                    colors = ["#ff4b4b", "#ffa500", "#00c853"]
                    labels = ["약함 🔴", "보통 🟡", "강함 🟢"]
                    idx = min(strength, 2)
                    st.markdown(f"""
                        <div style="margin-top: -10px; margin-bottom: 10px;">
                            <div style="width: 100%; height: 4px; background: #eee; border-radius: 2px;">
                                <div style="width: {(idx+1)*33}%; height: 100%; background: {colors[idx]}; border-radius: 2px;"></div>
                            </div>
                            <div style="font-size: 11px; color: {colors[idx]}; margin-top: 4px; font-weight: 700;">비밀번호 안전도: {labels[idx]}</div>
                        </div>
                    """, unsafe_allow_html=True)

                signup_password_confirm = st.text_input("비밀번호 확인", type="password", key="signup_password_confirm", placeholder="비밀번호 다시 입력")
                
                if signup_password and signup_password_confirm:
                    if signup_password == signup_password_confirm:
                        st.markdown("<p style='color: #00c853; font-size: 12px; font-weight: 700; margin-top: -10px;'>✅ 비밀번호가 일치합니다!</p>", unsafe_allow_html=True)
                    else:
                        st.markdown("<p style='color: #ff4b4b; font-size: 12px; font-weight: 700; margin-top: -10px;'>❌ 비밀번호가 다릅니다.</p>", unsafe_allow_html=True)
                
                signup_name = st.text_input("이름 (닉네임)", key="signup_name", placeholder="친구들이 부를 이름")
            
            with col2:
                if signup_user_type_value == 'child':
                    birth_date = st.date_input("생년월일", value=date.today().replace(year=date.today().year - 10))
                    age = calculate_age(birth_date)
                    st.info(f"만나이: **{age}세**")
                else:
                    st.info("부모님은 나이 입력이 필요 없습니다!")
                
                if signup_user_type_value == 'parent':
                    if st.button("🔑 새 코드 만들기", use_container_width=True, key="generate_code"):
                        new_code = generate_parent_code()
                        st.session_state['signup_parent_code'] = new_code
                        st.rerun()
                
                parent_code = st.text_input(
                    "🔑 부모 코드", 
                    key="signup_parent_code", 
                    placeholder="8자리 코드 입력",
                    help="부모님은 '새 코드 만들기'를 눌러주세요. 아이는 부모님께 받은 코드를 입력하세요."
                )

            col_btn1, col_btn2 = st.columns([1, 1])
            with col_btn1:
                if st.button("✨ 가입 완료!", type="primary", use_container_width=True, key="signup_submit"):
                    if not signup_username or not signup_password or not signup_password_confirm or not signup_name or not parent_code:
                        st.error("모든 정보를 입력해주세요! 😊")
                    elif signup_password != signup_password_confirm:
                        st.error("비밀번호가 일치하지 않습니다. 🧐")
                    elif len(signup_password) < 4:
                        st.error("비밀번호는 최소 4자 이상이어야 합니다! 🔒")
                    elif not validate_parent_code(parent_code):
                        st.error("부모 코드가 올바르지 않습니다. (8자리)")
                    else:
                        try:
                            if db.get_user_by_username(signup_username):
                                st.error("이미 사용 중인 아이디입니다.")
                            else:
                                user_id = db.create_user(signup_username, signup_password, signup_name, age if signup_user_type_value == 'child' else None, parent_code, signup_user_type_value)
                                st.session_state.logged_in = True
                                st.session_state.user_id = user_id
                                st.session_state.user_name = signup_name
                                st.session_state.show_login_success = True
                                st.session_state.show_signup = False
                                st.success("🎉 환영합니다! 가입이 완료되었습니다!")
                                st.balloons()
                                import time
                                time.sleep(1)
                                st.rerun()
                        except Exception as e:
                            st.error(f"오류가 발생했습니다: {str(e)}")
            with col_btn2:
                if st.button("↩️ 로그인으로 돌아가기", use_container_width=True, key="back_to_login"):
                    st.session_state.show_signup = False
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
    # 자녀 정보 및 통계 가져오기
    user = db.get_user_by_id(st.session_state.user_id)
    parent_code = user['parent_code'] if user else ""
    children = db.get_users_by_parent_code(parent_code)
    
    # DB에서 실제 데이터 가져오기
    monthly_stats = db.get_children_behavior_stats_this_month(parent_code)
    savings_history = db.get_children_monthly_savings(parent_code)
    
    # 최근 6개월 데이터 구성
    current_month = datetime.now().month
    months = []
    monthly_savings = []
    total_savings_val = 0
    for i in range(5, -1, -1):
        m = (current_month - i - 1) % 12 + 1
        months.append(f"{m}월")
        found = False
        for row in savings_history:
            if int(row['month']) == m:
                val = row['total_amount'] or 0
                monthly_savings.append(val / 1000)
                total_savings_val += val
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
    
    /* 게이지 차트 스타일 */
    .gauge-container {
        position: relative;
        width: 120px;
        height: 120px;
        margin: 0 auto;
    }
    .gauge-bg {
        fill: none;
        stroke: #eef2ff;
        stroke-width: 10;
    }
    .gauge-fill {
        fill: none;
        stroke: #6366f1;
        stroke-width: 10;
        stroke-linecap: round;
        transform: rotate(-90deg);
        transform-origin: 50% 50%;
        transition: stroke-dasharray 0.5s ease;
    }
    .gauge-text {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        font-size: 24px;
        font-weight: 800;
        color: #6366f1;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f'<div class="parent-header"><h1>안녕하세요, {user_name}님 👋</h1></div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1.2, 1, 0.8])
    
    with col1:
        if total_savings_val == 0:
            content_html = '<div style="height:150px; display:flex; align-items:center; justify-content:center; color:#a0aec0; font-weight:600; text-align:center;">지금까지 기록된 저축액이 없어요 🪙</div>'
        else:
            bars_html = ""
            labels_html = ""
            max_val = max(monthly_savings) if monthly_savings and max(monthly_savings) > 0 else 100
            for m, v in zip(months, monthly_savings):
                height = (v / max_val) * 100
                bars_html += f'<div class="chart-bar" style="height: {height}%;" title="{int(v*1000):,}원"></div>'
                labels_html += f'<div style="width: 30px; text-align: center;">{m}</div>'
            content_html = f'<div class="chart-container">{bars_html}</div><div style="display: flex; justify-content: space-around; font-size: 10px; color: #a0aec0; margin-bottom: 15px;">{labels_html}</div>'

        monthly_total = monthly_stats.get('monthly_total', 0) or 0
        yesterday_total = monthly_stats.get('yesterday_total', 0) or 0
        
        st.markdown(f"""
<div class="parent-card">
<div class="card-label">📈 이번 달 가족 저축액 <span style="margin-left:auto; background:#6366f1; color:white; font-size:11px; padding:2px 8px; border-radius:10px;">자세히 보기</span></div>
{content_html}
<div class="stat-row">
<div class="stat-item"><div class="stat-val">{int(monthly_total):,}원</div><div class="stat-lbl">이번달 총 저축</div></div>
<div class="stat-item"><div class="stat-val">{int(yesterday_total):,}원</div><div class="stat-lbl">어제 저축</div></div>
<div class="stat-item"><div class="stat-val">0원</div><div class="stat-lbl">목표 잔액</div></div>
</div>
</div>
""", unsafe_allow_html=True)

    with col2:
        if not children:
            children_content = '<div style="text-align:center; padding: 40px 0; color: #a0aec0;"><div style="font-size: 40px; margin-bottom: 10px;">👶</div>등록된 자녀가 없습니다.<br>자녀 계정으로 가입 시<br>부모 코드를 입력해주세요!</div>'
        else:
            children_content = ""
            for child in children:
                child_stats = db.get_child_stats(child['id'])
                total_savings = child_stats.get('total_savings', 0) or 0
                activity_count = child_stats.get('activity_count', 0) or 0
                children_content += f'<div class="child-item"><div class="child-avatar">{"👦" if child.get("age", 0) > 7 else "👶"}</div><div class="child-info"><div class="child-name">{child["name"]}</div></div><div class="child-amount">{int(total_savings):,}원<br><span style="font-size:11px; color:#a0aec0; font-weight:400;">{activity_count}개 활동 완료</span></div></div>'
        
        st.markdown(f"""
<div class="parent-card">
<div class="card-label">👦 자녀 용돈 현황</div>
<div class="children-list-container">
{children_content}
</div>
<div style="margin-top:20px;">
<button style="width:100%; padding:10px; border-radius:10px; border:1px solid #edf2f7; background:white; color:#4a5568; font-weight:700; cursor:pointer;">총 용돈 보기</button>
</div>
</div>
""", unsafe_allow_html=True)

    with col3:
        # 미션 달성률 (현재는 0%로 고정, 추후 DB 연동 가능)
        percent = 0
        circumference = 2 * 3.14159 * 45
        # 0%일 때는 아예 안 보이게 처리
        gauge_fill_html = ""
        if percent > 0:
            offset = circumference * (1 - percent / 100)
            gauge_fill_html = f'<circle class="gauge-fill" cx="50" cy="50" r="45" style="stroke-dasharray: {circumference}; stroke-dashoffset: {offset};"></circle>'
        
        st.markdown(f"""
<div class="parent-card" style="text-align:center;">
<div class="card-label">🏆 AI 금융 퀴즈 & 미션</div>
<div class="gauge-container">
<svg width="120" height="120" viewBox="0 0 100 100">
<circle class="gauge-bg" cx="50" cy="50" r="45"></circle>
{gauge_fill_html}
</svg>
<div class="gauge-text">⭐</div>
</div>
<div style="font-weight:700; color:#4a5568; margin-top:15px; margin-bottom:5px;">이번 주 {percent}% 완료</div>
<p style="font-size: 12px; color: #a0aec0;">아직 진행한 미션이 없습니다.</p>
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

    st.markdown(f'<div class="dashboard-header"><div class="mascot-piggy">🐷</div><div class="welcome-msg"><h1>안녕, {user_name}! 👋</h1><p style="font-size: 17px; color: #555; font-weight: 600; margin-top:5px;">오늘도 재미있게 돈 공부 해볼까? ✨</p></div></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""<div class="dash-card card-mint"><div class="card-title">💰 내 저축함</div><div class="badge-label" style="background:#fff385; color:#7F6000; position:absolute; top:25px; right:25px;">저축왕 진행 중! 👑</div><div style="margin-top:20px;"><div class="card-subtitle">저축왕 성취도 (75%)</div><div class="progress-bar-bg"><div class="progress-bar-fill" style="width: 75%;"></div></div><h2 style="margin:5px 0; font-size: 34px; font-weight:900;">45,000원</h2><p style="margin:0; font-size:14px; font-weight:700; opacity:0.8;">🌱 목표: 60,000원</p></div><div class="card-mascot">🍯</div></div>""", unsafe_allow_html=True)
        import os
        if st.button("거래 기록 보기 📋", key="main_history", use_container_width=True):
            try:
                if os.path.exists("pages/9_💵_용돈_관리.py"):
                    from utils.menu import add_to_recent
                    try:
                        add_to_recent("거래 내역", "pages/9_💵_용돈_관리.py", "💵")
                    except: pass
                    st.switch_page("pages/9_💵_용돈_관리.py")
                else:
                    st.info("거래 내역 페이지가 준비 중입니다. 곧 만나요! 💫")
            except Exception as e:
                st.info("거래 내역 페이지가 준비 중입니다. 곧 만나요! 💫")
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""<div class="dash-card card-coral"><div class="card-title">❓ 오늘의 퀴즈</div><p style="font-size: 18px; font-weight:700; margin-top:20px;">매일매일 지식이 쑥쑥!</p><div class="badge-label" style="margin-top:5px;">새로운 미션 도착! ✨</div><div class="card-mascot">❓</div></div>""", unsafe_allow_html=True)
        if os.path.exists("pages/7_🎯_금융_미션.py"):
            if st.button("지금 도전! 🚀", key="main_quiz", use_container_width=True):
                from utils.menu import add_to_recent
                try:
                    add_to_recent("오늘의 퀴즈", "pages/7_🎯_금융_미션.py", "🎯")
                except: pass
                st.switch_page("pages/7_🎯_금융_미션.py")

    with col2:
        st.markdown("""<div class="dash-card card-yellow"><div class="card-title">📖 오늘의 학습</div><div class="badge-label" style="background:#C5B4E3; color:#3D2B66; position:absolute; top:25px; right:25px;">꿈꾸기 가이드 📖</div><div style="margin-top:20px;"><div class="card-subtitle">오늘의 목표 (40%)</div><div class="progress-bar-bg"><div class="progress-bar-fill" style="width: 40%;"></div></div><p style="margin:0; font-weight:700; font-size:16px;">3/5 완료</p><p style="margin:5px 0 0 0; font-size:14px; opacity:0.8;">꿈을 이루는 저축법 배우기</p></div><div class="card-mascot">🤖</div></div>""", unsafe_allow_html=True)
        if os.path.exists("pages/8_📖_금융_스토리.py"):
            if st.button("학습 계속하기 📚", key="main_study", use_container_width=True):
                from utils.menu import add_to_recent
                try:
                    add_to_recent("금융 스토리", "pages/8_📖_금융_스토리.py", "📖")
                except: pass
                st.switch_page("pages/8_📖_금융_스토리.py")
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""<div class="dash-card card-lavender"><div class="card-title">🎯 나의 목표</div><div style="margin-top:20px;"><div class="card-subtitle">자전거 사기 (10%)</div><div class="progress-bar-bg"><div class="progress-bar-fill" style="width: 10%;"></div></div><p style="margin:0; font-weight:700; font-size:16px;">"새 자전거 사기" 🚲</p><p style="margin:5px 0 0 0; font-size:14px; font-weight:700;">남은 금액: 54,000원</p></div><div class="card-mascot">🎯</div></div>""", unsafe_allow_html=True)
        if st.button("목표 관리하기 🧸", key="main_goal", use_container_width=True):
            try:
                if os.path.exists("pages/9_💵_용돈_관리.py"):
                    from utils.menu import add_to_recent
                    try:
                        add_to_recent("거래 내역", "pages/9_💵_용돈_관리.py", "💵")
                    except: pass
                    st.switch_page("pages/9_💵_용돈_관리.py")
                else:
                    st.info("목표 관리 페이지가 준비 중입니다. 곧 만나요! 💫")
            except Exception as e:
                st.info("목표 관리 페이지가 준비 중입니다. 곧 만나요! 💫")

# 메인 로직
if st.session_state.logged_in:
    main_page()
else:
    login_page()
