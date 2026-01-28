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
        </style>
        """, unsafe_allow_html=True)
        st.markdown("### 💰 AI 금융교육 서비스")
        st.markdown("로그인하여 서비스를 이용하세요.")
    
    st.title("💰 AI 금융교육 서비스")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["🔐 로그인", "📝 회원가입"])
    
    with tab1:
        st.subheader("로그인")
        
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
                    # 생성된 코드를 입력란에 즉시 반영하도록 세션 상태 설정
                    st.session_state.signup_parent_code = new_code
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
                        <button onclick="copyToClipboard('{generated_code}')" 
                                style='background: rgba(255,255,255,0.2); border: 1px solid white; color: white; 
                                       padding: 8px 20px; border-radius: 8px; cursor: pointer; font-weight: bold;'>
                            📋 클립보드에 복사
                        </button>
                        <p style='font-size: 0.9em; margin-top: 10px; opacity: 0.9;'>
                            💡 코드가 아래 입력란에 자동으로 입력되었습니다.
                        </p>
                    </div>
                    <script>
                    function copyToClipboard(text) {{
                        const textArea = document.createElement("textarea");
                        textArea.value = text;
                        document.body.appendChild(textArea);
                        textArea.select();
                        try {{
                            document.execCommand("copy");
                            alert("코드가 클립보드에 복사되었습니다: " + text);
                        }} catch (err) {{
                            console.error("복사 실패", err);
                        }}
                        document.body.removeChild(textArea);
                    }}
                    </script>
                    """, unsafe_allow_html=True)

                # 부모 코드 입력란 (value를 세션 상태와 연동)
                parent_code = st.text_input(
                    "부모 코드 (8자리)", 
                    value=st.session_state.get('signup_parent_code', ''),
                    key="signup_parent_code_input",
                    help="부모 코드 생성 버튼을 누르면 자동으로 채워집니다."
                )
                # 입력란의 값을 세션 상태에 다시 저장 (사용자가 직접 수정할 수도 있으므로)
                st.session_state.signup_parent_code = parent_code
            else:
                # 아이는 부모 코드 직접 입력
                parent_code = st.text_input(
                    "부모 코드 (8자리)", 
                    value=st.session_state.get('signup_parent_code', ''),
                    key="signup_parent_code_child", 
                    help="부모님께 받은 코드를 입력하세요."
                )
                st.session_state.signup_parent_code = parent_code
        
        if st.button("회원가입", type="primary", use_container_width=True):
            parent_code = st.session_state.get('signup_parent_code', '') # 최종 값 가져오기
            if not username:
                st.error("사용자명을 입력해주세요.")
            elif not password:
                st.error("비밀번호를 입력해주세요.")
            elif not name:
                st.error("이름을 입력해주세요.")
            elif not parent_code or not validate_parent_code(parent_code):
                st.error("유효한 부모 코드(8자리)를 입력해주세요.")
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
    
    # 로그인 성공 메시지 표시 (한 번만, 간단하게)
    if st.session_state.get('show_login_success', True):
        st.success(f"✅ {st.session_state.user_name}님, 환영합니다! 🎉")
        st.session_state.show_login_success = False
    
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
