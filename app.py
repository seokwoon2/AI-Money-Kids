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
if 'saved_phone' not in st.session_state:
    st.session_state.saved_phone = ""
if 'sms_verification' not in st.session_state:
    st.session_state.sms_verification = {}
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
if 'current_auth_screen' not in st.session_state:
    st.session_state.current_auth_screen = 'login'  # 'login', 'signup', 'find_username', 'find_password'

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

def show_find_username_page():
    """아이디 찾기 페이지"""
    hide_sidebar_navigation()
    
    st.markdown("""
        <style>
        .stApp { background-color: #f9f9f9; }
        .back-button-container {
            margin-bottom: 20px;
        }
        </style>
        """, unsafe_allow_html=True)
    
    # 뒤로가기 버튼
    if st.button("← 로그인으로 돌아가기", key="back_to_login_from_find_username"):
        st.session_state.current_auth_screen = 'login'
        st.session_state.show_username_find = False
        st.session_state.show_found_usernames = False
        if 'sms_verification' in st.session_state:
            find_phone_val = st.session_state.get('find_username_phone', '')
            if find_phone_val:
                from services.sms_service import SMSService
                sms_service = SMSService()
                sms_service.clear_verification(find_phone_val)
        st.rerun()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
            <div style='text-align: center; padding: 30px 0 20px 0;'>
                <div style='font-size: 60px;'>🔍</div>
                <h1 style='color: #FF69B4; font-size: 28px; margin: 10px 0;'>아이디 찾기</h1>
                <p style='color: #888; font-size: 14px;'>가입 시 등록한 휴대폰번호로 인증하여 아이디를 찾을 수 있습니다</p>
            </div>
        """, unsafe_allow_html=True)
        
        from services.sms_service import SMSService
        sms_service = SMSService()
        
        # 휴대폰번호 입력
        find_phone = st.text_input("휴대폰번호", placeholder="010-1234-5678", key="find_username_phone")
        
        # 발송된 인증번호 표시 (개발 모드)
        find_sent_code_key = f'find_verification_code_{find_phone}' if find_phone else None
        find_sent_code = st.session_state.get(find_sent_code_key) if find_sent_code_key else None
        
        if find_phone and find_sent_code:
            st.markdown(f"""
                <div style='
                    background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%);
                    border: 3px solid #2196F3;
                    border-radius: 12px;
                    padding: 20px;
                    margin: 15px 0;
                    text-align: center;
                    box-shadow: 0 4px 12px rgba(33, 150, 243, 0.3);
                '>
                    <div style='font-size: 16px; color: #1976D2; margin-bottom: 10px; font-weight: bold;'>
                        📱 발송된 인증번호
                    </div>
                    <div style='
                        font-size: 32px;
                        font-weight: bold;
                        color: #0D47A1;
                        letter-spacing: 5px;
                        font-family: "Courier New", monospace;
                        margin: 15px 0;
                        padding: 15px;
                        background: white;
                        border-radius: 8px;
                        border: 2px dashed #2196F3;
                    '>{find_sent_code}</div>
                    <div style='font-size: 12px; color: #666; margin-top: 10px;'>
                        ⚠️ 개발 모드: 실제 SMS는 발송되지 않습니다<br>
                        위 인증번호를 입력란에 입력해주세요
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        # 인증번호 발송 및 확인
        col_phone1, col_phone2 = st.columns([2, 1])
        with col_phone1:
            find_verification_code = st.text_input("인증번호", placeholder="6자리 인증번호 입력", 
                                                  key="find_username_verification_code",
                                                  disabled=not sms_service.is_verified(find_phone) if find_phone else True,
                                                  max_chars=6)
        with col_phone2:
            st.markdown("<br>", unsafe_allow_html=True)
            find_send_clicked = st.button("인증번호\n발송", key="find_send_code_btn", use_container_width=True)
            
            if find_send_clicked:
                if find_phone:
                    result = sms_service.send_verification_code(find_phone)
                    if result['success']:
                        if 'code' in result:
                            st.session_state[find_sent_code_key] = result['code']
                        st.success("✅ 인증번호가 발송되었습니다!")
                        st.rerun()
                    else:
                        st.error(result['message'])
                else:
                    st.warning("휴대폰번호를 먼저 입력해주세요.")
        
        # 인증번호 확인 버튼
        if find_verification_code:
            if st.button("인증번호 확인", key="find_verify_code_btn", use_container_width=True):
                result = sms_service.verify_code(find_phone, find_verification_code)
                if result['success']:
                    st.success("✅ 인증이 완료되었습니다!")
                else:
                    st.error(result['message'])
        
        with st.form("find_username_form"):
            find_submitted = st.form_submit_button("아이디 찾기", use_container_width=True, type="primary")
            
            if find_submitted:
                find_phone_val = st.session_state.get('find_username_phone', '')
                
                if find_phone_val:
                    if sms_service.is_verified(find_phone_val):
                        users = db.get_users_by_phone(find_phone_val)
                        
                        if users:
                            usernames = [u['username'] for u in users]
                            st.session_state.found_usernames = usernames
                            st.success(f"✅ 찾은 아이디: **{', '.join(usernames)}**")
                            st.info("💡 위 아이디로 로그인해주세요.")
                        else:
                            st.error("❌ 해당 휴대폰번호로 등록된 아이디를 찾을 수 없습니다.")
                    else:
                        st.error("❌ 휴대폰 인증을 먼저 완료해주세요.")
                else:
                    st.warning("⚠️ 휴대폰번호를 입력해주세요.")

def show_find_password_page():
    """비밀번호 찾기 페이지"""
    hide_sidebar_navigation()
    
    st.markdown("""
        <style>
        .stApp { background-color: #f9f9f9; }
        </style>
    """, unsafe_allow_html=True)
    
    # 뒤로가기 버튼
    if st.button("← 로그인으로 돌아가기", key="back_to_login_from_find_password"):
        st.session_state.current_auth_screen = 'login'
        st.session_state.show_password_reset = False
        st.session_state.password_reset_verified = False
        st.session_state.verified_user_id = None
        st.session_state.saved_username = ""
        st.session_state.saved_phone = ""
        if 'temp_password' in st.session_state:
            del st.session_state.temp_password
        if 'sms_verification' in st.session_state and 'saved_phone' in st.session_state:
            from services.sms_service import SMSService
            sms_service = SMSService()
            sms_service.clear_verification(st.session_state.saved_phone)
        st.rerun()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
            <div style='text-align: center; padding: 30px 0 20px 0;'>
                <div style='font-size: 60px;'>🔑</div>
                <h1 style='color: #FF69B4; font-size: 28px; margin: 10px 0;'>비밀번호 찾기</h1>
                <p style='color: #888; font-size: 14px;'>아이디와 휴대폰 인증으로 임시 비밀번호를 발급받을 수 있습니다</p>
            </div>
        """, unsafe_allow_html=True)
        
        from services.sms_service import SMSService
        import secrets
        import string
        sms_service = SMSService()
        
        # 1단계: 아이디 입력 및 휴대폰 인증
        if not st.session_state.get('password_reset_verified', False):
            reset_username = st.text_input("아이디", placeholder="비밀번호를 찾을 아이디를 입력하세요", key="reset_password_username")
            reset_phone = st.text_input("휴대폰번호", placeholder="010-1234-5678", key="reset_password_phone")
            
            # 발송된 인증번호 표시
            reset_sent_code_key = f'reset_verification_code_{reset_phone}' if reset_phone else None
            reset_sent_code = st.session_state.get(reset_sent_code_key) if reset_sent_code_key else None
            
            if reset_phone and reset_sent_code:
                st.markdown(f"""
                    <div style='
                        background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%);
                        border: 3px solid #2196F3;
                        border-radius: 12px;
                        padding: 20px;
                        margin: 15px 0;
                        text-align: center;
                        box-shadow: 0 4px 12px rgba(33, 150, 243, 0.3);
                    '>
                        <div style='font-size: 16px; color: #1976D2; margin-bottom: 10px; font-weight: bold;'>
                            📱 발송된 인증번호
                        </div>
                        <div style='
                            font-size: 32px;
                            font-weight: bold;
                            color: #0D47A1;
                            letter-spacing: 5px;
                            font-family: "Courier New", monospace;
                            margin: 15px 0;
                            padding: 15px;
                            background: white;
                            border-radius: 8px;
                            border: 2px dashed #2196F3;
                        '>{reset_sent_code}</div>
                        <div style='font-size: 12px; color: #666; margin-top: 10px;'>
                            ⚠️ 개발 모드: 실제 SMS는 발송되지 않습니다<br>
                            위 인증번호를 입력란에 입력해주세요
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            
            col_phone1, col_phone2 = st.columns([2, 1])
            with col_phone1:
                reset_verification_code = st.text_input("인증번호", placeholder="6자리 인증번호 입력", 
                                                       key="reset_password_verification_code",
                                                       disabled=not sms_service.is_verified(reset_phone) if reset_phone else True,
                                                       max_chars=6)
            with col_phone2:
                st.markdown("<br>", unsafe_allow_html=True)
                reset_send_clicked = st.button("인증번호\n발송", key="reset_send_code_btn", use_container_width=True)
                
                if reset_send_clicked:
                    if reset_phone:
                        result = sms_service.send_verification_code(reset_phone)
                        if result['success']:
                            if 'code' in result:
                                st.session_state[reset_sent_code_key] = result['code']
                            st.success("✅ 인증번호가 발송되었습니다!")
                            st.rerun()
                        else:
                            st.error(result['message'])
                    else:
                        st.warning("휴대폰번호를 먼저 입력해주세요.")
            
            if reset_verification_code:
                if st.button("인증번호 확인", key="reset_verify_code_btn", use_container_width=True):
                    result = sms_service.verify_code(reset_phone, reset_verification_code)
                    if result['success']:
                        st.success("✅ 인증이 완료되었습니다!")
                    else:
                        st.error(result['message'])
            
            with st.form("find_password_form"):
                reset_submitted = st.form_submit_button("본인 확인", use_container_width=True, type="primary")
                
                if reset_submitted:
                    reset_username_val = st.session_state.get('reset_password_username', '')
                    reset_phone_val = st.session_state.get('reset_password_phone', '')
                    
                    if reset_username_val and reset_phone_val:
                        if sms_service.is_verified(reset_phone_val):
                            user = db.get_user_by_username(reset_username_val)
                            phone_clean = reset_phone_val.replace('-', '').replace(' ', '')
                            
                            if user and (user.get('phone_number') == reset_phone_val or user.get('phone_number') == phone_clean):
                                st.session_state.verified_user_id = user['id']
                                st.session_state.saved_username = reset_username_val
                                st.session_state.saved_phone = reset_phone_val
                                st.session_state.password_reset_verified = True
                                st.success("✅ 본인 확인이 완료되었습니다.")
                                st.rerun()
                            else:
                                st.error("❌ 아이디와 휴대폰번호가 일치하지 않습니다.")
                        else:
                            st.error("❌ 휴대폰 인증을 먼저 완료해주세요.")
                    else:
                        st.warning("⚠️ 아이디와 휴대폰번호를 모두 입력해주세요.")
        
        # 2단계: 임시 비밀번호 발급 및 변경
        if st.session_state.get('password_reset_verified', False):
            st.markdown("---")
            st.markdown("### 임시 비밀번호 발급")
            
            if 'temp_password' not in st.session_state:
                temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
                st.session_state.temp_password = temp_password
            
            st.markdown(f"""
                <div style='
                    background: linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%);
                    border: 3px solid #FF9800;
                    border-radius: 12px;
                    padding: 25px;
                    margin: 20px 0;
                    text-align: center;
                '>
                    <div style='font-size: 18px; color: #E65100; margin-bottom: 15px; font-weight: bold;'>
                        🔑 임시 비밀번호
                    </div>
                    <div style='
                        font-size: 36px;
                        font-weight: bold;
                        color: #E65100;
                        letter-spacing: 4px;
                        font-family: "Courier New", monospace;
                        margin: 20px 0;
                        padding: 20px;
                        background: white;
                        border-radius: 10px;
                        border: 3px solid #FF9800;
                    '>{st.session_state.temp_password}</div>
                    <div style='font-size: 13px; color: #666; margin-top: 15px;'>
                        ⚠️ 임시 비밀번호를 안전한 곳에 저장하세요<br>
                        로그인 후 반드시 비밀번호를 변경해주세요
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button("임시 비밀번호로 변경하기", use_container_width=True, type="primary", key="apply_temp_password"):
                if st.session_state.verified_user_id:
                    success = db.update_user_password(st.session_state.verified_user_id, st.session_state.temp_password)
                    if success:
                        st.success("✅ 임시 비밀번호로 변경되었습니다!")
                        st.info(f"**아이디**: `{st.session_state.saved_username}` / **임시 비밀번호**: `{st.session_state.temp_password}`")
                        
                        st.session_state.current_auth_screen = 'login'
                        st.session_state.show_password_reset = False
                        st.session_state.password_reset_verified = False
                        st.session_state.verified_user_id = None
                        st.session_state.saved_username = ""
                        st.session_state.saved_phone = ""
                        if 'temp_password' in st.session_state:
                            del st.session_state.temp_password
                        import time
                        time.sleep(3)
                        st.rerun()
                    else:
                        st.error("❌ 비밀번호 변경에 실패했습니다.")
            
            st.markdown("---")
            st.markdown("### 또는 새 비밀번호로 직접 변경")
            
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
                                        
                                        st.session_state.current_auth_screen = 'login'
                                        st.session_state.show_password_reset = False
                                        st.session_state.password_reset_verified = False
                                        st.session_state.verified_user_id = None
                                        st.session_state.saved_username = ""
                                        st.session_state.saved_phone = ""
                                        if 'temp_password' in st.session_state:
                                            del st.session_state.temp_password
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

def show_signup_page():
    """회원가입 페이지 (로그인 페이지와 동일한 디자인)"""
    hide_sidebar_navigation()
    
    # 세션 상태 초기화
    if 'signup_user_type' not in st.session_state:
        st.session_state['signup_user_type'] = None
    if 'signup_data' not in st.session_state:
        st.session_state['signup_data'] = {}
    
    # 전체 배경 스타일 (로그인 페이지와 동일한 색상 시스템)
    st.markdown("""
        <style>
        .stApp {
            background-color: #F8F9FA;
            font-family: 'Malgun Gothic', '맑은 고딕', 'Apple SD Gothic Neo', sans-serif;
        }
        .signup-container {
            max-width: 400px;
            margin: 0 auto;
            padding: 30px;
            background: white;
            border-radius: 16px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.07);
        }
        .section-title {
            color: #636E72 !important;
            font-size: 16px;
            font-weight: 600;
            margin: 25px 0 15px 0;
        }
        .stTextInput > div > div > input {
            border-radius: 8px;
            border: 1px solid #DFE6E9;
            padding: 12px;
            font-size: 14px;
            transition: all 0.2s;
        }
        .stTextInput > div > div > input:focus {
            border-color: #0984E3 !important;
            box-shadow: 0 0 0 2px rgba(9, 132, 227, 0.1) !important;
        }
        .stNumberInput > div > div > input {
            border-radius: 8px;
            border: 1px solid #DFE6E9;
            padding: 12px;
            font-size: 14px;
            transition: all 0.2s;
        }
        .stNumberInput > div > div > input:focus {
            border-color: #0984E3 !important;
            box-shadow: 0 0 0 2px rgba(9, 132, 227, 0.1) !important;
        }
        .stButton > button[kind="primary"] {
            width: 100% !important;
            background: linear-gradient(135deg, #00B894 0%, #55EFC4 100%) !important;
            color: white !important;
            border-radius: 12px !important;
            height: 50px !important;
            font-weight: 600 !important;
            border: none !important;
            box-shadow: 0 4px 12px rgba(0, 184, 148, 0.3) !important;
            transition: all 0.2s !important;
        }
        .stButton > button[kind="primary"]:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 16px rgba(0, 184, 148, 0.4) !important;
        }
        /* 부모님/아이 선택 버튼 (보라색) */
        button[key="select_parent"],
        button[key="select_child"] {
            height: 70px !important;
            font-size: 16px !important;
            white-space: pre-line !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # 중앙 정렬 컨테이너
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="signup-container">', unsafe_allow_html=True)
        
        # 헤더 (로그인 페이지와 동일)
        st.markdown("""
            <div style='text-align: center; padding: 20px 0;'>
                <div style='font-size: 80px; margin-bottom: 10px;'>🐷</div>
                <h1 style='color: #FF69B4; font-size: 32px; font-weight: 700; margin: 0;'>
                    AI Money Friends
                </h1>
                <p style='color: #B2BEC3; font-size: 14px; margin-top: 8px;'>
                    아이들의 경제 교육 친구
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        # ========== 섹션 1: 기본 정보 ==========
        st.markdown("<div class='section-title'>📋 기본 정보</div>", unsafe_allow_html=True)
        
        signup_username = st.text_input(
            "아이디",
            placeholder="아이디를 입력하세요 (4자 이상)",
            label_visibility="collapsed",
            key="signup_username"
        )
        
        signup_password = st.text_input(
            "비밀번호",
            type="password",
            placeholder="비밀번호를 입력하세요 (6자 이상)",
            label_visibility="collapsed",
            key="signup_password"
        )
        
        signup_password_confirm = st.text_input(
            "비밀번호 확인",
            type="password",
            placeholder="비밀번호를 다시 입력하세요",
            label_visibility="collapsed",
            key="signup_password_confirm"
        )
        
        # ========== 섹션 2: 사용자 유형 ==========
        st.markdown("<div class='section-title'>👨‍👩‍👧 사용자 유형</div>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button(
                "👨‍👩‍👧\n\n부모님",
                key="select_parent",
                use_container_width=True,
                type="primary" if st.session_state.get('signup_user_type') == 'parent' else "secondary"
            ):
                st.session_state['signup_user_type'] = 'parent'
                st.rerun()
        
        with col2:
            if st.button(
                "👶\n\n아이",
                key="select_child",
                use_container_width=True,
                type="primary" if st.session_state.get('signup_user_type') == 'child' else "secondary"
            ):
                st.session_state['signup_user_type'] = 'child'
                st.rerun()
        
        # 선택 상태 표시
        if st.session_state.get('signup_user_type'):
            user_type_text = "부모님" if st.session_state['signup_user_type'] == 'parent' else "아이"
            user_type_icon = "👨‍👩‍👧" if st.session_state['signup_user_type'] == 'parent' else "👶"
            st.info(f"✅ {user_type_icon} {user_type_text}으로 가입합니다")
        
        # ========== 섹션 3: 연락처 (선택) ==========
        st.markdown("<div class='section-title'>📧 연락처 (선택사항)</div>", unsafe_allow_html=True)
        
        signup_email = st.text_input(
            "이메일",
            placeholder="example@email.com (선택)",
            label_visibility="collapsed",
            key="signup_email"
        )
        
        # ========== 섹션 4: 아이 정보 (조건부 표시) ==========
        if st.session_state.get('signup_user_type') == 'child':
            st.markdown("<div class='section-title'>👶 아이 정보</div>", unsafe_allow_html=True)
            
            signup_name = st.text_input(
                "이름",
                placeholder="아이의 이름을 입력하세요",
                label_visibility="collapsed",
                key="signup_name"
            )
            
            signup_age = st.number_input(
                "나이",
                min_value=5,
                max_value=18,
                value=10,
                step=1,
                label_visibility="collapsed",
                key="signup_age"
            )
            
            # 부모 코드 입력 (강조)
            st.markdown("""
                <div style='
                    background: #FFF9E6;
                    border-left: 4px solid #FFD700;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 15px 0;
                '>
                    <strong>🔑 부모님 초대 코드</strong><br>
                    <span style='font-size: 13px; color: #666;'>
                        부모님께 받은 6자리 코드를 입력하세요
                    </span>
                </div>
            """, unsafe_allow_html=True)
            
            signup_parent_code = st.text_input(
                "부모 코드",
                placeholder="예: ABC123",
                max_chars=6,
                label_visibility="collapsed",
                key="signup_parent_code"
            )
        elif st.session_state.get('signup_user_type') == 'parent':
            # 부모인 경우 이름만 입력
            st.markdown("<div class='section-title'>👤 이름</div>", unsafe_allow_html=True)
            signup_name = st.text_input(
                "이름 (닉네임)",
                placeholder="친구들이 부를 이름",
                label_visibility="collapsed",
                key="signup_name"
            )
            signup_age = None
            signup_parent_code = None  # 부모는 자동 생성됨
        else:
            signup_name = None
            signup_age = None
            signup_parent_code = None
        
        # ========== 가입 완료 버튼 ==========
        st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
        
        if st.button("✨ 가입 완료!", use_container_width=True, type="primary"):
            # 유효성 검사
            errors = []
            
            if not signup_username or len(signup_username) < 4:
                errors.append("아이디는 4자 이상이어야 합니다.")
            
            if not signup_password or len(signup_password) < 6:
                errors.append("비밀번호는 6자 이상이어야 합니다.")
            
            if signup_password != signup_password_confirm:
                errors.append("비밀번호가 일치하지 않습니다.")
            
            if not st.session_state.get('signup_user_type'):
                errors.append("사용자 유형을 선택해주세요.")
            
            signup_user_type_value = st.session_state.get('signup_user_type')
            
            if signup_user_type_value == 'child':
                if not signup_name:
                    errors.append("아이의 이름을 입력해주세요.")
                if not signup_parent_code or len(signup_parent_code) != 6:
                    errors.append("올바른 부모 코드를 입력해주세요 (6자리).")
            elif signup_user_type_value == 'parent':
                if not signup_name:
                    errors.append("이름을 입력해주세요.")
            
            if signup_email and '@' not in signup_email:
                errors.append("올바른 이메일 형식이 아닙니다.")
            
            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
            else:
                # 회원가입 처리
                try:
                    # 아이디 중복 확인
                    if db.get_user_by_username(signup_username):
                        st.error("❌ 이미 사용 중인 아이디입니다.")
                    else:
                        # 부모인 경우 부모 코드 자동 생성
                        if signup_user_type_value == 'parent':
                            signup_parent_code = generate_parent_code()
                        
                        # 나이 처리
                        age_value = None
                        if signup_user_type_value == 'child' and signup_age is not None:
                            try:
                                age_value = int(signup_age)
                                if age_value < 5 or age_value > 18:
                                    age_value = None
                            except (ValueError, TypeError):
                                age_value = None
                        
                        # 부모 코드 검증 (아이인 경우)
                        if signup_user_type_value == 'child':
                            if not validate_parent_code(signup_parent_code):
                                st.error("❌ 부모 코드가 올바르지 않습니다.")
                            else:
                                parent_user = db.get_parent_by_code(signup_parent_code)
                                if not parent_user:
                                    st.error("❌ 유효하지 않은 부모 코드입니다.")
                                else:
                                    # 사용자 생성
                                    user_id = db.create_user(
                                        username=signup_username,
                                        password=signup_password,
                                        name=signup_name,
                                        age=age_value,
                                        parent_code=signup_parent_code,
                                        user_type=signup_user_type_value,
                                        parent_ssn=None,
                                        phone_number=None
                                    )
                                    
                                    # 자동 로그인 처리
                                    st.session_state.logged_in = True
                                    st.session_state.user_id = user_id
                                    st.session_state.user_name = signup_name
                                    st.session_state.username = signup_username
                                    st.session_state.user_type = signup_user_type_value
                                    if age_value:
                                        st.session_state.age = age_value
                                    st.session_state.show_login_success = True
                                    
                                    st.success("🎉 회원가입이 완료되었습니다!")
                                    st.balloons()
                                    
                                    import time
                                    time.sleep(1)
                                    st.rerun()
                        else:
                            # 부모인 경우 (부모 코드 자동 생성됨)
                            user_id = db.create_user(
                                username=signup_username,
                                password=signup_password,
                                name=signup_name,
                                age=None,
                                parent_code=signup_parent_code,
                                user_type=signup_user_type_value,
                                parent_ssn=None,
                                phone_number=None
                            )
                            
                            # 자동 로그인 처리
                            st.session_state.logged_in = True
                            st.session_state.user_id = user_id
                            st.session_state.user_name = signup_name
                            st.session_state.username = signup_username
                            st.session_state.user_type = signup_user_type_value
                            st.session_state.show_login_success = True
                            
                            st.success("🎉 회원가입이 완료되었습니다!")
                            st.balloons()
                            
                            import time
                            time.sleep(1)
                            st.rerun()
                except Exception as e:
                    st.error(f"❌ 오류가 발생했습니다: {str(e)}")
        
        # ========== 하단: 로그인 링크 ==========
        st.markdown("""
            <div style='
            text-align: center;
                margin-top: 25px;
                padding: 15px;
                background: #F1F3F5;
                border-radius: 8px;
            '>
                <span style='color: #636E72; font-size: 14px;'>
                    💬 이미 계정이 있으신가요?
                </span><br>
                <span style='color: #FF69B4; font-weight: 600; font-size: 15px; cursor: pointer;'>
                    로그인하기 →
                </span>
            </div>
        """, unsafe_allow_html=True)
        
        # 로그인 페이지로 이동
        if st.button("로그인 페이지로 이동", key="go_to_login", use_container_width=True, type="secondary"):
            st.session_state.current_auth_screen = 'login'
            st.session_state.show_signup = False
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)


def login_page():
    """로그인 페이지 (완전히 새로운 디자인 - 생동감 있고 귀여움)"""
    
    # 화면 전환 확인
    if st.session_state.get('current_auth_screen') == 'signup':
        show_signup_page()
        return
    elif st.session_state.get('current_auth_screen') == 'find_username':
        show_find_username_page()
        return
    elif st.session_state.get('current_auth_screen') == 'find_password':
        show_find_password_page()
        return
    
    # 사이드바 숨기기
    hide_sidebar_navigation()
    
    # 전체 스타일 (수정됨)
    st.markdown("""
        <style>
        /* 전체 배경 */
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            background-attachment: fixed;
        }
        
        /* 메인 컨테이너 */
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
        }
        
        /* 애니메이션 */
        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
        }
        
        .pig-icon {
            animation: bounce 2s infinite;
        }
        
        /* 입력 필드 */
        .stTextInput > div > div > input {
            border: 2px solid #E9ECEF !important;
            border-radius: 12px !important;
            padding: 14px !important;
            font-size: 15px !important;
            background: #F8F9FA !important;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #6C5CE7 !important;
            background: white !important;
            box-shadow: 0 0 0 4px rgba(108, 92, 231, 0.1) !important;
        }
        
        /* 소셜 로그인 버튼 */
        .social-btn {
            display: block;
            width: 100%;
            padding: 16px;
            border: none;
            border-radius: 14px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            margin-bottom: 12px;
            transition: all 0.3s;
            text-align: center;
            text-decoration: none;
        }
        
        .kakao-btn {
            background: linear-gradient(135deg, #FEE500 0%, #FFD600 100%);
            color: #3C1E1E;
            box-shadow: 0 4px 12px rgba(254, 229, 0, 0.4);
        }
        
        .naver-btn {
            background: linear-gradient(135deg, #03C75A 0%, #00B851 100%);
            color: white;
            box-shadow: 0 4px 12px rgba(3, 199, 90, 0.4);
        }
        
        .google-btn {
            background: white;
            color: #2D3436;
            border: 2px solid #E9ECEF;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }
        
        /* 로그인 버튼 */
        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #6C5CE7 0%, #A29BFE 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 14px !important;
            padding: 16px !important;
            font-size: 17px !important;
            font-weight: 700 !important;
            box-shadow: 0 8px 16px rgba(108, 92, 231, 0.3) !important;
        }
        
        /* 카드 */
        .login-card {
            background: white;
            border-radius: 24px;
            padding: 40px 35px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 440px;
            margin: 30px auto;
            position: relative;
            z-index: 10;
        }
        
        /* Streamlit 요소들이 보이게 */
        .stTextInput, .stButton, .stMarkdown {
            position: relative;
            z-index: 11;
        }
        
        /* 섹션 제목 */
        .section-title {
            color: #2D3436;
            font-size: 18px;
            font-weight: 700;
            margin: 30px 0 15px 0;
            text-align: left;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        /* 구분선 */
        .divider {
            text-align: center;
            margin: 30px 0;
            position: relative;
        }
        
        .divider::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 0;
            right: 0;
            height: 1px;
            background: #E9ECEF;
        }
        
        .divider span {
            position: relative;
            background: white;
            padding: 0 15px;
            color: #B2BEC3;
            font-size: 14px;
            font-weight: 600;
        }
        
        /* 모바일 대응 */
        @media (max-width: 768px) {
            .login-card {
                margin: 10px;
                padding: 25px 20px;
                border-radius: 20px;
            }
            .pig-icon {
                font-size: 70px !important;
            }
        }
        </style>
    """, unsafe_allow_html=True)
        
    # 중앙 정렬 컨테이너
    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    
    # 헤더
    st.markdown("""
        <div style='text-align: center; padding: 0 0 30px 0;'>
            <div class='pig-icon' style='font-size: 90px; margin-bottom: 15px;'>🐷</div>
            <h1 style='
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                font-size: 36px;
                font-weight: 800;
                margin: 0;
                letter-spacing: -1px;
            '>
                AI Money Friends
            </h1>
            <p style='color: #636E72; font-size: 15px; margin-top: 10px; font-weight: 500;'>
                아이들의 경제 교육 친구 💰
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # 간편 로그인 섹션
    st.markdown("""
        <div class='section-title'>
            <span style='font-size: 24px;'>✨</span>
            <span>간편 로그인</span>
        </div>
    """, unsafe_allow_html=True)
    
    # OAuth 서비스 초기화
    try:
        from services.oauth_service import OAuthService
        oauth_service = OAuthService()
        
        # 카카오 버튼
        kakao_url = oauth_service.get_kakao_login_url()
        if kakao_url:
            st.markdown(f"""
                <a href="{kakao_url}" target="_self" class="social-btn kakao-btn">
                    <span style='font-size: 28px;'>💬</span>
                    <span>카카오로 3초에 시작하기</span>
                </a>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div class="social-btn kakao-btn" style="opacity: 0.6; cursor: not-allowed;">
                    <span style='font-size: 28px;'>💬</span>
                    <span>카카오로 3초에 시작하기</span>
                </div>
            """, unsafe_allow_html=True)
        
        # 네이버 버튼
        naver_url = oauth_service.get_naver_login_url()
        if naver_url:
            st.markdown(f"""
                <a href="{naver_url}" target="_self" class="social-btn naver-btn">
                    <span style='font-size: 28px;'>N</span>
                    <span>네이버로 시작하기</span>
                </a>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div class="social-btn naver-btn" style="opacity: 0.6; cursor: not-allowed;">
                    <span style='font-size: 28px;'>N</span>
                    <span>네이버로 시작하기</span>
                </div>
            """, unsafe_allow_html=True)
        
        # 구글 버튼
        google_url = oauth_service.get_google_login_url()
        if google_url:
            st.markdown(f"""
                <a href="{google_url}" target="_self" class="social-btn google-btn">
                    <span style='font-size: 28px;'>G</span>
                    <span>구글로 시작하기</span>
                </a>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div class="social-btn google-btn" style="opacity: 0.6; cursor: not-allowed;">
                    <span style='font-size: 28px;'>G</span>
                    <span>구글로 시작하기</span>
                </div>
            """, unsafe_allow_html=True)
    except ImportError:
        st.warning("⚠️ OAuth 서비스를 불러올 수 없습니다. services/oauth_service.py 파일을 확인하세요.")
    
    # 구분선
    st.markdown("""
        <div class='divider'>
            <span>또는</span>
        </div>
    """, unsafe_allow_html=True)
    
    # 아이디로 로그인 섹션
    st.markdown("""
        <div class='section-title'>
            <span style='font-size: 24px;'>🔐</span>
            <span>아이디로 로그인</span>
        </div>
    """, unsafe_allow_html=True)
    
    # 입력 필드 (아이콘 포함)
    col_icon1, col_input1 = st.columns([0.1, 0.9])
    with col_icon1:
        st.markdown("<div style='font-size: 24px; margin-top: 8px;'>👤</div>", unsafe_allow_html=True)
    with col_input1:
        login_username = st.text_input(
            "아이디",
            placeholder="아이디를 입력하세요",
            label_visibility="collapsed",
            key="login_username"
        )
    
    col_icon2, col_input2 = st.columns([0.1, 0.9])
    with col_icon2:
        st.markdown("<div style='font-size: 24px; margin-top: 8px;'>🔒</div>", unsafe_allow_html=True)
    with col_input2:
        login_password = st.text_input(
            "비밀번호",
            type="password",
            placeholder="비밀번호를 입력하세요",
            label_visibility="collapsed",
            key="login_password"
        )
    
    # 사용자 유형 선택 (카드 버튼)
    st.markdown("<div style='margin: 20px 0 15px 0; font-size: 14px; color: #636E72; font-weight: 600;'>로그인 유형을 선택하세요</div>", unsafe_allow_html=True)
    
    # 세션 상태 초기화
    if 'login_user_type' not in st.session_state:
        st.session_state['login_user_type'] = None
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button(
            "👨‍👩‍👧\n\n부모님",
            key="user_type_parent",
            use_container_width=True,
            type="primary" if st.session_state.get('login_user_type') == 'parent' else "secondary"
        ):
            st.session_state['login_user_type'] = 'parent'
    
    with col2:
        if st.button(
            "👶\n\n아이",
            key="user_type_child",
            use_container_width=True,
            type="primary" if st.session_state.get('login_user_type') == 'child' else "secondary"
        ):
            st.session_state['login_user_type'] = 'child'
    
    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
    
    # 로그인 버튼
    if st.button("🚀 로그인하기", use_container_width=True, type="primary", key="login_submit"):
        if login_username and login_password:
            with st.spinner("로그인 중..."):
                user_type_value = st.session_state.get('login_user_type', 'parent')
                user = db.get_user_by_username(login_username)
                
                if user and db.verify_password(login_password, user['password_hash']):
                    if user['user_type'] != user_type_value:
                        type_kr = "부모님" if user['user_type'] == 'parent' else "아이"
                        st.error(f"❌ 이 계정은 **{type_kr}** 계정입니다.")
                    else:
                        # 로그인 성공
                        st.session_state['logged_in'] = True
                        st.session_state['user_id'] = user['id']
                        st.session_state['user_name'] = user['name']
                        st.session_state['username'] = login_username
                        st.session_state['user_type'] = user_type_value
                        st.session_state.show_login_success = True
                        
                        st.success(f"🎉 환영합니다, {user['name']}님!")
                        st.balloons()
                        import time
                        time.sleep(0.5)
                        st.rerun()
                else:
                    st.error("❌ 아이디나 비밀번호가 틀렸습니다.")
        else:
            st.error("❌ 아이디와 비밀번호를 입력하세요.")
    
    # 하단 링크
    st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
            <div style='text-align: center;'>
                <a href='#' style='color: #6C5CE7; text-decoration: none; font-weight: 600; font-size: 14px;'>
                    🔍 아이디 찾기
                </a>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
            <div style='text-align: center;'>
                <a href='#' style='color: #6C5CE7; text-decoration: none; font-weight: 600; font-size: 14px;'>
                    ✏️ 비밀번호 찾기
                </a>
            </div>
        """, unsafe_allow_html=True)
    
    # 실제 버튼 (숨김)
    col_find1, col_find2 = st.columns(2)
    with col_find1:
        if st.button("", key="find_username_hidden"):
            st.session_state.current_auth_screen = 'find_username'
            st.rerun()
    with col_find2:
        if st.button("", key="find_password_hidden"):
            st.session_state.current_auth_screen = 'find_password'
            st.rerun()
    
    # 회원가입 링크
    st.markdown("""
        <div style='
            text-align: center;
            margin-top: 30px;
            padding: 20px;
            background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
            border-radius: 12px;
        '>
            <span style='color: #636E72; font-size: 14px;'>
                💬 아직 계정이 없으신가요?
            </span><br>
            <a href='#' style='
                color: #6C5CE7;
                font-weight: 700;
                font-size: 16px;
                text-decoration: none;
                margin-top: 5px;
                display: inline-block;
            '>
                회원가입하기 →
            </a>
        </div>
    """, unsafe_allow_html=True)
    
    # 회원가입 버튼 (숨김)
    if st.button("", key="go_to_signup_hidden"):
        st.session_state['show_signup'] = True
        st.session_state.current_auth_screen = 'signup'
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)


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
                st.error(f"페이지 이동 중 오류가 발생했습니다: {str(e)}")
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
                        add_to_recent("목표 관리", "pages/9_💵_용돈_관리.py", "💵")
                    except: pass
                    st.switch_page("pages/9_💵_용돈_관리.py")
                else:
                    st.info("목표 관리 페이지가 준비 중입니다. 곧 만나요! 💫")
            except Exception as e:
                st.error(f"페이지 이동 중 오류가 발생했습니다: {str(e)}")
                st.info("목표 관리 페이지가 준비 중입니다. 곧 만나요! 💫")

# 메인 로직
# OAuth 콜백 처리
handle_oauth_callback()

if st.session_state.logged_in:
    main_page()
else:
    login_page()
