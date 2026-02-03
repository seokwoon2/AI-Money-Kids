import streamlit as st
import time
from datetime import date, datetime
from database.db_manager import DatabaseManager
from utils.auth import generate_parent_code, validate_parent_code
from utils.menu import hide_sidebar_navigation
from services.oauth_service import OAuthService
import re

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

def _signup_page_premium():
    """회원가입 페이지 - 프리미엄 디자인(구버전)"""

    hide_sidebar_navigation()

    # CSS
    st.markdown(
        """
        <style>
            /* 기본 설정 */
            [data-testid="stSidebar"] { display: none !important; }
            header, footer { display: none !important; }

            html, body, [data-testid="stAppViewContainer"]{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            }
            [data-testid="stAppViewContainer"] > .main { background: transparent !important; }

            /* 화면 폭/여백: 모바일에서도 안 깨지게 */
            .main > div { padding: 0 !important; }
            .block-container {
                max-width: 560px !important;
                padding: 18px 14px 28px 14px !important;
            }
            header, footer { display: none !important; }

            /* 진행 단계 표시 */
            .steps-container {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin: 2rem 0;
                padding: 0 1rem;
            }
            .step { flex: 1; text-align: center; position: relative; }
            .step-circle {
                width: 50px; height: 50px; border-radius: 50%;
                background: #E0E0E0; color: #999;
                display: flex; align-items: center; justify-content: center;
                margin: 0 auto 0.5rem;
                font-weight: 700; font-size: 20px;
                transition: all 0.3s;
            }
            .step.active .step-circle {
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: white;
                box-shadow: 0 4px 15px rgba(102,126,234,0.4);
                transform: scale(1.1);
            }
            .step.completed .step-circle { background: #4CAF50; color: white; }
            .step-label { font-size: 13px; color: #666; font-weight: 500; }
            .step.active .step-label { color: #667eea; font-weight: 700; }
            .step-line {
                position: absolute; top: 25px; left: 50%;
                width: 100%; height: 2px;
                background: #E0E0E0; z-index: -1;
            }
            .step.completed .step-line { background: #4CAF50; }

            /* 카드 스타일 */
            /* Streamlit 컨테이너(진짜 래핑)로 카드 구현 */
            div[data-testid="stVerticalBlockBorderWrapper"]{
                background: rgba(255,255,255,0.98) !important;
                border: 1px solid rgba(17,24,39,0.10) !important;
                border-radius: 24px !important;
                box-shadow: 0 25px 60px rgba(0,0,0,0.30) !important;
            }
            div[data-testid="stVerticalBlockBorderWrapper"] > div{
                padding: 26px 22px !important;
                border-radius: 24px !important;
            }
            @keyframes slideUp {
                from { opacity: 0; transform: translateY(30px); }
                to { opacity: 1; transform: translateY(0); }
            }

            /* 사용자 타입 선택 카드(시각적) */
            .user-type-card {
                border: 3px solid #E0E0E0;
                border-radius: 20px;
                padding: 2rem 1.5rem;
                text-align: center;
                transition: all 0.3s;
                background: white;
                position: relative;
                overflow: hidden;
            }
            .user-type-card::before {
                content: '';
                position: absolute; top: 0; left: 0; right: 0; bottom: 0;
                background: linear-gradient(135deg, rgba(102,126,234,0.05), rgba(118,75,162,0.05));
                opacity: 0;
                transition: opacity 0.3s;
            }
            .user-type-card:hover {
                border-color: #667eea;
                transform: translateY(-8px);
                box-shadow: 0 15px 35px rgba(102,126,234,0.3);
            }
            .user-type-card:hover::before { opacity: 1; }
            .user-type-card.selected {
                border-color: #667eea;
                background: linear-gradient(135deg, rgba(102,126,234,0.1), rgba(118,75,162,0.1));
                box-shadow: 0 10px 30px rgba(102,126,234,0.3);
            }
            .user-type-icon { font-size: 72px; margin-bottom: 1rem; display: block; }
            .user-type-title { font-size: 24px; font-weight: 700; color: #2D3436; margin-bottom: 0.5rem; }
            .user-type-desc { font-size: 14px; color: #636E72; }

            /* 입력 필드 */
            .stTextInput input {
                border-radius: 14px !important;
                border: 2px solid #E0E0E0 !important;
                padding: 14px 18px !important;
                font-size: 15px !important;
                transition: all 0.3s !important;
            }
            .stTextInput input:focus {
                border-color: #667eea !important;
                box-shadow: 0 0 0 4px rgba(102,126,234,0.1) !important;
                transform: translateY(-2px) !important;
            }
            .stTextInput > label {
                font-weight: 600 !important;
                color: #2D3436 !important;
                font-size: 15px !important;
                margin-bottom: 0.5rem !important;
            }

            /* 부모 코드 섹션 */
            .parent-code-section {
                background: linear-gradient(135deg, #FFF8E1, #FFECB3);
                border: 3px dashed #FFA726;
                border-radius: 20px;
                padding: 2rem;
                margin: 2rem 0;
                text-align: center;
                animation: pulse 2s infinite;
            }
            @keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.02); } }

            .code-verified {
                background: linear-gradient(135deg, #E8F5E9, #C8E6C9);
                border: 3px solid #4CAF50;
                padding: 1.5rem;
                border-radius: 16px;
                margin: 1rem 0;
                animation: slideIn 0.5s;
            }
            @keyframes slideIn { from { opacity: 0; transform: translateX(-20px); } to { opacity: 1; transform: translateX(0); } }

            /* 버튼 */
            .stButton button {
                border-radius: 14px !important;
                font-weight: 700 !important;
                padding: 14px 28px !important;
                font-size: 16px !important;
                transition: all 0.3s !important;
            }
            .stButton button:hover {
                transform: translateY(-3px) !important;
                box-shadow: 0 10px 25px rgba(0,0,0,0.15) !important;
            }
            button[kind="primary"] {
                background: linear-gradient(135deg, #667eea, #764ba2) !important;
                border: none !important;
                color: white !important;
                box-shadow: 0 8px 20px rgba(102,126,234,0.3) !important;
            }

            /* 섹션 제목 */
            .section-title {
                font-size: 22px;
                font-weight: 700;
                color: #2D3436;
                margin: 18px 0 10px 0;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }
            .section-subtitle {
                font-size: 14px;
                color: #636E72;
                margin: 0 0 14px 0;
            }

            /* 모바일에서 카드 패딩/타이포 살짝 축소 */
            @media (max-width: 480px){
                div[data-testid="stVerticalBlockBorderWrapper"] > div{
                    padding: 22px 16px !important;
                }
                .section-title{ font-size: 20px; }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # 세션 상태 초기화
    if "signup_step" not in st.session_state:
        st.session_state["signup_step"] = 1
    if "signup_user_type" not in st.session_state:
        st.session_state["signup_user_type"] = None

    # 중앙 정렬
    col1, col2, col3 = st.columns([1, 3, 1])

    with col2:
        # 헤더
        st.markdown(
            """
            <div style='text-align:center; margin:2rem 0;'>
                <div style='font-size:80px; margin-bottom:1rem; animation: bounce 2s infinite;'>🐷</div>
                <h1 style='color:white; margin:0; font-size:36px; text-shadow: 0 2px 10px rgba(0,0,0,0.2);'>
                    AI Money Friends
                </h1>
                <p style='color:rgba(255,255,255,0.9); margin:0.5rem 0; font-size:16px;'>
                    아이들의 경제 교육 친구와 함께하세요
                </p>
            </div>

            <style>
                @keyframes bounce {
                    0%, 100% { transform: translateY(0); }
                    50% { transform: translateY(-15px); }
                }
            </style>
            """,
            unsafe_allow_html=True,
        )

        # 진행 단계
        current_step = int(st.session_state.get("signup_step", 1) or 1)
        current_step = 1 if current_step < 1 else (3 if current_step > 3 else current_step)

        st.markdown(
            f"""
            <div class="steps-container">
                <div class="step {'active' if current_step == 1 else ''} {'completed' if current_step > 1 else ''}">
                    <div class="step-circle">{'✓' if current_step > 1 else '1'}</div>
                    <div class="step-label">유형 선택</div>
                    <div class="step-line"></div>
                </div>
                <div class="step {'active' if current_step == 2 else ''} {'completed' if current_step > 2 else ''}">
                    <div class="step-circle">{'✓' if current_step > 2 else '2'}</div>
                    <div class="step-label">정보 입력</div>
                    <div class="step-line"></div>
                </div>
                <div class="step {'active' if current_step == 3 else ''}">
                    <div class="step-circle">3</div>
                    <div class="step-label">완료</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 카드(진짜 컨테이너) 시작
        with st.container(border=True):

            # 공용 입력값(세션)
            name = st.session_state.get("signup_name_value", "")
            username = st.session_state.get("signup_username_value", "")

            # ========== STEP 1: 사용자 유형 선택 ==========
            if current_step == 1:
                st.markdown(
                    """
                    <div class="section-title">👤 사용자 유형을 선택하세요</div>
                    <div class="section-subtitle">부모님과 아이 중 하나를 선택해주세요</div>
                    """,
                    unsafe_allow_html=True,
                )

                type_col1, type_col2 = st.columns(2)
                with type_col1:
                    with st.container(border=True):
                        st.markdown(
                            """
                            <span class="user-type-icon">👨‍👩‍👧</span>
                            <div class="user-type-title">부모님</div>
                            <div class="user-type-desc">
                                자녀의 용돈을 관리하고<br>
                                경제 교육을 도와주세요
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                        if st.button("부모님 선택", key="select_parent", use_container_width=True):
                            st.session_state["signup_user_type"] = "parent"
                            st.session_state["signup_step"] = 2
                            st.rerun()

                with type_col2:
                    with st.container(border=True):
                        st.markdown(
                            """
                            <span class="user-type-icon">👶</span>
                            <div class="user-type-title">아이</div>
                            <div class="user-type-desc">
                                용돈을 관리하고<br>
                                경제를 배워보세요
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                        if st.button("아이 선택", key="select_child", use_container_width=True):
                            st.session_state["signup_user_type"] = "child"
                            st.session_state["signup_step"] = 2
                            st.rerun()

            # ========== STEP 2: 정보 입력 ==========
            elif current_step == 2:
                user_type = st.session_state.get("signup_user_type")
                if user_type not in ("parent", "child"):
                    st.session_state["signup_step"] = 1
                    st.rerun()

                # 선택한 유형 표시
                if user_type == "parent":
                    st.markdown(
                        """
                        <div style='background:linear-gradient(135deg, #667eea, #764ba2);
                                    color:white; padding:1rem; border-radius:16px;
                                    text-align:center; margin-bottom:1.2rem; font-weight:700;
                                    box-shadow: 0 8px 20px rgba(102,126,234,0.25);'>
                            👨‍👩‍👧 부모님으로 가입합니다
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        """
                        <div style='background:linear-gradient(135deg, #FFA726, #FF9800);
                                    color:white; padding:1rem; border-radius:16px;
                                    text-align:center; margin-bottom:1.2rem; font-weight:700;
                                    box-shadow: 0 8px 20px rgba(255,167,38,0.22);'>
                            👶 아이로 가입합니다
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                # 기본 정보
                st.markdown("<div class='section-title'>📝 기본 정보를 입력하세요</div>", unsafe_allow_html=True)

                col_a, col_b = st.columns(2)
                with col_a:
                    name = st.text_input("이름", placeholder="홍길동", key="name_input")
                with col_b:
                    username = st.text_input("아이디", placeholder="gildong123", key="username_input")
                password = st.text_input("비밀번호", type="password", placeholder="6자리 이상", key="pw_input")
                password_confirm = st.text_input("비밀번호 확인", type="password", placeholder="비밀번호 재입력", key="pw_confirm")

                # 세션에 저장(3단계에서 사용)
                st.session_state["signup_name_value"] = name
                st.session_state["signup_username_value"] = username

                # 아이인 경우 부모 코드
                parent_user = None
                parent_code_clean = ""
                if user_type == "child":
                    st.markdown(
                        """
                        <div class="parent-code-section">
                            <div style='font-size:48px; margin-bottom:1rem;'>🔗</div>
                            <div style='font-size:22px; font-weight:700; color:#F57C00; margin-bottom:0.5rem;'>
                                부모님과 연결하기
                            </div>
                            <div style='font-size:15px; color:#666;'>
                                부모님으로부터 받은 초대 코드를 입력하세요
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    parent_code_clean = (
                        st.text_input(
                            "부모 초대 코드",
                            max_chars=8,
                            placeholder="7C825EA9 또는 825EA9",
                            help="8자리 전체 또는 마지막 6자리",
                            key="parent_code",
                        )
                        .upper()
                        .strip()
                    )

                    if parent_code_clean:
                        if validate_parent_code(parent_code_clean):
                            try:
                                parent_user = db.find_parent_by_invite_code(parent_code_clean)
                            except Exception:
                                parent_user = None

                        if parent_user:
                            st.markdown(
                                f"""
                                <div class="code-verified">
                                    <div style='font-size:48px; margin-bottom:1rem;'>✅</div>
                                    <div style='font-size:20px; font-weight:700; color:#2E7D32; margin-bottom:0.5rem;'>
                                        연결 성공!
                                    </div>
                                    <div style='font-size:28px; font-weight:700; color:#2D3436; margin:1rem 0;'>
                                        👨‍👩‍👧 {parent_user.get('name', '부모님')}
                                    </div>
                                    <div style='font-size:14px; color:#666;'>
                                        @{parent_user.get('username', '')}
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                        else:
                            st.error("❌ 올바르지 않은 초대 코드입니다")
                            st.caption("💡 부모님께 정확한 코드를 확인해주세요")

                # 버튼들
                st.markdown("<br>", unsafe_allow_html=True)
                btn_col1, btn_col2 = st.columns([1, 2])
                with btn_col1:
                    if st.button("← 이전", key="btn_prev", use_container_width=True):
                        st.session_state["signup_step"] = 1
                        st.rerun()

                with btn_col2:
                    if st.button("🚀 가입 완료", type="primary", key="btn_complete", use_container_width=True):
                        # 유효성 검사
                        if not name or not username or not password:
                            st.error("⚠️ 모든 항목을 입력해주세요")
                        elif password != password_confirm:
                            st.error("❌ 비밀번호가 일치하지 않습니다")
                        elif len(password) < 6:
                            st.error("⚠️ 비밀번호는 6자리 이상이어야 합니다")
                        elif user_type == "child" and not parent_user:
                            st.error("⚠️ 올바른 부모 초대 코드를 입력해주세요")
                        elif db.get_user_by_username(username):
                            st.error("❌ 이미 사용 중인 아이디입니다")
                        else:
                            try:
                                if user_type == "parent":
                                    new_parent_code = generate_parent_code()
                                    new_user_id = db.create_user(
                                        username=username,
                                        password=password,
                                        name=name,
                                        age=None,
                                        parent_code=new_parent_code,
                                        user_type="parent",
                                        parent_ssn=None,
                                        phone_number=None,
                                    )
                                else:
                                    parent_full_code = (parent_user or {}).get("parent_code") or ""
                                    new_user_id = db.create_user(
                                        username=username,
                                        password=password,
                                        name=name,
                                        age=None,
                                        parent_code=str(parent_full_code).strip().upper(),
                                        user_type="child",
                                        parent_ssn=None,
                                        phone_number=None,
                                    )
                                    # 부모에게 알림(가능하면)
                                    try:
                                        pid = int((parent_user or {}).get("id") or 0)
                                        if pid:
                                            db.create_notification(
                                                pid,
                                                "새 자녀가 연결되었어요 👶",
                                                f"{name}({username}) 계정이 가족에 연결되었습니다.",
                                                level="success",
                                            )
                                    except Exception:
                                        pass

                                st.session_state["signup_step"] = 3
                                st.session_state["new_user_id"] = int(new_user_id)
                                st.session_state["new_user_name"] = name
                                st.session_state["new_username"] = username
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ 오류가 발생했습니다: {str(e)}")

            # ========== STEP 3: 완료 ==========
            else:
                st.markdown(
                    """
                    <div style='text-align:center; padding:2.2rem 0;'>
                        <div style='font-size:90px; margin-bottom:1.6rem; animation: scaleUp 0.5s;'>🎉</div>
                        <div style='font-size:30px; font-weight:800; color:#2D3436; margin-bottom:0.8rem;'>
                            회원가입 완료!
                        </div>
                        <div style='font-size:16px; color:#636E72; margin-bottom:2.2rem;'>
                            AI Money Friends와 함께<br>
                            즐거운 경제 교육을 시작하세요!
                        </div>
                    </div>
                    <style>
                        @keyframes scaleUp { from { transform: scale(0); } to { transform: scale(1); } }
                    </style>
                    """,
                    unsafe_allow_html=True,
                )
                st.balloons()

                if st.button("🏠 시작하기", type="primary", use_container_width=True, key="btn_start"):
                    st.session_state["logged_in"] = True
                    st.session_state["user_id"] = int(st.session_state.get("new_user_id") or 0)
                    st.session_state["user_name"] = st.session_state.get("new_user_name") or ""
                    st.session_state["username"] = st.session_state.get("new_username") or ""
                    st.session_state["user_type"] = st.session_state.get("signup_user_type") or "child"
                    st.session_state["show_login_success"] = True

                    # 세션 정리
                    for k in ["signup_step", "new_user_id", "new_user_name", "new_username", "signup_name_value", "signup_username_value"]:
                        if k in st.session_state:
                            del st.session_state[k]
                    st.session_state["show_signup"] = False
                    st.session_state["current_auth_screen"] = "login"

                    import time
                    time.sleep(0.6)
                    st.rerun()

        # 로그인 링크
        if current_step < 3:
            st.markdown(
                """
                <div style='text-align:center; margin:2rem 0;'>
                    <span style='color:rgba(255,255,255,0.9); font-size:15px;'>
                        이미 계정이 있으신가요?
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("로그인하러 가기", key="goto_login", use_container_width=True):
                st.session_state["show_signup"] = False
                st.session_state["current_auth_screen"] = "login"
                st.session_state["signup_step"] = 1
                st.session_state["signup_user_type"] = None
                for k in ["new_user_id", "new_user_name", "new_username", "signup_name_value", "signup_username_value"]:
                    if k in st.session_state:
                        del st.session_state[k]
                st.rerun()

        # 카드 컨테이너는 with 블록으로 자동 종료됨


def signup_page():
    """회원가입 페이지 - 로그인 페이지와 동일한 스타일(투 컬럼 레이아웃)"""

    hide_sidebar_navigation()

    # ✅ 보기(자동/모바일/PC) - 로그인과 동일한 세션 키 사용
    if "layout_mode" not in st.session_state:
        st.session_state["layout_mode"] = "auto"

    _, view_col = st.columns([0.78, 0.22])
    with view_col:
        current = {"auto": "자동", "mobile": "모바일", "pc": "PC"}.get(st.session_state.get("layout_mode", "auto"), "자동")
        if hasattr(st, "segmented_control"):
            picked = st.segmented_control(
                "보기",
                options=["자동", "모바일", "PC"],
                default=current,
                label_visibility="collapsed",
                key="amf_signup_layout_mode_segmented",
            )
        else:
            picked = st.selectbox(
                "보기",
                options=["자동", "모바일", "PC"],
                index=["자동", "모바일", "PC"].index(current),
                label_visibility="collapsed",
                key="amf_signup_layout_mode_select",
            )

        if picked:
            new_mode = {"자동": "auto", "모바일": "mobile", "PC": "pc"}[picked]
            if new_mode != st.session_state.get("layout_mode", "auto"):
                st.session_state["layout_mode"] = new_mode
                st.rerun()

    # 모드별 너비
    mode = st.session_state.get("layout_mode", "auto")
    if mode == "mobile":
        st.markdown("<style>:root{--signup-maxw:520px;--signup-pad:1rem 0.75rem;}</style>", unsafe_allow_html=True)
    elif mode == "pc":
        st.markdown("<style>:root{--signup-maxw:1100px;--signup-pad:1.25rem 1rem;}</style>", unsafe_allow_html=True)
    else:
        st.markdown(
            "<style>"
            ":root{--signup-maxw:1100px;--signup-pad:1.25rem 1rem;}"
            "@media (max-width: 720px){:root{--signup-maxw:520px;--signup-pad:1rem 0.75rem;}}"
            "</style>",
            unsafe_allow_html=True,
        )

    # CSS (HTML 래핑 없이 Streamlit 컨테이너로 안전하게)
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] { display: none !important; }
            header, footer { display: none !important; }
            html, body, [data-testid="stAppViewContainer"]{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            }
            [data-testid="stAppViewContainer"] > .main { background: transparent !important; }
            .main > div { padding: 0 !important; }
            .block-container{
                padding: var(--signup-pad, 1.1rem 0.75rem) !important;
                max-width: var(--signup-maxw, 520px) !important;
                min-height: 100vh !important;
            }

            /* 작은 화면: 2열 → 1열 */
            @media (max-width: 720px) {
                div[data-testid="stHorizontalBlock"]{ flex-wrap: wrap !important; gap: 0.85rem !important; }
                div[data-testid="stHorizontalBlock"] > div{ flex: 1 1 100% !important; min-width: 100% !important; }
            }

            /* 오른쪽 폼 카드 */
            div[data-testid="stVerticalBlockBorderWrapper"]:has(#signup_card_anchor){
                /* Glass 카드: 보라 배경 위에서도 화이트 폰트가 자연스럽게 */
                background: rgba(255,255,255,0.12) !important;
                border-radius: 22px !important;
                box-shadow: 0 18px 45px rgba(0,0,0,0.28) !important;
                border: 1px solid rgba(255,255,255,0.22) !important;
                overflow: hidden !important;
                backdrop-filter: blur(14px);
            }
            div[data-testid="stVerticalBlockBorderWrapper"]:has(#signup_card_anchor) > div{
                padding: 1.85rem 1.6rem !important;
            }

            /* 카드 내부 텍스트 컬러(화이트 톤) */
            div[data-testid="stVerticalBlockBorderWrapper"]:has(#signup_card_anchor) h1,
            div[data-testid="stVerticalBlockBorderWrapper"]:has(#signup_card_anchor) h2,
            div[data-testid="stVerticalBlockBorderWrapper"]:has(#signup_card_anchor) h3{
                color: rgba(255,255,255,0.96) !important;
                letter-spacing: -0.2px;
            }
            div[data-testid="stVerticalBlockBorderWrapper"]:has(#signup_card_anchor) p,
            div[data-testid="stVerticalBlockBorderWrapper"]:has(#signup_card_anchor) span,
            div[data-testid="stVerticalBlockBorderWrapper"]:has(#signup_card_anchor) label{
                color: rgba(255,255,255,0.88) !important;
            }

            .stTextInput input {
                border-radius: 12px !important;
                border: 2px solid #E0E0E0 !important;
                padding: 12px 16px !important;
                background: rgba(255,255,255,0.92) !important;
                color: #111827 !important; /* ✅ 입력값은 어둡게(가독성) */
            }
            .stTextInput input::placeholder{
                color: rgba(17,24,39,0.45) !important;
            }
            .stTextInput input:focus {
                border-color: #667eea !important;
                box-shadow: 0 0 0 3px rgba(102,126,234,0.12) !important;
            }

            .stButton button { border-radius: 12px !important; font-weight: 800 !important; }
            button[kind="primary"]{
                background: linear-gradient(135deg, #667eea, #764ba2) !important;
                border: none !important;
                color: white !important;
                box-shadow: 0 10px 22px rgba(102,126,234,0.25) !important;
            }

            /* 가입 유형 선택 안내(노란 warning 대신) */
            .amf-type-pill{
                display:flex;
                align-items:center;
                gap:10px;
                padding: 12px 14px;
                border-radius: 14px;
                border: 1px solid rgba(255,255,255,0.18);
                background: rgba(0,0,0,0.10);
                color: rgba(255,255,255,0.94);
                font-weight: 900;
                margin: 0.4rem 0 0.6rem 0;
            }
            .amf-type-pill small{
                margin-left:auto;
                font-weight: 800;
                opacity: 0.85;
            }

            .parent-code-box{
                background: linear-gradient(135deg, rgba(255,193,7,0.10), rgba(255,152,0,0.10));
                border: 2px dashed #FFA726;
                border-radius: 16px;
                padding: 1.2rem;
                margin: 1.2rem 0;
                text-align: center;
            }
            .code-verified{
                background: #E8F5E9;
                border: 2px solid #4CAF50;
                border-radius: 12px;
                padding: 1rem;
                margin: 1rem 0;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if "signup_user_type" not in st.session_state:
        st.session_state["signup_user_type"] = None
    if "signup_character_code" not in st.session_state:
        st.session_state["signup_character_code"] = None
    if "amf_signup_flow_step" not in st.session_state:
        # 1: 시작, 2: 아이/부모 선택, 3: 캐릭터 선택(아이), 4: 정보 입력
        st.session_state["amf_signup_flow_step"] = 1

    def _form():
        # === 온보딩 위자드(스샷처럼 선택 → 시작하기) ===
        def _goto(step: int):
            st.session_state["amf_signup_flow_step"] = int(step)
            st.rerun()

        step = int(st.session_state.get("amf_signup_flow_step") or 1)

        st.markdown(
            """
            <div style='text-align:center;'>
                <div style='font-size:44px; margin-bottom:0.65rem;'>🐷</div>
                <div style='font-size:22px; font-weight:950; color:rgba(255,255,255,0.96); line-height:1.15;'>AI Money Friends</div>
                <div style='color:rgba(255,255,255,0.82); margin:0.45rem 0 0.95rem 0; font-size:13px; font-weight:800;'>아이들의 경제 교육 친구</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 스텝 인디케이터(1~3)
        st.markdown(
            f"""
            <div style="display:flex; gap:10px; justify-content:center; margin: 6px 0 10px 0;">
              <div style="width:10px;height:10px;border-radius:99px;background:{'#fff' if step==1 else 'rgba(255,255,255,0.35)'};"></div>
              <div style="width:10px;height:10px;border-radius:99px;background:{'#fff' if step==2 else 'rgba(255,255,255,0.35)'};"></div>
              <div style="width:10px;height:10px;border-radius:99px;background:{'#fff' if step in (3,4) else 'rgba(255,255,255,0.35)'};"></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        user_type = st.session_state.get("signup_user_type")

        # Step 1: 시작하기
        if step == 1:
            st.markdown(
                """
                <div style="
                    border-radius:20px;
                    padding: 18px 16px;
                    background: rgba(0,0,0,0.12);
                    border: 1px solid rgba(255,255,255,0.18);
                ">
                  <div style="font-weight:950; font-size:18px; color:rgba(255,255,255,0.98);">안녕! 나는 너의 머니프렌즈</div>
                  <div style="margin-top:6px; font-weight:850; font-size:13px; opacity:0.9;">
                    용돈 · 미션 · 저축 목표를 게임처럼 같이 키워보자!
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
            if st.button("시작하기", key="amf_signup_start", use_container_width=True, type="primary"):
                _goto(2)
            if st.button("← 로그인으로 돌아가기", key="signup_back_login_top", use_container_width=True):
                st.session_state["show_signup"] = False
                st.session_state["current_auth_screen"] = "login"
                st.rerun()
            return

        # Step 2: 아이/부모 선택(카드형)
        if step == 2:
            st.markdown("### 누구로 시작할까?")
            st.caption("계정을 만들고, 우리 가족 머니프렌즈를 키워요.")
            a, b = st.columns(2)
            with a:
                st.markdown(
                    """
                    <div style="
                        border-radius:18px; padding:14px 14px 10px 14px;
                        background: rgba(255,255,255,0.10);
                        border: 1px solid rgba(255,255,255,0.22);
                    ">
                      <div style="font-size:22px; font-weight:950; color:rgba(255,255,255,0.96);">아이로 시작</div>
                      <div style="margin-top:6px; font-size:13px; font-weight:850; opacity:0.9;">나만의 머니프렌즈를 키워요</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button("이 친구로 시작하기", key="signup_child_btn", use_container_width=True, type="primary"):
                    st.session_state["signup_user_type"] = "child"
                    _goto(3)
            with b:
                st.markdown(
                    """
                    <div style="
                        border-radius:18px; padding:14px 14px 10px 14px;
                        background: rgba(255,255,255,0.10);
                        border: 1px solid rgba(255,255,255,0.22);
                    ">
                      <div style="font-size:22px; font-weight:950; color:rgba(255,255,255,0.96);">부모로 시작</div>
                      <div style="margin-top:6px; font-size:13px; font-weight:850; opacity:0.9;">아이와 함께 돈습관을 관리해요</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button("이 친구로 시작하기", key="signup_parent_btn", use_container_width=True):
                    st.session_state["signup_user_type"] = "parent"
                    _goto(4)
            st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
            if st.button("← 뒤로", key="amf_signup_back_2", use_container_width=True):
                _goto(1)
            return

        # Step 3: 캐릭터 선택(아이)
        if step == 3:
            st.session_state["signup_user_type"] = "child"
            st.markdown("### 친구를 골라봐!")
            st.caption("선택한 친구가 너의 머니프렌즈가 돼요.")
            try:
                from utils.characters import get_character_catalog, get_character_by_code
            except Exception:
                get_character_catalog = lambda: []  # type: ignore
                get_character_by_code = lambda _c: None  # type: ignore

            selected_code = st.session_state.get("signup_character_code")
            chars = get_character_catalog() or []
            cols = st.columns(3)
            for i, ch in enumerate(chars):
                with cols[i % 3]:
                    is_sel = selected_code == ch.get("code")
                    c1, c2 = (ch.get("colors") or ("#E5E7EB", "#F3F4F6"))[:2]
                    st.markdown(
                        f"""
                        <div style="
                            border-radius:18px;
                            padding:14px 14px 12px 14px;
                            border: 2px solid {'rgba(255,255,255,0.60)' if is_sel else 'rgba(255,255,255,0.18)'};
                            background: linear-gradient(135deg, {c1}, {c2});
                            box-shadow: 0 14px 30px rgba(0,0,0,0.18);
                            color: rgba(17,24,39,0.92);
                            min-height: 140px;
                        ">
                            <div style="font-size:34px; line-height:1;">{ch.get('emoji','🐾')}</div>
                            <div style="font-weight:950; font-size:18px; margin-top:6px;">{ch.get('name','캐릭터')}</div>
                            <div style="font-weight:800; font-size:12px; opacity:0.85;">{ch.get('role','')}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    if st.button(
                        "선택" if not is_sel else "선택됨",
                        use_container_width=True,
                        key=f"pick_char_{ch.get('code')}",
                        type="primary" if is_sel else "secondary",
                    ):
                        st.session_state["signup_character_code"] = ch.get("code")
                        st.rerun()

            picked = get_character_by_code(st.session_state.get("signup_character_code"))
            if picked:
                st.markdown(
                    f'<div class="amf-type-pill">🎮 <b>{picked.get("name")}</b>({picked.get("role")})로 시작해요 <small>선택됨</small></div>',
                    unsafe_allow_html=True,
                )
                st.session_state.setdefault("signup_character_nickname", "")
                nick_default = st.session_state.get("signup_character_nickname") or ""
                character_nickname = st.text_input(
                    "캐릭터 이름(별명)",
                    value=nick_default,
                    placeholder=f"예: {picked.get('name')}짱",
                    key="signup_character_nickname_input",
                )
                st.session_state["signup_character_nickname"] = character_nickname

            # CTA
            disabled = not bool(st.session_state.get("signup_character_code"))
            if st.button(
                "이 친구랑 시작하기",
                key="amf_signup_pick_done",
                use_container_width=True,
                type="primary",
                disabled=disabled,
            ):
                _goto(4)
            if st.button("← 뒤로", key="amf_signup_back_3", use_container_width=True):
                _goto(2)
            return

        # Step 4: 정보 입력(기존 폼)
        if not user_type:
            _goto(2)
            return
        if user_type == "parent":
            st.markdown('<div class="amf-type-pill">👨‍👩‍👧 부모님으로 가입합니다 <small>선택됨</small></div>', unsafe_allow_html=True)
        elif user_type == "child":
            st.markdown('<div class="amf-type-pill">👶 아이로 가입합니다 <small>선택됨</small></div>', unsafe_allow_html=True)
            if st.session_state.get("signup_character_code"):
                if st.button("캐릭터 다시 고르기", key="amf_signup_repick_char", use_container_width=True):
                    _goto(3)
            else:
                if st.button("캐릭터 고르러 가기", key="amf_signup_go_char", use_container_width=True, type="primary"):
                    _goto(3)
                    return

        st.markdown("---")
        st.markdown("### 📝 기본 정보")
        name = st.text_input("이름", placeholder="홍길동", key="signup_name_input")
        birth_date = None
        if user_type == "child":
            # ✅ 아이 회원가입: 생년월일 필수
            birth_date = st.date_input(
                "생년월일",
                value=None,
                min_value=date(1900, 1, 1),
                max_value=date.today(),
                key="signup_birth_date_input",
            )
        username = st.text_input("아이디", placeholder="gildong123", key="signup_username_input")
        password = st.text_input("비밀번호", type="password", placeholder="6자리 이상", key="signup_pw_input")
        password_confirm = st.text_input("비밀번호 확인", type="password", placeholder="비밀번호 재입력", key="signup_pw_confirm_input")

        parent_user = None
        if user_type == "child":
            st.markdown("---")
            st.markdown(
                """
                <div class="parent-code-box">
                    <div style="font-size: 36px;">🔗</div>
                    <div style="font-weight: 900; font-size: 17px; color: #F57C00; margin: 0.5rem 0;">
                        부모님과 연결하기
                    </div>
                    <div style="font-size: 13px; color: #666;">
                        부모님의 초대 코드를 입력하거나 QR을 업로드하세요
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # MF-XXXX 키패드 입력
            st.markdown("#### 🔢 코드 입력(MF-XXXX)")
            if "signup_invite_digits" not in st.session_state:
                st.session_state["signup_invite_digits"] = ""
            digits = str(st.session_state.get("signup_invite_digits") or "")
            code_preview = f"MF-{digits.ljust(4, '_')}"
            st.code(code_preview, language=None)

            grid = [
                ["1", "2", "3"],
                ["4", "5", "6"],
                ["7", "8", "9"],
                ["C", "0", "←"],
            ]
            for r_i, row in enumerate(grid):
                cols = st.columns(3)
                for c_i, keycap in enumerate(row):
                    with cols[c_i]:
                        if st.button(keycap, use_container_width=True, key=f"invite_key_{r_i}_{c_i}"):
                            if keycap == "C":
                                digits = ""
                            elif keycap == "←":
                                digits = digits[:-1]
                            else:
                                if len(digits) < 4 and keycap.isdigit():
                                    digits = digits + keycap
                            st.session_state["signup_invite_digits"] = digits
                            st.rerun()

            parent_code = f"MF-{digits}" if len(digits) == 4 else ""

            # QR 업로드(옵션): 외부 API로 decode
            with st.expander("📷 QR 업로드로 입력(옵션)", expanded=False):
                up = st.file_uploader("QR 이미지 업로드", type=["png", "jpg", "jpeg"], key="signup_qr_upload")
                if up is not None:
                    try:
                        import requests

                        resp = requests.post(
                            "https://api.qrserver.com/v1/read-qr-code/",
                            files={"file": (up.name, up.getvalue(), up.type or "application/octet-stream")},
                            timeout=15,
                        )
                        data = resp.json()
                        txt = ""
                        try:
                            txt = (data[0].get("symbol") or [{}])[0].get("data") or ""
                        except Exception:
                            txt = ""
                        m = re.search(r"MF-\d{4}", str(txt).upper())
                        if m:
                            digits = m.group(0).split("-")[1]
                            st.session_state["signup_invite_digits"] = digits
                            st.success(f"인식됨: {m.group(0)}")
                            st.rerun()
                        else:
                            st.info("QR에서 MF-XXXX 코드를 찾지 못했어요. 다른 이미지로 시도해보세요.")
                    except Exception:
                        st.info("QR 인식에 실패했어요. 키패드로 입력해주세요.")

            # 기존 호환: 6/8자리 코드 입력(선택)
            legacy = st.text_input(
                "기존 코드(호환용, 6~8자리)",
                placeholder="예: 7C825EA9 또는 825EA9",
                key="signup_parent_code_legacy",
            ).upper().strip()

            parent_user = None
            invite_record = None
            if parent_code:
                try:
                    if hasattr(db, "verify_invite_code"):
                        vr = db.verify_invite_code(parent_code)
                        if vr:
                            invite_record = (vr or {}).get("invite")
                            parent_user = (vr or {}).get("parent")
                except Exception:
                    parent_user = None

            if not parent_user and legacy:
                if validate_parent_code(legacy):
                    try:
                        parent_user = db.find_parent_by_invite_code(legacy)
                    except Exception:
                        parent_user = None

            if parent_user:
                exp = ""
                if invite_record and invite_record.get("expires_at"):
                    exp = f" (만료: {invite_record.get('expires_at')})"
                st.markdown(
                    f"""
                    <div class="code-verified">
                        <div style="text-align: center;">
                            <div style="font-size: 32px;">✅</div>
                            <div style="font-weight: 900; margin: 0.5rem 0;">
                                {parent_user.get('name', '부모님')}과 연결됩니다!{exp}
                            </div>
                            <div style="font-size: 14px; color: #666;">
                                @{parent_user.get('username', '')}
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            elif parent_code or legacy:
                st.error("❌ 올바르지 않은 초대 코드입니다")

        st.markdown("---")
        if st.button("🚀 가입하기", type="primary", use_container_width=True, key="signup_submit_btn"):
            if not name or not username or not password:
                st.error("⚠️ 모든 항목을 입력해주세요")
            elif user_type == "child" and not birth_date:
                st.error("⚠️ 생년월일을 입력해주세요")
            elif user_type == "child" and not st.session_state.get("signup_character_code"):
                st.error("⚠️ 캐릭터를 선택해주세요")
            elif password != password_confirm:
                st.error("❌ 비밀번호가 일치하지 않습니다")
            elif len(password) < 6:
                st.error("⚠️ 비밀번호는 6자리 이상이어야 합니다")
            elif user_type == "child" and not parent_user:
                st.error("⚠️ 올바른 부모 초대 코드를 입력해주세요")
            elif db.get_user_by_username(username):
                st.error("❌ 이미 사용 중인 아이디입니다")
            else:
                try:
                    # 나이 계산(기존 age 컬럼 호환)
                    computed_age = None
                    birth_date_str = None
                    if birth_date:
                        birth_date_str = birth_date.isoformat()
                        today = date.today()
                        computed_age = today.year - birth_date.year - (
                            (today.month, today.day) < (birth_date.month, birth_date.day)
                        )
                    if user_type == "parent":
                        new_parent_code = generate_parent_code()
                        new_user_id = db.create_user(
                            username=username,
                            password=password,
                            name=name,
                            age=computed_age,
                            parent_code=new_parent_code,
                            user_type="parent",
                            parent_ssn=None,
                            phone_number=None,
                            birth_date=birth_date_str,
                            character_code=None,
                        )
                    else:
                        parent_full_code = (parent_user or {}).get("parent_code") or ""
                        # 기본 스킨은 캐릭터에 맞춰 자동 지정
                        skin_code = None
                        if st.session_state.get("signup_character_code"):
                            skin_code = f"{st.session_state.get('signup_character_code')}:default"
                        nickname = (st.session_state.get("signup_character_nickname") or "").strip()
                        if not nickname:
                            try:
                                from utils.characters import get_character_by_code
                                cc = get_character_by_code(st.session_state.get("signup_character_code"))
                                nickname = (cc or {}).get("name") or "내 캐릭터"
                            except Exception:
                                nickname = "내 캐릭터"
                        new_user_id = db.create_user(
                            username=username,
                            password=password,
                            name=name,
                            age=computed_age,
                            parent_code=str(parent_full_code).strip().upper(),
                            user_type="child",
                            parent_ssn=None,
                            phone_number=None,
                            birth_date=birth_date_str,
                            character_code=st.session_state.get("signup_character_code"),
                            character_nickname=nickname,
                            character_skin_code=skin_code,
                        )
                        # 기본 스킨 해금 + 첫 보상 지급 체크(레벨1)
                        try:
                            if hasattr(db, "unlock_skin") and skin_code:
                                db.unlock_skin(int(new_user_id), skin_code)
                            if hasattr(db, "grant_level_rewards_if_needed"):
                                db.grant_level_rewards_if_needed(int(new_user_id))
                        except Exception:
                            pass
                        # ✅ 초대코드 1회 사용 처리(MF-XXXX)
                        try:
                            if parent_code and hasattr(db, "consume_invite_code"):
                                db.consume_invite_code(parent_code, int(new_user_id))
                        except Exception:
                            pass
                        # ✅ 첫 미션 도착 메시지(스토리보드)
                        try:
                            db.create_notification(
                                int(new_user_id),
                                "첫 미션이 도착했어요! 🎁",
                                "홈에서 오늘의 미션을 확인해볼까요?",
                                level="success",
                            )
                            # 오늘 미션 바로 배정(가능한 경우)
                            if hasattr(db, "assign_daily_missions_if_needed"):
                                db.assign_daily_missions_if_needed(int(new_user_id), date.today().isoformat())
                        except Exception:
                            pass
                        try:
                            pid = int((parent_user or {}).get("id") or 0)
                            if pid:
                                db.create_notification(
                                    pid,
                                    "새 자녀가 연결되었어요 👶",
                                    f"{name}({username}) 계정이 가족에 연결되었습니다.",
                                    level="success",
                                )
                        except Exception:
                            pass

                    st.success("✅ 회원가입이 완료되었습니다!")
                    st.balloons()
                    st.session_state["logged_in"] = True
                    st.session_state["user_id"] = int(new_user_id)
                    st.session_state["user_name"] = name
                    st.session_state["username"] = username
                    st.session_state["user_type"] = user_type
                    st.session_state["show_signup"] = False
                    st.session_state["current_auth_screen"] = "login"
                    st.session_state["show_login_success"] = True
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 오류가 발생했습니다: {str(e)}")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("← 로그인으로 돌아가기", key="signup_back_login", use_container_width=True):
            st.session_state["show_signup"] = False
            st.session_state["current_auth_screen"] = "login"
            st.rerun()

    if mode in ("pc", "auto"):
        left, right = st.columns([1.05, 0.95], vertical_alignment="top")
        with left:
            st.markdown(
                """
                <div style='color:white; padding: 10px 6px 2px 6px;'>
                    <div style='font-size:64px; line-height:1; margin: 10px 0 10px 0;'>🐷</div>
                    <div style='font-size:34px; font-weight:950; letter-spacing:-0.5px; text-shadow: 0 2px 10px rgba(0,0,0,0.18);'>
                        AI Money Friends
                    </div>
                    <div style='margin-top:8px; font-size:15px; font-weight:800; opacity:0.95;'>
                        아이들의 경제 교육 친구
                    </div>
                    <div style='margin-top:16px; font-size:14px; font-weight:800; opacity:0.92; line-height:1.6;'>
                        ✅ 용돈 관리 · ✅ 미션 · ✅ 저축 목표 · ✅ 리포트<br>
                        가족과 함께 돈 습관을 만들어봐요.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with right:
            with st.container(border=True):
                st.markdown('<div id="signup_card_anchor"></div>', unsafe_allow_html=True)
                _form()
    else:
        with st.container(border=True):
            st.markdown('<div id="signup_card_anchor"></div>', unsafe_allow_html=True)
            _form()


def show_signup_page():
    """회원가입 페이지(호환 래퍼)"""
    signup_page()


def login_page():
    """로그인 페이지 - 단순 깔끔 버전"""

    # 화면 전환 (구버전 플래그 + current_auth_screen 둘 다 지원)
    if st.session_state.get("current_auth_screen") == "signup" or st.session_state.get("show_signup", False):
        show_signup_page()
        return
    if st.session_state.get("current_auth_screen") == "find_username" or st.session_state.get("show_find_username", False):
        show_find_username_page()
        return
    if st.session_state.get("current_auth_screen") == "find_password" or st.session_state.get("show_find_password", False):
        show_find_password_page()
        return

    # ✅ 로그인 페이지에서도 보기(자동/모바일/PC) 제공
    if "layout_mode" not in st.session_state:
        st.session_state["layout_mode"] = "auto"
    layout_mode = st.session_state.get("layout_mode", "auto")

    top_spacer, top_view = st.columns([0.78, 0.22])
    with top_view:
        current = {"auto": "자동", "mobile": "모바일", "pc": "PC"}.get(layout_mode, "자동")
        if hasattr(st, "segmented_control"):
            picked = st.segmented_control(
                "보기",
                options=["자동", "모바일", "PC"],
                default=current,
                label_visibility="collapsed",
                key="amf_login_layout_mode_segmented",
            )
        else:
            picked = st.selectbox(
                "보기",
                options=["자동", "모바일", "PC"],
                index=["자동", "모바일", "PC"].index(current),
                label_visibility="collapsed",
                key="amf_login_layout_mode_select",
            )

        if picked:
            new_mode = {"자동": "auto", "모바일": "mobile", "PC": "pc"}[picked]
            if new_mode != st.session_state.get("layout_mode", "auto"):
                st.session_state["layout_mode"] = new_mode
                st.rerun()

    # 로그인 페이지 레이아웃 변수(모드별)
    layout_mode = st.session_state.get("layout_mode", "auto")
    if layout_mode == "mobile":
        st.markdown("<style>:root{--login-maxw:520px;--login-pad:1rem 0.75rem;}</style>", unsafe_allow_html=True)
    elif layout_mode == "pc":
        st.markdown("<style>:root{--login-maxw:980px;--login-pad:1.25rem 1rem;}</style>", unsafe_allow_html=True)
    else:
        # auto: 큰 화면은 PC 톤, 작은 화면은 모바일 톤으로 자동
        st.markdown(
            "<style>"
            ":root{--login-maxw:980px;--login-pad:1.25rem 1rem;}"
            "@media (max-width: 720px){:root{--login-maxw:520px;--login-pad:1rem 0.75rem;}}"
            "</style>",
            unsafe_allow_html=True,
        )

    # CSS (최소 + 트렌디 정리)
    st.markdown(
        """
        <style>
            /* 배경을 최상단 컨테이너까지 통일 (상/하단 보라색 테두리/틈 방지) */
            html, body, [data-testid="stAppViewContainer"] {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            }
            [data-testid="stAppViewContainer"] > .main { background: transparent !important; }

            /* 사이드바 제거 */
            [data-testid="stSidebar"] { display: none !important; }

            /* 헤더/푸터 제거 */
            header, footer { display: none !important; }

            /* Streamlit 여백/폭 정리 (스크롤 최소화) */
            .main > div { padding: 0 !important; }
            .block-container {
                padding: var(--login-pad, 1.1rem 0.75rem) !important;
                max-width: var(--login-maxw, 520px) !important;
                min-height: 100vh !important;
                display: flex !important;
                flex-direction: column !important;
                justify-content: flex-start !important; /* 상단 정렬(모바일에서 자연스러움) */
            }

            /* PC 레이아웃(2열)도 모바일에서는 자연스럽게 1열로 */
            @media (max-width: 720px) {
                div[data-testid="stHorizontalBlock"]{
                    flex-wrap: wrap !important;
                    gap: 0.85rem !important;
                }
                div[data-testid="stHorizontalBlock"] > div{
                    flex: 1 1 100% !important;
                    min-width: 100% !important;
                }
            }

            /* 입력 필드 */
            .stTextInput input {
                border-radius: 12px !important;
                border: 1.5px solid #E0E0E0 !important;
                padding: 12px 14px !important;
            }
            .stTextInput input:focus {
                border-color: #667eea !important;
                box-shadow: 0 0 0 3px rgba(102,126,234,0.12) !important;
            }

            /* 버튼 */
            .stButton button { border-radius: 12px !important; font-weight: 800 !important; }

            /* Primary 버튼 */
            .stButton > button[kind="primary"],
            button[kind="primary"],
            button[data-testid="baseButton-primary"] {
                background: linear-gradient(135deg, #667eea, #764ba2) !important;
                border: none !important;
                color: white !important;
                box-shadow: 0 10px 22px rgba(102,126,234,0.25) !important;
            }
            .stButton > button[kind="primary"]:hover,
            button[kind="primary"]:hover,
            button[data-testid="baseButton-primary"]:hover {
                transform: translateY(-1px);
                box-shadow: 0 14px 28px rgba(102,126,234,0.32) !important;
            }

            /* 카드: form 자체를 카드로 */
            /* 카드: login_card_anchor가 있는 "border wrapper"만 카드로 (PC 2열에서 전체가 덮이는 문제 방지) */
            div[data-testid="stVerticalBlockBorderWrapper"]:has(#login_card_anchor){
                background: white !important;
                border-radius: 22px !important;
                box-shadow: 0 18px 45px rgba(0,0,0,0.28) !important;
                border: 1px solid rgba(17,24,39,0.08) !important;
                overflow: hidden !important;
            }
            div[data-testid="stVerticalBlockBorderWrapper"]:has(#login_card_anchor) > div{
                padding: 1.75rem 1.5rem !important;
            }

            /* 탭(요즘 느낌: pill) */
            .stTabs [data-baseweb="tab-list"] {
                gap: 8px;
                background: #f3f4f6;
                border-radius: 14px;
                padding: 6px;
            }
            .stTabs [data-baseweb="tab"] {
                border-radius: 12px;
                padding: 10px 12px;
                font-weight: 800;
                color: #374151;
            }
            .stTabs [aria-selected="true"] {
                background: white;
                box-shadow: 0 6px 14px rgba(0,0,0,0.08);
                color: #111827;
            }

            /* 선택 배지(부모/아이) */
            .login-hint {
                margin: 0.75rem 0 0.65rem 0;
                padding: 10px 12px;
                border-radius: 12px;
                font-weight: 900;
                text-align: center;
                color: #111827;
                background: linear-gradient(135deg, rgba(102,126,234,0.12), rgba(118,75,162,0.12));
                border: 1px solid rgba(102,126,234,0.18);
            }

            /* 소셜 버튼 내부 점(•) 같은 브라우저 기본 스타일 방지 */
            button { -webkit-appearance: none; appearance: none; }

            /* 모바일: 패딩만 조정(모드 전환을 막지 않도록 max-width 강제는 제거) */
            @media (max-width: 520px) {
                .block-container { padding: 1rem 0.75rem !important; }
                div[data-testid="stVerticalBlockBorderWrapper"]:has(#login_card_anchor) > div { padding: 1.4rem 1.1rem !important; }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # OAuth URL 준비 (기존 방식 유지)
    kakao_url = None
    naver_url = None
    google_url = None
    try:
        oauth_service = get_oauth_service()
        kakao_url = getattr(oauth_service, "get_kakao_login_url", lambda: None)()
        naver_url = getattr(oauth_service, "get_naver_login_url", lambda: None)()
        google_url = getattr(oauth_service, "get_google_login_url", lambda: None)()
    except Exception:
        pass

    # ====== 레이아웃에 따라 실제 UI 구조 변경 ======
    # mobile: 1열(현재 톤)
    # pc/auto: 2열(브랜딩 패널 + 로그인 카드) → 모바일 폭에서는 자동으로 1열로 래핑
    is_desktop_layout = st.session_state.get("layout_mode") in ("pc", "auto")

    if is_desktop_layout:
        left, right = st.columns([1.05, 0.95], vertical_alignment="top")
        with left:
            st.markdown(
                """
                <div style='color:white; padding: 10px 6px 2px 6px;'>
                    <div style='font-size:64px; line-height:1; margin: 10px 0 10px 0;'>🐷</div>
                    <div style='font-size:34px; font-weight:950; letter-spacing:-0.5px; text-shadow: 0 2px 10px rgba(0,0,0,0.18);'>
                        AI Money Friends
                    </div>
                    <div style='margin-top:8px; font-size:15px; font-weight:800; opacity:0.95;'>
                        아이들의 경제 교육 친구
                    </div>
                    <div style='margin-top:16px; font-size:14px; font-weight:800; opacity:0.92; line-height:1.6;'>
                        ✅ 용돈 관리 · ✅ 미션 · ✅ 저축 목표 · ✅ 리포트<br>
                        가족과 함께 돈 습관을 만들어봐요.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with right:
            # 카드 내용: 컨테이너로 "진짜 래핑" (PC에서 카드 CSS 범위가 커지는 문제 방지)
            with st.container(border=True):
                st.markdown('<div id="login_card_anchor"></div>', unsafe_allow_html=True)
                st.markdown(
                    """
                    <div style='text-align:center;'>
                        <div style='font-size:44px; margin-bottom:0.65rem;'>🐷</div>
                        <div style='font-size:22px; font-weight:900; color:#2D3436; line-height:1.15;'>AI Money Friends</div>
                        <div style='color:#636E72; margin:0.45rem 0 0.95rem 0; font-size:13px;'>아이들의 경제 교육 친구</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                tab_social, tab_id = st.tabs(["✨ 간편 로그인", "📝 아이디 로그인"])
    else:
        # 모바일 톤: 기존 1열 레이아웃
        with st.container(border=True):
            st.markdown('<div id="login_card_anchor"></div>', unsafe_allow_html=True)
            st.markdown(
                """
                <div style='text-align:center;'>
                    <div style='font-size:58px; margin-bottom:0.75rem;'>🐷</div>
                    <div style='font-size:26px; font-weight:900; color:#2D3436; line-height:1.15;'>AI Money Friends</div>
                    <div style='color:#636E72; margin:0.5rem 0 1.1rem 0; font-size:14px;'>아이들의 경제 교육 친구</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            tab_social, tab_id = st.tabs(["✨ 간편 로그인", "📝 아이디 로그인"])

    with tab_social:
        # 소셜 버튼은 줄바꿈을 줄여 스크롤 최소화 + '점/불릿' 느낌 제거
        def _social_btn(url, bg, fg, border, label):
            common = (
                "width:100%; padding:12px 14px; border-radius:12px; font-weight:900; "
                "cursor:pointer; margin-bottom:10px; font-size:14px; "
                "outline:none; display:flex; align-items:center; justify-content:center; gap:8px;"
            )
            if url and url != "#":
                st.markdown(
                    f"""
                    <a href="{url}" target="_self" style="text-decoration:none; display:block;">
                        <button style="{common} background:{bg}; color:{fg}; border:{border};">
                            {label}
                        </button>
                    </a>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"""
                    <button disabled style="{common} background:{bg}; color:{fg}; border:{border}; opacity:0.55;">
                        {label} <span style="font-weight:800;">(준비중)</span>
                    </button>
                    """,
                    unsafe_allow_html=True,
                )

        _social_btn(kakao_url, "#FEE500", "#000", "none", "🟡 카카오로 시작하기")
        _social_btn(naver_url, "#03C75A", "white", "none", "🟢 네이버로 시작하기")
        _social_btn(google_url, "white", "#5F6368", "1.5px solid #E0E0E0", "🔴 구글로 시작하기")

        st.caption("아이디/비밀번호 로그인은 ‘아이디 로그인’ 탭에서 진행하세요.")

    with tab_id:
        username = st.text_input("ID", placeholder="아이디를 입력하세요", key="login_username", label_visibility="collapsed")
        password = st.text_input("PW", type="password", placeholder="비밀번호를 입력하세요", key="login_password", label_visibility="collapsed")

        # 로그인 버튼(간결/요즘 앱 톤: 🚀)
        if st.button("🚀 로그인하기", key="do_login_btn", use_container_width=True, type="primary"):
            if not username or not password:
                st.error("⚠️ 아이디와 비밀번호를 입력하세요")
            else:
                user = db.get_user_by_username(username)
                if user and db.verify_password(password, user["password_hash"]):
                    # ✅ 사용자 유형은 DB에서 자동 판별
                    inferred_type = user.get("user_type") or "child"
                    st.session_state["logged_in"] = True
                    st.session_state["user_id"] = user["id"]
                    st.session_state["user_name"] = user["name"]
                    st.session_state["username"] = username
                    st.session_state["user_type"] = inferred_type
                    st.session_state.show_login_success = True

                    st.success("✅ 로그인 성공!")
                    st.balloons()
                    import time

                    time.sleep(0.9)
                    st.rerun()
                else:
                    st.error("❌ 아이디 또는 비밀번호가 틀렸습니다")

        # 도움 링크는 접어서 한 화면에 다 안 나오게
        with st.expander("도움이 필요해요", expanded=False):
            ca, cb = st.columns(2)
            with ca:
                if st.button("🔍 아이디 찾기", key="go_find_id_btn", use_container_width=True):
                    st.session_state["show_find_username"] = True
                    st.session_state.current_auth_screen = "find_username"
                    st.rerun()
            with cb:
                if st.button("🔑 비밀번호 찾기", key="go_find_pw_btn", use_container_width=True):
                    st.session_state["show_find_password"] = True
                    st.session_state.current_auth_screen = "find_password"
                    st.rerun()

            if st.button("📝 회원가입하기", key="go_signup_btn", use_container_width=True):
                st.session_state["show_signup"] = True
                st.session_state.current_auth_screen = "signup"
                st.rerun()


def main_page():
    """로그인 후 홈으로 이동(새 구조 통일)"""
    # 이제 로그인 후 첫 화면은 `pages/1_🏠_대시보드.py`(홈)로 통일합니다.
    # (페이지 누락/라우팅 이슈가 있어도 앱이 죽지 않도록 예외 처리)
    try:
        st.switch_page("pages/1_🏠_대시보드.py")
    except Exception:
        st.session_state["logged_in"] = False
        st.session_state["current_auth_screen"] = "login"
        st.rerun()

def parent_dashboard(user_name):
    """부모용 홈 - Style B (전문적인 분석형)"""
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
    /* 부모 홈 전용 스타일 */
    .main { background-color: #f0f2f6 !important; }
    .stApp {
        background: #f0f2f6 !important;
    }
    .parent-header { padding: 10px 0 14px 0; margin-bottom: 14px; display:flex; align-items:flex-end; justify-content:space-between; gap:12px; }
    .parent-header h1 { font-size: 26px; font-weight: 900; color: #111827; margin:0; letter-spacing:-0.3px; }
    .parent-sub { font-size: 13px; color:#6b7280; font-weight:800; margin-top:6px; }
    .parent-chip { background: rgba(255,255,255,0.85); border: 1px solid rgba(17,24,39,0.08); border-radius: 999px; padding: 6px 10px; font-size: 12px; font-weight: 900; color:#374151; }

    /* 카드 공통: 섹션 간격 통일 */
    .parent-card { background-color: white; border-radius: 22px; padding: 22px; box-shadow: 0 16px 30px rgba(17,24,39,0.08); height: 100%; border: 1px solid rgba(17,24,39,0.06); margin-bottom: 16px; }
    .card-label { font-size: 16px; font-weight: 900; color: #111827; margin-bottom: 16px; display: flex; align-items: center; gap: 10px; }
    .child-item { display: flex; align-items: center; padding: 12px 0; border-bottom: 1px solid #f7fafc; }
    .child-avatar { width: 45px; height: 45px; background-color: #edf2ff; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 20px; margin-right: 15px; }
    .child-info { flex: 1; }
    .child-name { font-weight: 900; color: #111827; }
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

    today_str = datetime.now().strftime("%Y.%m.%d")
    st.markdown(
        f"""
        <div class="parent-header">
            <div>
                <h1>안녕하세요, {user_name}님 👋</h1>
                <div class="parent-sub">오늘도 우리 가족의 금융 습관을 한눈에 확인해요</div>
            </div>
            <div class="parent-chip">📅 {today_str}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

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
    """아이용 홈 - Style A (친근하고 귀여운 카드형)"""
    st.markdown("""
    <style>
    /* 아이 홈 전용 스타일 */
    .main { background-color: #fcfdfe !important; }
    .stApp {
        background: #fcfdfe !important;
    }
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

    # NOTE: 호칭(“~아/야”)은 어색하다는 피드백이 있어 제거하고 중립 문구로 표시
    st.markdown(
        f'<div class="dashboard-header"><div class="mascot-piggy">🐷</div><div class="welcome-msg"><h1>안녕하세요, {user_name}! 👋</h1><p style="font-size: 17px; color: #555; font-weight: 600; margin-top:5px;">오늘도 재미있게 돈 공부 해볼까? ✨</p></div></div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""<div class="dash-card card-mint"><div class="card-title">💰 내 저축함</div><div class="badge-label" style="background:#fff385; color:#7F6000; position:absolute; top:25px; right:25px;">저축왕 진행 중! 👑</div><div style="margin-top:20px;"><div class="card-subtitle">저축왕 성취도 (75%)</div><div class="progress-bar-bg"><div class="progress-bar-fill" style="width: 75%;"></div></div><h2 style="margin:5px 0; font-size: 34px; font-weight:900;">45,000원</h2><p style="margin:0; font-size:14px; font-weight:700; opacity:0.8;">🌱 목표: 60,000원</p></div><div class="card-mascot">🍯</div></div>""", unsafe_allow_html=True)
        # (구버전 child_dashboard) 새 페이지 구조로 이동
        if st.button("거래 기록 보기 📋", key="main_history", use_container_width=True):
            try:
                st.switch_page("pages/3_💵_용돈_관리.py")
            except Exception as e:
                st.error(f"페이지 이동 중 오류가 발생했습니다: {str(e)}")
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""<div class="dash-card card-coral"><div class="card-title">❓ 오늘의 퀴즈</div><p style="font-size: 18px; font-weight:700; margin-top:20px;">매일매일 지식이 쑥쑥!</p><div class="badge-label" style="margin-top:5px;">새로운 미션 도착! ✨</div><div class="card-mascot">❓</div></div>""", unsafe_allow_html=True)
        if st.button("지금 도전! 🚀", key="main_quiz", use_container_width=True):
            try:
                st.switch_page("pages/10_✅_미션.py")
            except Exception as e:
                st.error(f"페이지 이동 중 오류가 발생했습니다: {str(e)}")

    with col2:
        st.markdown("""<div class="dash-card card-yellow"><div class="card-title">📖 오늘의 학습</div><div class="badge-label" style="background:#C5B4E3; color:#3D2B66; position:absolute; top:25px; right:25px;">꿈꾸기 가이드 📖</div><div style="margin-top:20px;"><div class="card-subtitle">오늘의 목표 (40%)</div><div class="progress-bar-bg"><div class="progress-bar-fill" style="width: 40%;"></div></div><p style="margin:0; font-weight:700; font-size:16px;">3/5 완료</p><p style="margin:5px 0 0 0; font-size:14px; opacity:0.8;">꿈을 이루는 저축법 배우기</p></div><div class="card-mascot">🤖</div></div>""", unsafe_allow_html=True)
        if st.button("학습 계속하기 📚", key="main_study", use_container_width=True):
            try:
                st.switch_page("pages/12_📚_경제_교실.py")
            except Exception as e:
                st.error(f"페이지 이동 중 오류가 발생했습니다: {str(e)}")
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""<div class="dash-card card-lavender"><div class="card-title">🎯 나의 목표</div><div style="margin-top:20px;"><div class="card-subtitle">자전거 사기 (10%)</div><div class="progress-bar-bg"><div class="progress-bar-fill" style="width: 10%;"></div></div><p style="margin:0; font-weight:700; font-size:16px;">"새 자전거 사기" 🚲</p><p style="margin:5px 0 0 0; font-size:14px; font-weight:700;">남은 금액: 54,000원</p></div><div class="card-mascot">🎯</div></div>""", unsafe_allow_html=True)
        if st.button("목표 관리하기 🧸", key="main_goal", use_container_width=True):
            try:
                st.switch_page("pages/8_🎯_저축_목표.py")
            except Exception as e:
                st.error(f"페이지 이동 중 오류가 발생했습니다: {str(e)}")

# 메인 로직
# OAuth 콜백 처리
handle_oauth_callback()

if st.session_state.get("logged_in", False):
    main_page()
else:
    login_page()
