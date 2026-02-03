-- 사용자 테이블
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    age INTEGER,
    birth_date TEXT,  -- YYYY-MM-DD
    character_code TEXT,  -- 선택 캐릭터 코드
    character_nickname TEXT,  -- 캐릭터 별명/이름
    character_skin_code TEXT,  -- 선택 스킨 코드
    coins INTEGER NOT NULL DEFAULT 0,  -- 게임화 재화(코인)
    last_reward_level INTEGER NOT NULL DEFAULT 0,  -- 레벨업 보상 지급 체크포인트
    user_type TEXT NOT NULL DEFAULT 'child',  -- 'parent' or 'child'
    parent_code TEXT NOT NULL,
    parent_ssn TEXT,  -- 부모 주민등록번호 (암호화 저장)
    phone_number TEXT,  -- 휴대폰번호
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 캐릭터 스킨 해금(게임화)
CREATE TABLE IF NOT EXISTS user_skins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    skin_code TEXT NOT NULL,
    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, skin_code),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 대화 세션 테이블
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 메시지 테이블
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    role TEXT NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);

-- 금융 행동 기록 테이블
CREATE TABLE IF NOT EXISTS behaviors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    behavior_type TEXT NOT NULL,  -- 'saving', 'planned_spending', 'impulse_buying', 'delayed_gratification', 'comparing_prices'
    amount REAL,
    description TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 감정 기록(소비 전/후, 미션 리플렉션 등)
CREATE TABLE IF NOT EXISTS emotion_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    context TEXT NOT NULL,  -- 'pre_spend' | 'post_spend' | 'daily' | ...
    emotion TEXT NOT NULL,  -- emoji or short label
    note TEXT,
    related_behavior_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (related_behavior_id) REFERENCES behaviors(id)
);

-- 금융습관 점수 테이블
CREATE TABLE IF NOT EXISTS scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    impulsivity REAL NOT NULL,  -- 0-100 (낮을수록 좋음)
    saving_tendency REAL NOT NULL,  -- 0-100 (높을수록 좋음)
    patience REAL NOT NULL,  -- 0-100 (높을수록 좋음)
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 요청(아이 → 부모) : 용돈/지출 승인
CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    child_id INTEGER NOT NULL,
    parent_code TEXT NOT NULL,
    request_type TEXT NOT NULL,  -- 'allowance' | 'spend'
    amount REAL NOT NULL,
    category TEXT,
    reason TEXT,
    status TEXT NOT NULL DEFAULT 'pending',  -- pending|approved|rejected
    decided_by INTEGER,
    decided_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (child_id) REFERENCES users(id)
);

-- 알림
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    body TEXT,
    level TEXT NOT NULL DEFAULT 'info',  -- info|success|warning|error
    is_read INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 정기 용돈
CREATE TABLE IF NOT EXISTS recurring_allowances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_id INTEGER NOT NULL,
    child_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    frequency TEXT NOT NULL,  -- weekly|monthly
    day_of_week INTEGER,
    day_of_month INTEGER,
    next_run TEXT,
    memo TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES users(id),
    FOREIGN KEY (child_id) REFERENCES users(id)
);

-- 초대코드(부모-자녀 연결) : MF-XXXX (24시간)
CREATE TABLE IF NOT EXISTS invite_codes (
    code TEXT PRIMARY KEY, -- MF-XXXX
    parent_id INTEGER NOT NULL,
    expires_at TEXT NOT NULL, -- YYYY-MM-DD HH:MM:SS
    is_used INTEGER NOT NULL DEFAULT 0,
    used_by_child_id INTEGER,
    used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES users(id),
    FOREIGN KEY (used_by_child_id) REFERENCES users(id)
);

-- 충동구매/리스크 시그널(부모 리포트/알림용)
CREATE TABLE IF NOT EXISTS risk_signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    signal_type TEXT NOT NULL, -- impulse_stop | impulse_request | ...
    score INTEGER NOT NULL DEFAULT 0,
    context TEXT,
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 리마인더(예약 알림)
CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    body TEXT,
    due_at TEXT NOT NULL, -- YYYY-MM-DD HH:MM:SS
    is_sent INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_behaviors_user_id ON behaviors(user_id);
CREATE INDEX IF NOT EXISTS idx_behaviors_timestamp ON behaviors(timestamp);
CREATE INDEX IF NOT EXISTS idx_emotion_logs_user_id ON emotion_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_emotion_logs_created_at ON emotion_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_scores_user_id ON scores(user_id);
CREATE INDEX IF NOT EXISTS idx_users_parent_code ON users(parent_code);
CREATE INDEX IF NOT EXISTS idx_user_skins_user_id ON user_skins(user_id);
CREATE INDEX IF NOT EXISTS idx_requests_parent_code ON requests(parent_code);
CREATE INDEX IF NOT EXISTS idx_requests_child_id ON requests(child_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_invite_codes_parent_id ON invite_codes(parent_id);
CREATE INDEX IF NOT EXISTS idx_invite_codes_expires_at ON invite_codes(expires_at);
CREATE INDEX IF NOT EXISTS idx_risk_signals_user_id ON risk_signals(user_id);
CREATE INDEX IF NOT EXISTS idx_risk_signals_created_at ON risk_signals(created_at);
CREATE INDEX IF NOT EXISTS idx_reminders_user_id ON reminders(user_id);
CREATE INDEX IF NOT EXISTS idx_reminders_due_at ON reminders(due_at);