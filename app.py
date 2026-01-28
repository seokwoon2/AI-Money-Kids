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
            padding: 40px 0 20px 0;
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
        # JavaScript로 localStorage 값을 읽어와서 쿠키에 저장 (매번 실행)
        st.markdown("""
        <script>
        (function() {
            try {
                const savedUsername = localStorage.getItem('saved_username');
                const rememberUsername = localStorage.getItem('remember_username') === 'true';
                const autoLogin = localStorage.getItem('auto_login') === 'true';
                
                // 쿠키에 저장하여 Python에서 읽을 수 있도록
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
        
        # 쿠키에서 localStorage 값 읽기 (매번 실행)
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
            pass  # 쿠키 읽기 실패 시 무시
        
        # 저장된 아이디가 있으면 자동으로 채우기
        saved_username_value = st.session_state.get('saved_username', '')
        
        # 로그인 실패 후 입력값이 있으면 그것을 사용, 없으면 저장된 아이디 사용
        if st.session_state.get('login_username_value'):
            initial_username = st.session_state.get('login_username_value', '')
        else:
            initial_username = saved_username_value
        
        # 폼을 사용하여 엔터 키로 제출 가능하도록
        with st.form("login_form", clear_on_submit=False):
            # 입력값이 세션 상태에 있으면 사용, 없으면 초기값 사용
            form_username = st.text_input("사용자명", key="login_username_form", value=initial_username)
            form_password = st.text_input("비밀번호", type="password", key="login_password_form", value="")
            
            # 아이디 저장 및 자동 로그인 옵션
            # localStorage에서 값을 읽어와서 초기값으로 설정
            col_check1, col_check2 = st.columns(2)
            with col_check1:
                # localStorage에서 값을 읽어와서 초기값 설정
                remember_default = st.session_state.get('remember_username', False)
                remember_username = st.checkbox("💾 아이디 저장", value=remember_default, key="remember_username_check",
                                               help="아이디를 저장하여 다음 방문 시 자동으로 입력됩니다")
            with col_check2:
                auto_default = st.session_state.get('auto_login', False)
                auto_login = st.checkbox("🚀 자동 로그인", value=auto_default, key="auto_login_check", 
                                        help="아이디 저장 시 자동으로 입력됩니다 (비밀번호는 입력 필요)")
            
            # localStorage에서 값을 읽어와서 입력 필드와 체크박스에 직접 설정 (JavaScript)
            # 더 강력한 방법으로 체크박스와 입력 필드 설정
            st.markdown("""
            <script>
            (function() {
                let synced = false;
                let attempts = 0;
                const maxAttempts = 30; // 최대 15초 동안 시도
                
                function syncLocalStorage() {
                    if (synced) return; // 이미 동기화되었으면 중단
                    attempts++;
                    
                    try {
                        const savedUsername = localStorage.getItem('saved_username');
                        const rememberUsername = localStorage.getItem('remember_username') === 'true';
                        const autoLogin = localStorage.getItem('auto_login') === 'true';
                        
                        let usernameInput = null;
                        let rememberCheckbox = null;
                        let autoLoginCheckbox = null;
                        
                        // 사용자명 입력 필드 찾기 (여러 방법 시도)
                        usernameInput = document.querySelector('input[data-testid*="login_username_form"]');
                        if (!usernameInput) {
                            const inputs = document.querySelectorAll('input[type="text"]');
                            inputs.forEach(function(input) {
                                const label = input.closest('[data-testid*="stTextInput"]') || input.closest('.stTextInput');
                                if (label && (label.textContent.includes('사용자명') || label.textContent.includes('사용자'))) {
                                    usernameInput = input;
                                }
                            });
                        }
                        
                        // 아이디 저장 체크박스 찾기
                        rememberCheckbox = document.querySelector('input[data-testid*="remember_username_check"]');
                        if (!rememberCheckbox) {
                            const checkboxes = document.querySelectorAll('input[type="checkbox"]');
                            checkboxes.forEach(function(cb) {
                                const label = cb.closest('[data-testid*="stCheckbox"]') || cb.closest('.stCheckbox');
                                if (label && label.textContent.includes('아이디 저장')) {
                                    rememberCheckbox = cb;
                                }
                            });
                        }
                        
                        // 자동 로그인 체크박스 찾기
                        autoLoginCheckbox = document.querySelector('input[data-testid*="auto_login_check"]');
                        if (!autoLoginCheckbox) {
                            const checkboxes = document.querySelectorAll('input[type="checkbox"]');
                            checkboxes.forEach(function(cb) {
                                const label = cb.closest('[data-testid*="stCheckbox"]') || cb.closest('.stCheckbox');
                                if (label && label.textContent.includes('자동 로그인')) {
                                    autoLoginCheckbox = cb;
                                }
                            });
                        }
                        
                        // 사용자명 입력 필드 설정
                        if (usernameInput && savedUsername) {
                            if (usernameInput.value !== savedUsername) {
                                usernameInput.value = savedUsername;
                                // 모든 가능한 이벤트 트리거
                                ['input', 'change', 'blur', 'keyup', 'keydown'].forEach(function(eventType) {
                                    usernameInput.dispatchEvent(new Event(eventType, { bubbles: true, cancelable: true }));
                                });
                                // InputEvent도 트리거
                                try {
                                    usernameInput.dispatchEvent(new InputEvent('input', { bubbles: true, cancelable: true, data: savedUsername }));
                                } catch(e) {}
                            }
                        }
                        
                        // 아이디 저장 체크박스 설정
                        if (rememberCheckbox) {
                            const shouldBeChecked = rememberUsername;
                            if (rememberCheckbox.checked !== shouldBeChecked) {
                                // 체크박스 상태 직접 설정
                                rememberCheckbox.checked = shouldBeChecked;
                                // 모든 가능한 이벤트 트리거
                                ['change', 'input', 'click', 'focus', 'blur'].forEach(function(eventType) {
                                    rememberCheckbox.dispatchEvent(new Event(eventType, { bubbles: true, cancelable: true }));
                                });
                                // 실제 클릭 이벤트도 시뮬레이션
                                if (shouldBeChecked && !rememberCheckbox.checked) {
                                    rememberCheckbox.click();
                                }
                            }
                        }
                        
                        // 자동 로그인 체크박스 설정
                        if (autoLoginCheckbox) {
                            const shouldBeChecked = autoLogin;
                            if (autoLoginCheckbox.checked !== shouldBeChecked) {
                                // 체크박스 상태 직접 설정
                                autoLoginCheckbox.checked = shouldBeChecked;
                                // 모든 가능한 이벤트 트리거
                                ['change', 'input', 'click', 'focus', 'blur'].forEach(function(eventType) {
                                    autoLoginCheckbox.dispatchEvent(new Event(eventType, { bubbles: true, cancelable: true }));
                                });
                                // 실제 클릭 이벤트도 시뮬레이션
                                if (shouldBeChecked && !autoLoginCheckbox.checked) {
                                    autoLoginCheckbox.click();
                                }
                            }
                        }
                        
                        // 모든 요소를 찾았고 설정했으면 성공
                        if ((!savedUsername || usernameInput) && rememberCheckbox && autoLoginCheckbox) {
                            synced = true;
                            return true;
                        }
                    } catch(e) {
                        console.error('localStorage 동기화 오류:', e);
                    }
                    
                    // 최대 시도 횟수에 도달하지 않았으면 계속 시도
                    if (attempts < maxAttempts) {
                        setTimeout(syncLocalStorage, 500);
                    }
                    return false;
                }
                
                // MutationObserver를 사용하여 DOM 변경 감지
                const observer = new MutationObserver(function(mutations) {
                    if (!synced) {
                        syncLocalStorage();
                    }
                });
                
                // 문서 전체를 관찰
                observer.observe(document.body, {
                    childList: true,
                    subtree: true,
                    attributes: true,
                    attributeFilter: ['data-testid', 'class']
                });
                
                // 즉시 실행 및 여러 시점에서 재시도
                setTimeout(syncLocalStorage, 50);
                setTimeout(syncLocalStorage, 200);
                setTimeout(syncLocalStorage, 500);
                setTimeout(syncLocalStorage, 1000);
                setTimeout(syncLocalStorage, 2000);
                setTimeout(syncLocalStorage, 3000);
                
                // Streamlit이 완전히 렌더링된 후에도 실행
                if (document.readyState === 'loading') {
                    document.addEventListener('DOMContentLoaded', function() {
                        setTimeout(syncLocalStorage, 100);
                        setTimeout(syncLocalStorage, 500);
                    });
                }
                window.addEventListener('load', function() {
                    setTimeout(syncLocalStorage, 100);
                    setTimeout(syncLocalStorage, 500);
                });
                
                // Streamlit의 rerun 후에도 실행
                window.addEventListener('streamlit:rerun', function() {
                    synced = false;
                    attempts = 0;
                    setTimeout(syncLocalStorage, 100);
                });
            })();
            </script>
            """, unsafe_allow_html=True)
            
            # 로그인 버튼 (폼 내부에서 제출 버튼 역할)
            login_clicked = st.form_submit_button("로그인", type="primary", use_container_width=True)
        
        if login_clicked:
            # 폼에서 입력받은 값을 사용
            username = form_username
            password = form_password
            # 입력값 검증
            if not username:
                st.warning("⚠️ 사용자명을 입력해주세요.")
            elif not password:
                st.warning("⚠️ 비밀번호를 입력해주세요.")
            else:
                # 입력값 저장 (실패 시 유지용)
                st.session_state.login_username_value = username
                
                # 사용자 인증
                user = db.get_user_by_username(username)
                if user and db.verify_password(password, user['password_hash']):
                    # 로그인 유형 일치 확인
                    if user['user_type'] != login_type_value:
                        type_kr = "부모님" if user['user_type'] == 'parent' else "아이"
                        st.error(f"❌ 이 계정은 **{type_kr}** 계정입니다. 로그인 유형을 확인해주세요.")
                    else:
                        # 로그인 성공 - 모든 상태를 먼저 설정
                        st.session_state.logged_in = True
                        st.session_state.user_id = user['id']
                        st.session_state.user_name = user['name']
                        st.session_state.show_login_success = True
                        st.session_state.login_username_value = ""
                        
                        # 아이디 저장 설정
                    if remember_username:
                        st.session_state.saved_username = username
                        st.session_state.remember_username = True
                        # localStorage 저장
                        st.markdown(f"""
                        <script>
                        try {{
                            localStorage.setItem('saved_username', '{username}');
                            localStorage.setItem('remember_username', 'true');
                        }} catch(e) {{}}
                        </script>
                        """, unsafe_allow_html=True)
                    else:
                        st.session_state.saved_username = ""
                        st.session_state.remember_username = False
                        st.markdown("""
                        <script>
                        try {
                            localStorage.removeItem('saved_username');
                            localStorage.removeItem('remember_username');
                        } catch(e) {}
                        </script>
                        """, unsafe_allow_html=True)
                    
                    # 자동 로그인 설정
                    st.session_state.auto_login = auto_login
                    if auto_login:
                        st.markdown("""
                        <script>
                        try {
                            localStorage.setItem('auto_login', 'true');
                        } catch(e) {}
                        </script>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <script>
                        try {
                            localStorage.removeItem('auto_login');
                        } catch(e) {}
                        </script>
                        """, unsafe_allow_html=True)
                    
                    # 즉시 페이지 전환
                    st.rerun()
                else:
                    # 로그인 실패
                    st.error("❌ 사용자명 또는 비밀번호가 올바르지 않습니다.")
                    st.session_state.login_username_value = username  # 사용자명 유지
        
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
            
            find_name = st.text_input("이름 (닉네임)", key="find_name", placeholder="가입 시 사용한 이름 입력", value=st.session_state.get('find_name_input', ''))
            find_parent_code = st.text_input("부모 코드 (8자리)", key="find_parent_code", 
                                            placeholder="회원가입 시 사용한 부모 코드 입력",
                                            help="회원가입 시 사용한 부모 코드를 입력하세요",
                                            value=st.session_state.get('find_parent_code_input', ''))
            
            col_find_btn1, col_find_btn2 = st.columns(2)
            
            with col_find_btn1:
                search_clicked = st.button("🔍 아이디 찾기", type="primary", use_container_width=True, key="search_username")
            
            with col_find_btn2:
                if st.button("❌ 취소", use_container_width=True, key="cancel_find_username"):
                    st.session_state.show_username_find = False
                    st.session_state.show_found_usernames = False
                    st.session_state.find_name_input = ""
                    st.session_state.find_parent_code_input = ""
                    st.rerun()
            
            # 버튼 클릭 시 처리
            if search_clicked:
                # 입력값 저장
                st.session_state.find_name_input = find_name
                st.session_state.find_parent_code_input = find_parent_code
                
                # 입력값 검증 (공백 제거)
                find_name_clean = find_name.strip() if find_name else ""
                find_parent_code_clean = find_parent_code.strip().upper() if find_parent_code else ""
                
                if find_name_clean and find_parent_code_clean:
                    # 부모 코드로 연결된 모든 사용자 찾기 (부모 포함)
                    users = db.get_users_by_parent_code_all(find_parent_code_clean)
                    
                    # 디버깅 정보 (개발용)
                    # st.info(f"디버깅: 부모코드 '{find_parent_code_clean}'로 {len(users)}명의 사용자를 찾았습니다.")
                    
                    # 이름으로 필터링
                    matching_users = [u for u in users if u.get('name', '').strip() == find_name_clean]
                    
                    if matching_users:
                        st.session_state.found_usernames = [u['username'] for u in matching_users]
                        st.session_state.show_found_usernames = True
                        st.rerun()
                    else:
                        st.error("❌ 이름 또는 부모 코드가 일치하는 사용자를 찾을 수 없습니다.")
                        if users:
                            st.info(f"💡 부모 코드 '{find_parent_code_clean}'로는 다음 사용자들이 등록되어 있습니다: {', '.join([u.get('name', '') for u in users])}")
                        else:
                            st.info(f"💡 부모 코드 '{find_parent_code_clean}'로 등록된 사용자가 없습니다.")
                else:
                    if not find_name_clean:
                        st.warning("⚠️ 이름을 입력해주세요.")
                    if not find_parent_code_clean:
                        st.warning("⚠️ 부모 코드를 입력해주세요.")
            
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
                # 부모 코드 생성 버튼
                if st.button("🔑 부모 코드 생성", use_container_width=True, type="primary"):
                    new_code = generate_parent_code()
                    st.session_state.generated_parent_code = new_code
                    # 입력란 key인 'signup_parent_code'에 직접 값을 할당 (이게 가장 확실함)
                    st.session_state['signup_parent_code'] = new_code
                    st.session_state.code_generated = True
                    st.rerun()
                
                # 생성된 코드 표시 (코드가 있을 때만)
                if st.session_state.get('generated_parent_code'):
                    generated_code = st.session_state.generated_parent_code
                    st.markdown(f"""
                    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                padding: 20px; border-radius: 12px; color: white; margin: 15px 0; text-align: center;'>
                        <h4 style='color: white; margin: 0 0 10px 0;'>✅ 생성된 부모 코드</h4>
                        <div style='font-size: 2em; font-weight: bold; margin: 10px 0; font-family: monospace; letter-spacing: 3px;'>
                            {generated_code}
                        </div>
                        <div style='display: flex; justify-content: center; gap: 10px;'>
                            <button id='copy-btn-{generated_code}'
                                    style='background: rgba(255,255,255,0.2); border: 1px solid white; color: white; 
                                           padding: 8px 20px; border-radius: 8px; cursor: pointer; font-weight: bold;'>
                                📋 클립보드에 복사
                            </button>
                        </div>
                        <p style='font-size: 0.9em; margin-top: 10px; opacity: 0.9;'>
                            ✨ 코드가 아래 입력란에 자동으로 입력되었습니다.
                        </p>
                    </div>
                    <script>
                    (function() {{
                        const btn = document.getElementById('copy-btn-{generated_code}');
                        if (!btn) return;
                        btn.onclick = function() {{
                            const text = '{generated_code}';
                            if (navigator.clipboard && navigator.clipboard.writeText) {{
                                navigator.clipboard.writeText(text).then(() => alert("복사 완료: " + text))
                                .catch(() => fallbackCopy(text));
                            }} else {{
                                fallbackCopy(text);
                            }}
                        }};
                        function fallbackCopy(text) {{
                            const ta = document.createElement("textarea");
                            ta.value = text;
                            ta.style.position = "fixed";
                            ta.style.opacity = "0";
                            document.body.appendChild(ta);
                            ta.select();
                            try {{ document.execCommand("copy"); alert("복사 완료: " + text); }}
                            catch (e) {{ console.error(e); }}
                            document.body.removeChild(ta);
                        }}
                    }})();</script>""", unsafe_allow_html=True)

                # 부모 코드 입력란 (key를 'signup_parent_code'로 설정하여 세션 상태와 직접 연동)
                parent_code = st.text_input(
                    "부모 코드 (8자리)", 
                    key="signup_parent_code",
                    help="부모 코드 생성 버튼을 누르면 자동으로 채워집니다."
                )
            else:
                # 아이는 부모 코드 직접 입력
                parent_code = st.text_input(
                    "부모 코드 (8자리)", 
                    key="signup_parent_code", 
                    help="부모님께 받은 코드를 입력하세요."
                )
        
        if st.button("회원가입", type="primary", use_container_width=True):
            # parent_code는 st.text_input의 반환값인 위 변수를 그대로 사용
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
                        
                        # 회원가입 성공 후 자동 로그인 처리
                        st.session_state.logged_in = True
                        st.session_state.user_id = user_id
                        st.session_state.user_name = name
                        st.session_state.show_login_success = True
                        
                        # 성공 메시지 및 축하
                        st.success(f"✅ 회원가입이 완료되었습니다! ({user_type_kr}) 자동으로 로그인되었습니다.")
                        st.balloons()
                        
                        # 페이지 새로고침하여 메인 페이지로 이동
                        st.rerun()
                except Exception as e:
                    st.error(f"회원가입 중 오류가 발생했습니다: {str(e)}")

def main_page():
    """로그인 후 메인 대시보드 페이지 - 스타일 A 컨셉"""
    from utils.menu import render_sidebar_menu, hide_sidebar_navigation
    hide_sidebar_navigation()
    
    user = db.get_user_by_id(st.session_state.user_id)
    user_type = user.get('user_type', 'child') if user else 'child'
    render_sidebar_menu(st.session_state.user_id, st.session_state.user_name, user_type)
    
    # 스타일 A 전용 CSS
    st.markdown("""
    <style>
    /* 메인 배경색 */
    .main {
        background-color: #fcfdfe !important;
    }
    
    /* 상단 헤더 */
    .dashboard-header {
        display: flex;
        align-items: center;
        gap: 20px;
        margin-bottom: 40px;
        padding: 20px 0;
    }
    .mascot-piggy {
        font-size: 80px;
        animation: swing 3s ease-in-out infinite;
    }
    @keyframes swing {
        0%, 100% { transform: rotate(-5deg); }
        50% { transform: rotate(5deg); }
    }
    .welcome-msg h1 {
        font-size: 38px;
        font-weight: 900;
        color: #1a202c;
        margin: 0;
    }
    
    /* 카드 그리드 - 반응형 (모바일 1열, 데스크탑 2열) */
    .card-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 25px;
    }
    
    /* 공통 카드 스타일 */
    .dash-card {
        border-radius: 35px;
        padding: 25px;
        position: relative;
        overflow: hidden;
        min-height: 200px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.05);
        border: 4px solid white;
        transition: all 0.3s ease;
        margin-bottom: 20px;
    }
    .dash-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 15px 30px rgba(0,0,0,0.1);
    }
    .card-title {
        font-size: 22px;
        font-weight: 800;
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 10px;
    }
    .card-subtitle {
        font-size: 14px;
        font-weight: 600;
        opacity: 0.8;
        margin-bottom: 5px;
    }
    
    /* 카드별 배경색 */
    .card-mint { background-color: #C1F0D5; color: #1E4D2B; }
    .card-yellow { background-color: #FFE5A5; color: #7F6000; }
    .card-coral { background-color: #FFB3B3; color: #661A1A; }
    .card-lavender { background-color: #D9D1F2; color: #3D2B66; }
    
    /* 게이미피케이션 요소 */
    .progress-bar-bg {
        background: rgba(255,255,255,0.4);
        border-radius: 15px;
        height: 14px;
        margin: 12px 0;
        position: relative;
    }
    .progress-bar-fill {
        background: currentColor;
        height: 100%;
        border-radius: 15px;
        transition: width 1s ease-in-out;
    }
    .progress-text {
        font-size: 13px;
        font-weight: 700;
        text-align: right;
        margin-bottom: 15px;
    }
    .badge-label {
        background: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
        display: inline-block;
    }
    
    /* 마스코트 */
    .card-mascot {
        position: absolute;
        right: 15px;
        bottom: 10px;
        font-size: 60px;
        opacity: 0.9;
    }

    /* 모바일 대응: 화면이 작아지면 1열로 */
    @media (max-width: 768px) {
        .dashboard-header {
            flex-direction: column;
            text-align: center;
        }
        .card-grid {
            grid-template-columns: 1fr;
        }
    }
    </style>
    """, unsafe_allow_html=True)

    # 1. 헤더
    st.markdown(f"""
    <div class="dashboard-header">
        <div class="mascot-piggy">🐷</div>
        <div class="welcome-msg">
            <h1>안녕, {st.session_state.user_name}아! 👋</h1>
            <p style="font-size: 17px; color: #555; font-weight: 600; margin-top:5px;">오늘도 재미있게 돈 공부 해볼까? ✨</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. 카드 레이아웃 (반응형 그리드 사용)
    # 내 저축함 & 오늘의 학습
    col1, col2 = st.columns(2)
    
    with col1:
        # 내 저축함 카드 (정보 보강)
        st.markdown("""
        <div class="dash-card card-mint">
            <div class="card-title">💰 내 저축함</div>
            <div class="badge-label" style="background:#fff385; color:#7F6000; position:absolute; top:25px; right:25px;">저축왕 진행 중! 👑</div>
            <div style="margin-top:20px;">
                <div class="card-subtitle">저축 성취도 (75%)</div>
                <div class="progress-bar-bg"><div class="progress-bar-fill" style="width: 75%;"></div></div>
                <h2 style="margin:5px 0; font-size: 34px; font-weight:900;">45,000원</h2>
                <p style="margin:0; font-size:14px; font-weight:700; opacity:0.8;">🌱 목표: 60,000원</p>
            </div>
            <div class="card-mascot">🍯</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("거래 기록 보기 📋", key="main_history", use_container_width=True):
            st.switch_page("pages/9_💵_용돈_관리.py")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 오늘의 퀴즈 카드
        st.markdown("""
        <div class="dash-card card-coral">
            <div class="card-title">❓ 오늘의 퀴즈</div>
            <p style="font-size: 18px; font-weight:700; margin-top:20px;">매일매일 지식이 쑥쑥!</p>
            <div class="badge-label" style="margin-top:5px;">새로운 미션 도착! ✨</div>
            <div class="card-mascot">❓</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("지금 도전! 🚀", key="main_quiz", use_container_width=True):
            st.switch_page("pages/7_🎯_금융_미션.py")

    with col2:
        # 오늘의 학습 카드
        st.markdown("""
        <div class="dash-card card-yellow">
            <div class="card-title">📖 오늘의 학습</div>
            <div class="badge-label" style="background:#C5B4E3; color:#3D2B66; position:absolute; top:25px; right:25px;">꿈꾸기 가이드 📖</div>
            <div style="margin-top:20px;">
                <div class="card-subtitle">오늘의 목표 (40%)</div>
                <div class="progress-bar-bg"><div class="progress-bar-fill" style="width: 40%;"></div></div>
                <p style="margin:0; font-weight:700; font-size:16px;">3/5 완료</p>
                <p style="margin:5px 0 0 0; font-size:14px; opacity:0.8;">꿈을 이루는 저축법 배우기</p>
            </div>
            <div class="card-mascot">🤖</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("학습 계속하기 📚", key="main_study", use_container_width=True):
            st.switch_page("pages/8_📖_금융_스토리.py")
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 나의 목표 카드 (정보 보강)
        st.markdown("""
        <div class="dash-card card-lavender">
            <div class="card-title">🎯 나의 목표</div>
            <div style="margin-top:20px;">
                <div class="card-subtitle">자전거 사기 (10%)</div>
                <div class="progress-bar-bg"><div class="progress-bar-fill" style="width: 10%;"></div></div>
                <p style="margin:0; font-weight:700; font-size:16px;">"새 자전거 사기" 🚲</p>
                <p style="margin:5px 0 0 0; font-size:14px; font-weight:700;">남은 금액: 54,000원</p>
            </div>
            <div class="card-mascot">🎯</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("목표 관리하기 🧸", key="main_goal", use_container_width=True):
            st.switch_page("pages/9_💵_용돈_관리.py")

    # 로그인 성공 풍선 (처음 한 번만)
    if st.session_state.get('show_login_success', False):
        st.balloons()
        st.session_state.show_login_success = False

# 메인 로직
if st.session_state.logged_in:
    main_page()
else:
    login_page()
