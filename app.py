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
if 'password_reset_verified' not in st.session_state:
    st.session_state.password_reset_verified = False
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

def handle_oauth_callback():
    """
    소셜 로그인 콜백 처리
    카카오, 네이버, 구글 OAuth 콜백을 처리합니다.
    """
    query_params = st.query_params
    
    # 에러 파라미터 확인
    if 'error' in query_params:
        error = query_params.get('error')
        error_description = query_params.get('error_description', '알 수 없는 오류')
        st.error(f"로그인 오류: {error_description}")
        st.query_params.clear()
        return
    
    try:
        from services.oauth_service import OAuthService
        oauth = OAuthService()
        
        # 카카오 로그인 처리
        if 'code' in query_params and 'state' not in query_params:
            code = query_params['code']
            with st.spinner("카카오 로그인 처리 중... 🐷"):
                token = oauth.get_kakao_token(code)
                if 'access_token' in token:
                    user_info = oauth.get_kakao_user_info(token['access_token'])
                    if user_info and 'id' in user_info:
                        # 카카오 사용자 정보 추출
                        nickname = user_info.get('properties', {}).get('nickname', '사용자')
                        user_id = f"kakao_{user_info['id']}"
                        
                        # 세션 저장
                        st.session_state['logged_in'] = True
                        st.session_state['user_id'] = user_id
                        st.session_state['user_name'] = nickname
                        st.session_state['username'] = nickname
                        st.session_state['user_type'] = 'parent'
                        st.session_state['oauth_provider'] = 'kakao'
                        st.session_state['access_token'] = token['access_token']
                        st.session_state['user_info'] = user_info
                        st.session_state['show_login_success'] = True
                        
                        st.success(f"🎉 환영합니다, {nickname}님!")
                        st.balloons()
                        st.query_params.clear()
                        import time
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("카카오 사용자 정보를 가져올 수 없습니다.")
                else:
                    st.error("카카오 토큰 발급에 실패했습니다.")
        
        # 네이버 로그인 처리
        elif 'code' in query_params and 'state' in query_params:
            code = query_params['code']
            state = query_params['state']
            
            # State 검증
            saved_state = st.session_state.get('naver_state')
            if saved_state != state:
                st.error("네이버 로그인 보안 검증에 실패했습니다. 다시 시도해주세요.")
                st.query_params.clear()
                return
            
            with st.spinner("네이버 로그인 처리 중... 🟢"):
                token = oauth.get_naver_token(code, state)
                if 'access_token' in token:
                    user_info = oauth.get_naver_user_info(token['access_token'])
                    if user_info and user_info.get('resultcode') == '00':
                        response = user_info.get('response', {})
                        name = response.get('name', '사용자')
                        user_id = f"naver_{response.get('id', '')}"
                        
                        # 세션 저장
                        st.session_state['logged_in'] = True
                        st.session_state['user_id'] = user_id
                        st.session_state['user_name'] = name
                        st.session_state['username'] = name
                        st.session_state['user_type'] = 'parent'
                        st.session_state['oauth_provider'] = 'naver'
                        st.session_state['access_token'] = token['access_token']
                        st.session_state['user_info'] = response
                        st.session_state['show_login_success'] = True
                        
                        st.success(f"🎉 환영합니다, {name}님!")
                        st.balloons()
                        st.query_params.clear()
                        import time
                        time.sleep(1)
                        st.rerun()
                    else:
                        error_msg = user_info.get('message', '알 수 없는 오류') if user_info else '사용자 정보 조회 실패'
                        st.error(f"네이버 사용자 정보 조회 실패: {error_msg}")
                else:
                    st.error("네이버 토큰 발급에 실패했습니다.")
        
        # 구글 로그인 처리
        elif 'code' in query_params:
            code = query_params['code']
            with st.spinner("구글 로그인 처리 중... 🔵"):
                token = oauth.get_google_token(code)
                if 'access_token' in token:
                    user_info = oauth.get_google_user_info(token['access_token'])
                    if user_info and 'id' in user_info:
                        name = user_info.get('name', '사용자')
                        user_id = f"google_{user_info['id']}"
                        
                        # 세션 저장
                        st.session_state['logged_in'] = True
                        st.session_state['user_id'] = user_id
                        st.session_state['user_name'] = name
                        st.session_state['username'] = name
                        st.session_state['user_type'] = 'parent'
                        st.session_state['oauth_provider'] = 'google'
                        st.session_state['access_token'] = token['access_token']
                        st.session_state['user_info'] = user_info
                        st.session_state['show_login_success'] = True
                        
                        st.success(f"🎉 환영합니다, {name}님!")
                        st.balloons()
                        st.query_params.clear()
                        import time
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("구글 사용자 정보를 가져올 수 없습니다.")
                else:
                    st.error("구글 토큰 발급에 실패했습니다.")
                    
    except Exception as e:
        st.error(f"로그인 처리 중 오류가 발생했습니다: {str(e)}")
        st.query_params.clear()

def login_page():
    """로그인 페이지 - 3개 소셜 로그인 지원"""
    
    # 사이드바 숨기기
    hide_sidebar_navigation()
    
    st.markdown("""
        <style>
        .stApp { background-color: #f9f9f9; }
        
        /* 돼지 애니메이션 */
        @keyframes pigBounce {
            0%, 100% {
                transform: translateY(0px) rotate(0deg) scale(1);
            }
            10% {
                transform: translateY(-10px) rotate(-3deg) scale(1.05);
            }
            20% {
                transform: translateY(-15px) rotate(3deg) scale(1.08);
            }
            30% {
                transform: translateY(-18px) rotate(-2deg) scale(1.1);
            }
            40% {
                transform: translateY(-15px) rotate(2deg) scale(1.08);
            }
            50% {
                transform: translateY(-10px) rotate(-1deg) scale(1.05);
            }
            60% {
                transform: translateY(-5px) rotate(1deg) scale(1.02);
            }
            70% {
                transform: translateY(-2px) rotate(0deg) scale(1.01);
            }
            80% {
                transform: translateY(0px) rotate(0deg) scale(1);
            }
        }
        
        .pig-animation {
            display: inline-block !important;
            animation: pigBounce 2.5s ease-in-out infinite !important;
            transform-origin: center center !important;
            will-change: transform !important;
        }
        
        .pig-animation:hover {
            animation-duration: 1s !important;
        }
        
        .stTextInput > div > div > input {
            border-radius: 10px !important;
            border: 2px solid #e0e0e0 !important;
            padding: 12px 15px !important;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #FF69B4 !important;
            box-shadow: 0 0 0 3px rgba(255, 105, 180, 0.1) !important;
        }
        
        .stRadio > div {
            flex-direction: row !important;
            gap: 15px !important;
        }
        
        .stButton > button {
            width: 100% !important;
            background: linear-gradient(135deg, #FF69B4 0%, #FF1493 100%) !important;
            color: white !important;
            border-radius: 12px !important;
            padding: 14px !important;
            font-weight: bold !important;
            transition: all 0.3s !important;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 12px rgba(255, 105, 180, 0.4) !important;
        }
        
        /* 아이디/비밀번호 찾기 버튼 스타일 */
        button[key="find_username_btn"],
        button[key="find_password_btn"] {
            background: linear-gradient(135deg, #E0E0E0 0%, #BDBDBD 100%) !important;
            color: #333 !important;
            font-size: 14px !important;
            padding: 10px !important;
        }
        
        button[key="find_username_btn"]:hover,
        button[key="find_password_btn"]:hover {
            background: linear-gradient(135deg, #D0D0D0 0%, #ADADAD 100%) !important;
            transform: translateY(-1px) !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # 로고
        st.markdown("""
            <div style='text-align: center; padding: 40px 0 30px 0;'>
                <div class='pig-animation' style='font-size: 80px; display: inline-block; cursor: pointer;'>🐷</div>
                <h1 style='color: #FF69B4; font-size: 32px; margin: 10px 0;'>AI Money Friends</h1>
                <p style='color: #888; font-size: 14px;'>아이들의 경제 교육 친구</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 소셜 로그인
        st.markdown("<p style='text-align: center; color: #666; font-size: 16px; margin-bottom: 15px;'>간편 로그인</p>", unsafe_allow_html=True)
        
        try:
            from services.oauth_service import OAuthService
            oauth = OAuthService()
            
            # 카카오
            kakao_enabled = oauth.kakao_key is not None and oauth.kakao_key != ""
            kakao_url = None
            if kakao_enabled:
                try:
                    kakao_url = oauth.get_kakao_login_url()
                except Exception as e:
                    kakao_enabled = False
            
            if kakao_url:
                st.markdown(f"""
                    <a href="{kakao_url}" target="_self" style='
                        display: block; width: 100%; padding: 14px; margin: 10px 0;
                        background: linear-gradient(135deg, #FEE500 0%, #FFD700 100%);
                        color: #000; text-align: center; text-decoration: none;
                        border-radius: 12px; font-weight: bold;
                        box-shadow: 0 2px 8px rgba(254, 229, 0, 0.3);
                        cursor: pointer; transition: all 0.3s;
                    '>🟡 카카오로 시작하기</a>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                    <div style='
                        display: block; width: 100%; padding: 14px; margin: 10px 0;
                        background: linear-gradient(135deg, #FEE500 0%, #FFD700 100%);
                        color: #000; text-align: center;
                        border-radius: 12px; font-weight: bold;
                        box-shadow: 0 2px 8px rgba(254, 229, 0, 0.3);
                    '>🟡 카카오로 시작하기</div>
                """, unsafe_allow_html=True)
                st.caption("💡 카카오 로그인을 사용하려면 Streamlit Secrets에 `KAKAO_CLIENT_ID`를 설정해주세요.")
            
            # 네이버
            naver_enabled = oauth.naver_client_id is not None and oauth.naver_client_id != ""
            naver_url = None
            if naver_enabled:
                try:
                    naver_url = oauth.get_naver_login_url()
                except Exception as e:
                    naver_enabled = False
            
            if naver_url:
                st.markdown(f"""
                    <a href="{naver_url}" target="_self" style='
                        display: block; width: 100%; padding: 14px; margin: 10px 0;
                        background: linear-gradient(135deg, #03C75A 0%, #00B347 100%);
                        color: white; text-align: center; text-decoration: none;
                        border-radius: 12px; font-weight: bold;
                        box-shadow: 0 2px 8px rgba(3, 199, 90, 0.3);
                        cursor: pointer; transition: all 0.3s;
                    '>🟢 네이버로 시작하기</a>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                    <div style='
                        display: block; width: 100%; padding: 14px; margin: 10px 0;
                        background: linear-gradient(135deg, #03C75A 0%, #00B347 100%);
                        color: white; text-align: center;
                        border-radius: 12px; font-weight: bold;
                        box-shadow: 0 2px 8px rgba(3, 199, 90, 0.3);
                    '>🟢 네이버로 시작하기</div>
                """, unsafe_allow_html=True)
                st.caption("💡 네이버 로그인을 사용하려면 Streamlit Secrets에 `NAVER_CLIENT_ID`를 설정해주세요.")
            
            # 구글
            google_enabled = oauth.google_client_id is not None and oauth.google_client_id != ""
            google_url = None
            if google_enabled:
                try:
                    google_url = oauth.get_google_login_url()
                except Exception as e:
                    google_enabled = False
            
            if google_url:
                st.markdown(f"""
                    <a href="{google_url}" target="_self" style='
                        display: block; width: 100%; padding: 14px; margin: 10px 0;
                        background: linear-gradient(135deg, #4285F4 0%, #357AE8 100%);
                        color: white; text-align: center; text-decoration: none;
                        border-radius: 12px; font-weight: bold;
                        box-shadow: 0 2px 8px rgba(66, 133, 244, 0.3);
                        cursor: pointer; transition: all 0.3s;
                    '>🔵 구글로 시작하기</a>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                    <div style='
                        display: block; width: 100%; padding: 14px; margin: 10px 0;
                        background: linear-gradient(135deg, #4285F4 0%, #357AE8 100%);
                        color: white; text-align: center;
                        border-radius: 12px; font-weight: bold;
                        box-shadow: 0 2px 8px rgba(66, 133, 244, 0.3);
                    '>🔵 구글로 시작하기</div>
                """, unsafe_allow_html=True)
                st.caption("💡 구글 로그인을 사용하려면 Streamlit Secrets에 `GOOGLE_CLIENT_ID`를 설정해주세요.")
            
        except Exception as e:
            # 오류 발생 시에도 버튼은 표시
            st.markdown("""
                <div style='
                    display: block; width: 100%; padding: 14px; margin: 10px 0;
                    background: linear-gradient(135deg, #FEE500 0%, #FFD700 100%);
                    color: #000; text-align: center;
                    border-radius: 12px; font-weight: bold;
                    box-shadow: 0 2px 8px rgba(254, 229, 0, 0.3);
                '>🟡 카카오로 시작하기</div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
                <div style='
                    display: block; width: 100%; padding: 14px; margin: 10px 0;
                    background: linear-gradient(135deg, #03C75A 0%, #00B347 100%);
                    color: white; text-align: center;
                    border-radius: 12px; font-weight: bold;
                    box-shadow: 0 2px 8px rgba(3, 199, 90, 0.3);
                '>🟢 네이버로 시작하기</div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
                <div style='
                    display: block; width: 100%; padding: 14px; margin: 10px 0;
                    background: linear-gradient(135deg, #4285F4 0%, #357AE8 100%);
                    color: white; text-align: center;
                    border-radius: 12px; font-weight: bold;
                    box-shadow: 0 2px 8px rgba(66, 133, 244, 0.3);
                '>🔵 구글로 시작하기</div>
            """, unsafe_allow_html=True)
            
            st.error(f"소셜 로그인 초기화 실패: {e}")
            st.info("💡 Streamlit Secrets를 확인해주세요.")
        
        # 구분선
        st.markdown("""
            <div style='display: flex; align-items: center; margin: 25px 0;'>
                <div style='flex: 1; height: 1px; background: #ddd;'></div>
                <span style='padding: 0 15px; color: #999;'>또는</span>
                <div style='flex: 1; height: 1px; background: #ddd;'></div>
            </div>
        """, unsafe_allow_html=True)
        
        # 아이디 로그인
        st.markdown("<p style='text-align: center; color: #666; font-size: 16px; margin-bottom: 15px;'>👤 아이디로 로그인</p>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("아이디", placeholder="아이디를 입력하세요", label_visibility="collapsed")
            password = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요", label_visibility="collapsed")
            
            col_a, col_b = st.columns(2)
            with col_a:
                user_type = st.radio("", ["부모님", "아이"], horizontal=True, label_visibility="collapsed")
            
            age = None
            if user_type == "아이":
                with col_b:
                    age = st.number_input("나이", 5, 18, 10, label_visibility="collapsed")
            
            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("🚀 로그인하기")
            
            if submitted and username and password:
                with st.spinner("로그인 중..."):
                    user_type_value = 'parent' if user_type == '부모님' else 'child'
                    user = db.get_user_by_username(username)
                    
                    if user and db.verify_password(password, user['password_hash']):
                        if user['user_type'] != user_type_value:
                            type_kr = "부모님" if user['user_type'] == 'parent' else "아이"
                            st.error(f"❌ 이 계정은 **{type_kr}** 계정입니다.")
                        else:
                            # 로그인 성공
                            st.session_state['logged_in'] = True
                            st.session_state['user_id'] = user['id']
                            st.session_state['user_name'] = user['name']
                            st.session_state['username'] = username
                            st.session_state['user_type'] = user_type_value
                            if age:
                                st.session_state['age'] = age
                            st.session_state.show_login_success = True
                            
                            st.success(f"🎉 환영합니다, {user['name']}님!")
                            st.balloons()
                            import time
                            time.sleep(1)
                            st.rerun()
                    else:
                        st.error("❌ 아이디나 비밀번호가 틀렸습니다.")
            
            # 아이디 찾기 / 비밀번호 찾기 링크
            st.markdown("<br>", unsafe_allow_html=True)
            col_find1, col_find2 = st.columns(2)
            with col_find1:
                if st.button("🔍 아이디 찾기", use_container_width=True, key="find_username_btn", 
                            help="이름과 부모 코드로 아이디를 찾습니다"):
                    st.session_state.show_username_find = True
                    st.session_state.show_password_reset = False
                    st.rerun()
            with col_find2:
                if st.button("🔑 비밀번호 찾기", use_container_width=True, key="find_password_btn",
                            help="아이디, 이름, 부모 코드로 비밀번호를 재설정합니다"):
                    st.session_state.show_password_reset = True
                    st.session_state.show_username_find = False
                    st.rerun()
        
        # 아이디 찾기 섹션
        if st.session_state.get('show_username_find', False):
            st.markdown("---")
            st.markdown("### 🔍 아이디 찾기")
            
            with st.form("find_username_form"):
                find_name = st.text_input("이름", placeholder="가입 시 입력한 이름을 입력하세요", key="find_username_name")
                find_parent_code = st.text_input("부모 코드", placeholder="8자리 부모 코드를 입력하세요", key="find_username_code")
                
                find_submitted = st.form_submit_button("아이디 찾기", use_container_width=True)
                
                if find_submitted:
                    if find_name and find_parent_code:
                        # 데이터베이스에서 사용자 찾기
                        users = db.get_users_by_parent_code(find_parent_code)
                        found_users = [u for u in users if u.get('name') == find_name]
                        
                        if found_users:
                            usernames = [u['username'] for u in found_users]
                            st.session_state.found_usernames = usernames
                            st.session_state.show_found_usernames = True
                            st.success(f"✅ 찾은 아이디: {', '.join(usernames)}")
                        else:
                            st.error("❌ 일치하는 정보를 찾을 수 없습니다. 이름과 부모 코드를 확인해주세요.")
                    else:
                        st.warning("⚠️ 이름과 부모 코드를 모두 입력해주세요.")
            
            if st.button("↩️ 로그인으로 돌아가기", use_container_width=True, key="back_from_find_username"):
                st.session_state.show_username_find = False
                st.session_state.show_found_usernames = False
                st.rerun()
        
        # 비밀번호 찾기 섹션
        if st.session_state.get('show_password_reset', False):
            st.markdown("---")
            st.markdown("### 🔑 비밀번호 찾기")
            
            with st.form("find_password_form"):
                reset_username = st.text_input("아이디", placeholder="비밀번호를 찾을 아이디를 입력하세요", key="reset_password_username")
                reset_name = st.text_input("이름", placeholder="가입 시 입력한 이름을 입력하세요", key="reset_password_name")
                reset_parent_code = st.text_input("부모 코드", placeholder="8자리 부모 코드를 입력하세요", key="reset_password_code")
                
                reset_submitted = st.form_submit_button("비밀번호 재설정", use_container_width=True)
                
                if reset_submitted:
                    if reset_username and reset_name and reset_parent_code:
                        # 사용자 확인
                        user = db.get_user_by_username(reset_username)
                        
                        if user and user.get('name') == reset_name and user.get('parent_code') == reset_parent_code:
                            st.session_state.verified_user_id = user['id']
                            st.session_state.saved_username = reset_username
                            st.success("✅ 본인 확인이 완료되었습니다. 새 비밀번호를 입력해주세요.")
                            st.session_state.show_password_reset = True
                            st.session_state.password_reset_verified = True
                        else:
                            st.error("❌ 일치하는 정보를 찾을 수 없습니다. 입력한 정보를 확인해주세요.")
                    else:
                        st.warning("⚠️ 모든 정보를 입력해주세요.")
            
            # 비밀번호 재설정
            if st.session_state.get('password_reset_verified', False):
                st.markdown("---")
                st.markdown("#### 새 비밀번호 설정")
                
                with st.form("reset_password_form"):
                    new_password = st.text_input("새 비밀번호", type="password", placeholder="새 비밀번호를 입력하세요", key="new_password")
                    new_password_confirm = st.text_input("새 비밀번호 확인", type="password", placeholder="새 비밀번호를 다시 입력하세요", key="new_password_confirm")
                    
                    reset_final_submitted = st.form_submit_button("비밀번호 변경", use_container_width=True)
                    
                    if reset_final_submitted:
                        if new_password and new_password_confirm:
                            if new_password == new_password_confirm:
                                if len(new_password) >= 4:
                                    if st.session_state.verified_user_id:
                                        success = db.update_user_password(st.session_state.verified_user_id, new_password)
                                        if success:
                                            st.success("✅ 비밀번호가 성공적으로 변경되었습니다!")
                                            st.session_state.show_password_reset = False
                                            st.session_state.password_reset_verified = False
                                            st.session_state.verified_user_id = None
                                            st.session_state.saved_username = ""
                                            import time
                                            time.sleep(2)
                                            st.rerun()
                                        else:
                                            st.error("❌ 비밀번호 변경에 실패했습니다.")
                                else:
                                    st.error("❌ 비밀번호는 최소 4자 이상이어야 합니다.")
                            else:
                                st.error("❌ 비밀번호가 일치하지 않습니다.")
                        else:
                            st.warning("⚠️ 비밀번호를 모두 입력해주세요.")
            
            if st.button("↩️ 로그인으로 돌아가기", use_container_width=True, key="back_from_reset_password"):
                st.session_state.show_password_reset = False
                st.session_state.password_reset_verified = False
                st.session_state.verified_user_id = None
                st.session_state.saved_username = ""
                st.rerun()
        
        # 회원가입
        st.markdown("""
            <div style='text-align: center; padding: 15px; background: #FFE4E1; border-radius: 10px; margin-top: 20px;'>
                <p style='margin: 0; color: #666;'>
                    처음이신가요? <a href='#' style='color: #FF69B4; font-weight: bold; text-decoration: none;'>회원가입 →</a>
                </p>
            </div>
        """, unsafe_allow_html=True)


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
# OAuth 콜백 처리
handle_oauth_callback()

if st.session_state.logged_in:
    main_page()
else:
    login_page()
