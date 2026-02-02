-- 사용자 테이블
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    age INTEGER,
    user_type TEXT NOT NULL DEFAULT 'child',  -- 'parent' or 'child'
    parent_code TEXT NOT NULL,
    parent_ssn TEXT,  -- 부모 주민등록번호 (암호화 저장)
    phone_number TEXT,  -- 휴대폰번호
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    category TEXT,  -- 예: 간식/장난감/저축/기타
    description TEXT,
    related_request_id INTEGER, -- 용돈 요청/지출 승인 등과 연결
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

-- 용돈/지출 요청 테이블 (아이 → 부모)
CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    child_id INTEGER NOT NULL,
    parent_code TEXT NOT NULL,
    request_type TEXT NOT NULL, -- 'allowance' | 'spend'
    amount REAL NOT NULL,
    category TEXT,
    reason TEXT,
    status TEXT NOT NULL DEFAULT 'pending', -- 'pending' | 'approved' | 'rejected'
    decided_by INTEGER,
    decided_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (child_id) REFERENCES users(id),
    FOREIGN KEY (decided_by) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_requests_parent_code ON requests(parent_code);
CREATE INDEX IF NOT EXISTS idx_requests_child_id ON requests(child_id);
CREATE INDEX IF NOT EXISTS idx_requests_status ON requests(status);

-- 정기 용돈 테이블 (부모 → 자녀)
CREATE TABLE IF NOT EXISTS recurring_allowances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_id INTEGER NOT NULL,
    child_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    frequency TEXT NOT NULL, -- 'weekly' | 'monthly'
    day_of_week INTEGER, -- 0=월..6=일 (weekly)
    day_of_month INTEGER, -- 1..31 (monthly)
    next_run DATE,
    is_active INTEGER NOT NULL DEFAULT 1,
    memo TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES users(id),
    FOREIGN KEY (child_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_recurring_allowances_parent_id ON recurring_allowances(parent_id);
CREATE INDEX IF NOT EXISTS idx_recurring_allowances_child_id ON recurring_allowances(child_id);

-- 저축 목표 테이블 (아이)
CREATE TABLE IF NOT EXISTS goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    target_amount REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    achieved_at TIMESTAMP,
    is_active INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_goals_user_id ON goals(user_id);

-- 목표 적립(기여) 테이블 (저축 기록을 목표에 연결)
CREATE TABLE IF NOT EXISTS goal_contributions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (goal_id) REFERENCES goals(id)
);

CREATE INDEX IF NOT EXISTS idx_goal_contrib_goal_id ON goal_contributions(goal_id);

-- 알림 테이블 (부모/아이 공용)
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    body TEXT,
    level TEXT NOT NULL DEFAULT 'info', -- 'info'|'warning'|'success'
    is_read INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);

-- 미션 템플릿(시스템/부모 커스텀)
CREATE TABLE IF NOT EXISTS mission_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_code TEXT, -- NULL이면 시스템 공용
    title TEXT NOT NULL,
    description TEXT,
    difficulty TEXT NOT NULL DEFAULT 'easy', -- easy|normal|hard
    reward_amount REAL NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_by INTEGER, -- 부모가 만들면 parent user_id
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- 미션 할당(아이에게 배정)
CREATE TABLE IF NOT EXISTS mission_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    template_id INTEGER NOT NULL,
    cycle TEXT NOT NULL, -- daily|weekly|custom
    assigned_date DATE NOT NULL,
    status TEXT NOT NULL DEFAULT 'active', -- active|completed|expired
    completed_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (template_id) REFERENCES mission_templates(id)
);

CREATE INDEX IF NOT EXISTS idx_mission_assignments_user_id ON mission_assignments(user_id);
CREATE INDEX IF NOT EXISTS idx_mission_assignments_assigned_date ON mission_assignments(assigned_date);
CREATE INDEX IF NOT EXISTS idx_mission_assignments_status ON mission_assignments(status);

-- 배지/업적
CREATE TABLE IF NOT EXISTS badges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    icon TEXT,
    required_xp INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS user_badges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    badge_id INTEGER NOT NULL,
    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (badge_id) REFERENCES badges(id)
);

CREATE INDEX IF NOT EXISTS idx_user_badges_user_id ON user_badges(user_id);

-- 학습 진행(경제 교실)
CREATE TABLE IF NOT EXISTS learning_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    lesson_code TEXT NOT NULL,
    progress REAL NOT NULL DEFAULT 0, -- 0..1
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, lesson_code),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_learning_progress_user_id ON learning_progress(user_id);
