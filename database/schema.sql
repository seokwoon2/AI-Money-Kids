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

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_behaviors_user_id ON behaviors(user_id);
CREATE INDEX IF NOT EXISTS idx_behaviors_timestamp ON behaviors(timestamp);
CREATE INDEX IF NOT EXISTS idx_scores_user_id ON scores(user_id);
CREATE INDEX IF NOT EXISTS idx_users_parent_code ON users(parent_code);
CREATE INDEX IF NOT EXISTS idx_user_skins_user_id ON user_skins(user_id);