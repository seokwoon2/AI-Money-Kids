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
    page_title="홈 | AI 금융교육 서비스",
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
if 'verified_user_id' not in st.session_state:
    st.session_state.verified_user_id = None

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
        </style>
        """, unsafe_allow_html=True)
        st.markdown("### 💰 AI 금융교육 서비스")
        st.markdown("로그인하여 서비스를 이용하세요.")
    
    st.title("💰 AI 금융교육 서비스")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["🔐 로그인", "📝 회원가입"])
    
    with tab1:
        st.subheader("로그인")
        username = st.text_input("사용자명", key="login_username")
        password = st.text_input("비밀번호", type="password", key="login_password")
        
        # 로그인 버튼과 비밀번호 찾기
        if st.button("로그인", type="primary", use_container_width=True):
            if username and password:
                user = db.get_user_by_username(username)
                if user and db.verify_password(password, user['password_hash']):
                    st.session_state.logged_in = True
                    st.session_state.user_id = user['id']
                    st.session_state.user_name = user['name']
                    st.rerun()
                else:
                    st.error("사용자명 또는 비밀번호가 올바르지 않습니다.")
            else:
                st.warning("사용자명과 비밀번호를 입력해주세요.")
        
        # 아이디 찾기 및 비밀번호 찾기 링크
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
        
        # 아이디 찾기 섹션
        if st.session_state.get('show_username_find', False):
            st.markdown("---")
            st.markdown("""
            <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 20px; border-radius: 12px; color: white; margin-bottom: 20px;'>
                <h3 style='color: white; margin-top: 0;'>🔍 아이디 찾기</h3>
                <p style='color: white; opacity: 0.9; margin: 0;'>이름과 부모 코드로 사용자명을 찾을 수 있습니다.</p>
            </div>
            """, unsafe_allow_html=True)
            
            find_name = st.text_input("이름 (닉네임)", key="find_name", placeholder="가입 시 사용한 이름 입력")
            find_parent_code = st.text_input("부모 코드 (8자리)", key="find_parent_code", 
                                            placeholder="회원가입 시 사용한 부모 코드 입력",
                                            help="회원가입 시 사용한 부모 코드를 입력하세요")
            
            col_find_btn1, col_find_btn2 = st.columns(2)
            
            with col_find_btn1:
                if st.button("🔍 아이디 찾기", type="primary", use_container_width=True, key="search_username"):
                    if find_name and find_parent_code:
                        # 부모 코드로 연결된 모든 사용자 찾기 (부모 포함)
                        users = db.get_users_by_parent_code_all(find_parent_code)
                        # 이름으로 필터링
                        matching_users = [u for u in users if u.get('name') == find_name]
                        
                        if matching_users:
                            st.session_state.found_usernames = [u['username'] for u in matching_users]
                            st.session_state.show_found_usernames = True
                        else:
                            st.error("❌ 이름 또는 부모 코드가 일치하는 사용자를 찾을 수 없습니다.")
                    else:
                        st.warning("⚠️ 이름과 부모 코드를 입력해주세요.")
            
            with col_find_btn2:
                if st.button("❌ 취소", use_container_width=True, key="cancel_find_username"):
                    st.session_state.show_username_find = False
                    st.session_state.show_found_usernames = False
                    st.rerun()
            
            # 찾은 아이디 표시
            if st.session_state.get('show_found_usernames', False):
                st.markdown("---")
                st.markdown("""
                <div style='background: #f8f9fa; padding: 20px; border-radius: 12px; 
                            border-left: 4px solid #667eea; margin-bottom: 20px;'>
                    <h3 style='color: #667eea; margin-top: 0;'>✅ 찾은 아이디</h3>
                </div>
                """, unsafe_allow_html=True)
                
                found_usernames = st.session_state.get('found_usernames', [])
                if found_usernames:
                    for idx, username in enumerate(found_usernames):
                        st.markdown(f"""
                        <div style='background: white; padding: 15px; border-radius: 8px; 
                                    margin-bottom: 10px; border: 1px solid #e9ecef;'>
                            <strong style='color: #667eea; font-size: 1.1em;'>사용자명 {idx+1}:</strong>
                            <p style='font-size: 1.2em; margin: 5px 0; color: #262730;'>{username}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.success("✅ 아이디를 찾았습니다! 위의 사용자명으로 로그인하세요.")
                else:
                    st.info("ℹ️ 일치하는 사용자를 찾을 수 없습니다.")
        
        # 비밀번호 찾기 섹션
        if st.session_state.get('show_password_reset', False):
            st.markdown("---")
            st.markdown("""
            <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 20px; border-radius: 12px; color: white; margin-bottom: 20px;'>
                <h3 style='color: white; margin-top: 0;'>🔑 비밀번호 찾기</h3>
                <p style='color: white; opacity: 0.9; margin: 0;'>사용자명과 부모 코드로 본인 확인 후 비밀번호를 재설정할 수 있습니다.</p>
            </div>
            """, unsafe_allow_html=True)
            
            reset_username = st.text_input("사용자명", key="reset_username", placeholder="비밀번호를 찾을 사용자명 입력")
            reset_parent_code = st.text_input("부모 코드 (8자리)", key="reset_parent_code", 
                                             placeholder="회원가입 시 사용한 부모 코드 입력",
                                             help="회원가입 시 사용한 부모 코드를 입력하세요")
            
            col_reset1, col_reset2 = st.columns(2)
            
            with col_reset1:
                if st.button("✅ 본인 확인", type="primary", use_container_width=True, key="verify_identity"):
                    if reset_username and reset_parent_code:
                        user = db.get_user_by_username(reset_username)
                        if user and user.get('parent_code') == reset_parent_code:
                            st.session_state.verified_user_id = user['id']
                            st.session_state.verified_username = reset_username
                            st.success("✅ 본인 확인이 완료되었습니다!")
                        else:
                            st.error("❌ 사용자명 또는 부모 코드가 일치하지 않습니다.")
                    else:
                        st.warning("⚠️ 사용자명과 부모 코드를 입력해주세요.")
            
            with col_reset2:
                if st.button("❌ 취소", use_container_width=True, key="cancel_reset"):
                    st.session_state.show_password_reset = False
                    st.session_state.verified_user_id = None
                    st.rerun()
            
            # 본인 확인 후 비밀번호 재설정
            if st.session_state.get('verified_user_id'):
                st.markdown("---")
                st.markdown("""
                <div style='background: #f8f9fa; padding: 20px; border-radius: 12px; 
                            border-left: 4px solid #667eea; margin-bottom: 20px;'>
                    <h3 style='color: #667eea; margin-top: 0;'>🔐 새 비밀번호 설정</h3>
                    <p style='color: #6c757d; margin: 0;'>새로운 비밀번호를 입력해주세요.</p>
                </div>
                """, unsafe_allow_html=True)
                
                new_password_reset = st.text_input("새 비밀번호", type="password", key="new_password_reset",
                                                   placeholder="새 비밀번호를 입력하세요")
                confirm_password_reset = st.text_input("새 비밀번호 확인", type="password", key="confirm_password_reset",
                                                       placeholder="새 비밀번호를 다시 입력하세요")
                
                if st.button("💾 비밀번호 재설정", type="primary", use_container_width=True, key="reset_password"):
                    if not new_password_reset:
                        st.warning("⚠️ 새 비밀번호를 입력해주세요.")
                    elif new_password_reset != confirm_password_reset:
                        st.error("❌ 새 비밀번호가 일치하지 않습니다.")
                    elif len(new_password_reset) < 4:
                        st.error("❌ 비밀번호는 최소 4자 이상이어야 합니다.")
                    else:
                        user_id = st.session_state.verified_user_id
                        if db.update_user_password(user_id, new_password_reset):
                            st.success("✅ 비밀번호가 재설정되었습니다! 로그인해주세요.")
                            st.session_state.show_password_reset = False
                            st.session_state.verified_user_id = None
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("❌ 비밀번호 재설정에 실패했습니다.")
    
    with tab2:
        st.subheader("회원가입")
        
        # 사용자 타입 선택
        user_type = st.radio(
            "가입 유형 선택",
            ["👨‍👩‍👧 부모로 가입", "👶 아이로 가입"],
            key="signup_user_type",
            horizontal=True
        )
        user_type_value = 'parent' if user_type == "👨‍👩‍👧 부모로 가입" else 'child'
        
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input("사용자명", key="signup_username")
            password = st.text_input("비밀번호", type="password", key="signup_password")
            name = st.text_input("이름 (닉네임)", key="signup_name")
        
        with col2:
            if user_type_value == 'child':
                birth_date = st.date_input(
                    "생년월일",
                    value=date.today().replace(year=date.today().year - 10),
                    min_value=date.today().replace(year=date.today().year - 100),
                    max_value=date.today(),
                    key="signup_birth_date",
                    help="생년월일을 선택하면 만나이가 자동으로 계산됩니다."
                )
                
                # 만나이 계산 및 표시
                calculated_age = calculate_age(birth_date)
                st.info(f"만나이: **{calculated_age}세**")
            else:
                # 부모는 나이 입력 불필요
                birth_date = None
                calculated_age = None
                st.info("부모님은 나이 입력이 필요하지 않습니다.")
            
            if user_type_value == 'parent':
                # 부모는 부모 코드 생성
                if st.button("부모 코드 생성", use_container_width=True, type="primary"):
                    new_code = generate_parent_code()
                    st.session_state.generated_parent_code = new_code
                    st.success(f"생성된 부모 코드: **{new_code}**")
                    st.info("이 코드를 안전한 곳에 저장하세요. 자녀들이 이 코드로 가입할 수 있습니다.")
                
                parent_code = st.text_input(
                    "부모 코드 (8자리)", 
                    value=st.session_state.get('generated_parent_code', ''),
                    key="signup_parent_code",
                    help="위의 '부모 코드 생성' 버튼을 눌러 코드를 생성하세요."
                )
            else:
                # 아이는 부모 코드 입력
                parent_code = st.text_input("부모 코드 (8자리)", key="signup_parent_code", 
                                           help="부모님께 받은 코드를 입력하세요.")
        
        if st.button("회원가입", type="primary", use_container_width=True):
            if not username:
                st.error("사용자명을 입력해주세요.")
            elif not password:
                st.error("비밀번호를 입력해주세요.")
            elif not name:
                st.error("이름을 입력해주세요.")
            elif not parent_code or not validate_parent_code(parent_code):
                st.error("유효한 부모 코드(8자리)를 입력해주세요.")
            else:
                # 만나이 계산 (아이인 경우만)
                age = calculate_age(birth_date) if birth_date else None
                
                # 나이 유효성 검사 (아이인 경우만, 5세 이상)
                if user_type_value == 'child':
                    if age < 5:
                        st.error("만 5세 이상만 가입 가능합니다.")
                        return
                
                try:
                    # 사용자명 중복 확인
                    if db.get_user_by_username(username):
                        st.error("이미 사용 중인 사용자명입니다.")
                    else:
                        user_id = db.create_user(username, password, name, age, parent_code, user_type_value)
                        user_type_kr = "부모" if user_type_value == 'parent' else f"아이 (만 {age}세)"
                        st.success(f"회원가입이 완료되었습니다! ({user_type_kr}) 로그인해주세요.")
                        st.balloons()
                except Exception as e:
                    st.error(f"회원가입 중 오류가 발생했습니다: {str(e)}")

def main_page():
    """로그인 후 메인 페이지 (홈)"""
    # Streamlit 기본 네비게이션 숨기기
    from utils.menu import hide_sidebar_navigation
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
    
    # 사용자 정보 가져오기
    user = db.get_user_by_id(st.session_state.user_id)
    user_type = user.get('user_type', 'child') if user else 'child'
    
    # 사이드바 메뉴 렌더링
    from utils.menu import render_sidebar_menu
    render_sidebar_menu(st.session_state.user_id, st.session_state.user_name, user_type)
    
    # 메인 콘텐츠 영역 - 간단한 환영 메시지만
    st.markdown(f"""
    <div style='text-align: center; padding: 60px 20px;'>
        <h1 style='font-size: 2.5em; margin-bottom: 15px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
            안녕하세요, {st.session_state.user_name}님! 👋
        </h1>
        <p style='font-size: 1.3em; color: #6c757d; margin-bottom: 40px;'>
            AI 금융교육 서비스에 오신 것을 환영합니다
        </p>
        <p style='font-size: 1.1em; color: #868e96;'>
            왼쪽 메뉴에서 원하는 서비스를 선택해주세요
        </p>
    </div>
    """, unsafe_allow_html=True)

# 메인 로직
if st.session_state.logged_in:
    main_page()
else:
    login_page()
