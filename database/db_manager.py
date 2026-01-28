import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Tuple
import bcrypt
from config import Config

class DatabaseManager:
    """데이터베이스 관리 클래스"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or Config.DATABASE_PATH
        self._ensure_db_exists()
        self._init_database()
    
    def _ensure_db_exists(self):
        """데이터베이스 파일이 존재하도록 디렉토리 생성"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
    
    def _init_database(self):
        """데이터베이스 초기화 및 테이블 생성"""
        with open(os.path.join(os.path.dirname(__file__), 'schema.sql'), 'r', encoding='utf-8') as f:
            schema = f.read()
        
        conn = sqlite3.connect(self.db_path)
        conn.executescript(schema)
        conn.commit()
        conn.close()
    
    def _get_connection(self):
        """데이터베이스 연결 반환"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    # ========== 사용자 관리 ==========
    
    def create_user(self, username: str, password: str, name: str, age: int, parent_code: str, user_type: str = 'child') -> int:
        """새 사용자 생성"""
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # 기존 테이블에 user_type 컬럼이 없을 수 있으므로 ALTER TABLE 시도
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN user_type TEXT DEFAULT 'child'")
                conn.commit()
            except sqlite3.OperationalError:
                # 컬럼이 이미 존재하면 무시
                pass
            
            cursor.execute("""
                INSERT INTO users (username, password_hash, name, age, parent_code, user_type)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (username, password_hash, name, age, parent_code, user_type))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """사용자명으로 사용자 조회"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """ID로 사용자 조회"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """비밀번호 검증"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def get_users_by_parent_code(self, parent_code: str) -> List[Dict]:
        """부모 코드로 연결된 모든 자녀 조회"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM users WHERE parent_code = ? AND user_type = 'child' ORDER BY name", (parent_code,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()
    
    def get_parent_by_code(self, parent_code: str) -> Optional[Dict]:
        """부모 코드로 부모 사용자 조회"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM users WHERE parent_code = ? AND user_type = 'parent' LIMIT 1", (parent_code,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
    
    def update_user_name(self, user_id: int, new_name: str) -> bool:
        """사용자 이름 업데이트"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE users SET name = ? WHERE id = ?", (new_name, user_id))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def update_user_password(self, user_id: int, new_password: str) -> bool:
        """사용자 비밀번호 업데이트"""
        password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def update_user_info(self, user_id: int, name: str = None, password: str = None) -> bool:
        """사용자 정보 업데이트 (이름, 비밀번호)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            updates = []
            params = []
            
            if name:
                updates.append("name = ?")
                params.append(name)
            
            if password:
                password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                updates.append("password_hash = ?")
                params.append(password_hash)
            
            if not updates:
                return False
            
            params.append(user_id)
            query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def update_user_type(self, user_id: int, user_type: str) -> bool:
        """사용자 타입 업데이트 (parent/child)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE users SET user_type = ? WHERE id = ?", (user_type, user_id))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def get_all_users(self) -> List[Dict]:
        """모든 사용자 조회 (관리용)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, username, name, user_type, parent_code, age FROM users ORDER BY id")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()
    
    # ========== 대화 관리 ==========
    
    def create_conversation(self, user_id: int) -> int:
        """새 대화 세션 생성"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO conversations (user_id)
                VALUES (?)
            """, (user_id,))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()
    
    def get_or_create_today_conversation(self, user_id: int) -> int:
        """오늘 날짜의 대화 세션 조회 또는 생성"""
        today = datetime.now().date()
        
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # 오늘 생성된 대화 세션 찾기
            cursor.execute("""
                SELECT id FROM conversations 
                WHERE user_id = ? AND DATE(created_at) = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (user_id, today.isoformat()))
            
            row = cursor.fetchone()
            if row:
                return row['id']
            
            # 없으면 새로 생성
            cursor.execute("""
                INSERT INTO conversations (user_id)
                VALUES (?)
            """, (user_id,))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()
    
    def save_message(self, conversation_id: int, role: str, content: str):
        """메시지 저장"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO messages (conversation_id, role, content)
                VALUES (?, ?, ?)
            """, (conversation_id, role, content))
            conn.commit()
        finally:
            conn.close()
    
    def get_conversation_messages(self, conversation_id: int, limit: int = 10) -> List[Dict]:
        """대화 메시지 조회 (최근 N개)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT role, content, timestamp
                FROM messages
                WHERE conversation_id = ?
                ORDER BY timestamp ASC
                LIMIT ?
            """, (conversation_id, limit))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()
    
    # ========== 행동 기록 ==========
    
    def save_behavior(self, user_id: int, behavior_type: str, amount: float = None, description: str = None):
        """금융 행동 기록 저장"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO behaviors (user_id, behavior_type, amount, description)
                VALUES (?, ?, ?, ?)
            """, (user_id, behavior_type, amount, description))
            conn.commit()
        finally:
            conn.close()
    
    def get_user_behaviors(self, user_id: int, limit: int = 100) -> List[Dict]:
        """사용자의 행동 기록 조회"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT * FROM behaviors
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (user_id, limit))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()
    
    def get_behaviors_by_type(self, user_id: int, behavior_type: str) -> List[Dict]:
        """특정 타입의 행동 기록 조회"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT * FROM behaviors
                WHERE user_id = ? AND behavior_type = ?
                ORDER BY timestamp DESC
            """, (user_id, behavior_type))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()
    
    # ========== 점수 관리 ==========
    
    def save_score(self, user_id: int, impulsivity: float, saving_tendency: float, patience: float):
        """금융습관 점수 저장"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO scores (user_id, impulsivity, saving_tendency, patience)
                VALUES (?, ?, ?, ?)
            """, (user_id, impulsivity, saving_tendency, patience))
            conn.commit()
        finally:
            conn.close()
    
    def get_latest_score(self, user_id: int) -> Optional[Dict]:
        """최신 점수 조회"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT * FROM scores
                WHERE user_id = ?
                ORDER BY calculated_at DESC
                LIMIT 1
            """, (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
    
    def get_score_history(self, user_id: int, days: int = 30) -> List[Dict]:
        """점수 히스토리 조회"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT * FROM scores
                WHERE user_id = ? AND calculated_at >= datetime('now', '-' || ? || ' days')
                ORDER BY calculated_at ASC
            """, (user_id, days))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()
