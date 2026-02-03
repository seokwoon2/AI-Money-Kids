import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Tuple
import bcrypt
from config import Config
from datetime import date as _date, timedelta as _timedelta
from utils.characters import get_skins_for_character
from datetime import timedelta as _timedelta2
import random as _random
import re as _re
import json as _json

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

        # 기존 DB 마이그레이션(컬럼 추가 등)
        self._ensure_columns()

        # 기존 DB에 새 테이블이 추가되었을 수 있으니 한 번 더 보정
        self._ensure_tables()

    def _ensure_tables(self):
        """기존 DB에 누락된 테이블을 보정(CREATE TABLE IF NOT EXISTS)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # schema.sql 전체를 다시 실행하면 안전(CREATE IF NOT EXISTS)
            with open(os.path.join(os.path.dirname(__file__), "schema.sql"), "r", encoding="utf-8") as f:
                schema = f.read()
            conn.executescript(schema)
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()

    # ========== 초대코드(MF-XXXX) ==========

    @staticmethod
    def _normalize_invite_code(code: str | None) -> str:
        return str(code or "").strip().upper()

    def create_invite_code(self, parent_id: int, ttl_hours: int = 24) -> Dict:
        """
        MF-XXXX 초대코드 생성(24시간 유효)
        - 기본은 1회 사용 처리(is_used=1)지만, 필요하면 재생성하면 됩니다.
        """
        parent_id = int(parent_id)
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # 최대 30회 시도(중복 회피)
            for _ in range(30):
                code = f"MF-{_random.randint(0, 9999):04d}"
                cursor.execute("SELECT code FROM invite_codes WHERE code = ?", (code,))
                if cursor.fetchone():
                    continue
                expires_at = (datetime.now() + _timedelta2(hours=int(ttl_hours))).strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute(
                    """
                    INSERT INTO invite_codes (code, parent_id, expires_at, is_used)
                    VALUES (?, ?, ?, 0)
                    """,
                    (code, parent_id, expires_at),
                )
                conn.commit()
                return {"code": code, "expires_at": expires_at}
            raise RuntimeError("초대코드 생성에 실패했습니다.")
        finally:
            conn.close()

    def get_invite_code(self, code: str) -> Optional[Dict]:
        code = self._normalize_invite_code(code)
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM invite_codes WHERE code = ? LIMIT 1", (code,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def verify_invite_code(self, code: str) -> Optional[Dict]:
        """
        유효한 초대코드인지 확인하고 부모 사용자 반환
        return: {"invite":..., "parent":...}
        """
        code = self._normalize_invite_code(code)
        if not _re.fullmatch(r"MF-\d{4}", code):
            return None
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT *
                FROM invite_codes
                WHERE code = ?
                  AND is_used = 0
                  AND datetime(expires_at) > datetime('now')
                LIMIT 1
                """,
                (code,),
            )
            inv = cursor.fetchone()
            if not inv:
                return None
            invd = dict(inv)
            cursor.execute("SELECT * FROM users WHERE id = ? AND user_type = 'parent' LIMIT 1", (int(invd["parent_id"]),))
            p = cursor.fetchone()
            if not p:
                return None
            return {"invite": invd, "parent": dict(p)}
        finally:
            conn.close()

    def consume_invite_code(self, code: str, child_id: int) -> bool:
        """연동 완료 시 1회 사용 처리"""
        code = self._normalize_invite_code(code)
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE invite_codes
                SET is_used = 1, used_by_child_id = ?, used_at = CURRENT_TIMESTAMP
                WHERE code = ? AND is_used = 0
                """,
                (int(child_id), code),
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def get_active_invite_code(self, parent_id: int) -> Optional[Dict]:
        """부모의 사용 가능(미사용/미만료) 초대코드 중 최신 1개"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT code, expires_at, parent_id, is_used
                FROM invite_codes
                WHERE parent_id = ?
                  AND is_used = 0
                  AND datetime(expires_at) > datetime('now')
                ORDER BY id DESC
                LIMIT 1
                """,
                (int(parent_id),),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def link_child_with_invite_code(self, code: str, child_id: int) -> Optional[Dict]:
        """
        초대코드(MF-XXXX)로 자녀 계정을 부모와 연동(원자적 처리).
        - invite_codes 유효성(미사용/미만료) 확인
        - 자녀 users.parent_code 를 부모의 parent_code 로 업데이트(기존 구조 유지)
        - invite_codes 1회 사용 처리
        return: {"code":..., "expires_at":..., "parent_id":..., "parent_name":..., "parent_code":...}
        """
        code = self._normalize_invite_code(code)
        if not _re.fullmatch(r"MF-\d{4}", code):
            return None

        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("BEGIN")
            cursor.execute(
                """
                SELECT ic.code, ic.expires_at, ic.parent_id, u.name AS parent_name, u.parent_code AS parent_code
                FROM invite_codes ic
                JOIN users u ON u.id = ic.parent_id
                WHERE ic.code = ?
                  AND ic.is_used = 0
                  AND datetime(ic.expires_at) > datetime('now')
                  AND u.user_type = 'parent'
                LIMIT 1
                """,
                (code,),
            )
            row = cursor.fetchone()
            if not row:
                conn.rollback()
                return None

            d = dict(row)
            parent_code = str(d.get("parent_code") or "").strip().upper()
            if not parent_code:
                conn.rollback()
                return None

            cursor.execute(
                """
                UPDATE users
                SET parent_code = ?
                WHERE id = ? AND user_type = 'child'
                """,
                (parent_code, int(child_id)),
            )
            if cursor.rowcount <= 0:
                conn.rollback()
                return None

            cursor.execute(
                """
                UPDATE invite_codes
                SET is_used = 1, used_by_child_id = ?, used_at = CURRENT_TIMESTAMP
                WHERE code = ? AND is_used = 0
                """,
                (int(child_id), code),
            )
            if cursor.rowcount <= 0:
                conn.rollback()
                return None

            conn.commit()
            return {
                "code": d.get("code"),
                "expires_at": d.get("expires_at"),
                "parent_id": d.get("parent_id"),
                "parent_name": d.get("parent_name"),
                "parent_code": parent_code,
            }
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            return None
        finally:
            conn.close()

    def _ensure_columns(self):
        """기존 DB에 누락된 컬럼/테이블 보정(안전한 ALTER)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # behaviors 확장 컬럼
            try:
                cursor.execute("ALTER TABLE behaviors ADD COLUMN category TEXT")
                conn.commit()
            except sqlite3.OperationalError:
                pass
            try:
                cursor.execute("ALTER TABLE behaviors ADD COLUMN related_request_id INTEGER")
                conn.commit()
            except sqlite3.OperationalError:
                pass

            # users 확장 컬럼
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN birth_date TEXT")
                conn.commit()
            except sqlite3.OperationalError:
                pass
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN character_code TEXT")
                conn.commit()
            except sqlite3.OperationalError:
                pass
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN character_nickname TEXT")
                conn.commit()
            except sqlite3.OperationalError:
                pass
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN character_skin_code TEXT")
                conn.commit()
            except sqlite3.OperationalError:
                pass
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN coins INTEGER NOT NULL DEFAULT 0")
                conn.commit()
            except sqlite3.OperationalError:
                pass
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN last_reward_level INTEGER NOT NULL DEFAULT 0")
                conn.commit()
            except sqlite3.OperationalError:
                pass

            # user_skins 테이블(없으면 생성)
            try:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS user_skins (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        skin_code TEXT NOT NULL,
                        unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id, skin_code)
                    )
                    """
                )
                conn.commit()
            except Exception:
                pass
        finally:
            conn.close()

    # ========== 미션 ==========

    def seed_default_missions_and_badges(self):
        """기본 미션/배지 시드(없을 때만)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # 기본 미션 템플릿(시스템 공용)
            cursor.execute("SELECT COUNT(*) as cnt FROM mission_templates")
            if int(cursor.fetchone()["cnt"] or 0) == 0:
                templates = [
                    ("오늘은 저금통에 1,000원 저축하기", "저축(saving) 기록을 남겨요", "easy", 500),
                    ("계획 지출 1건 기록하기", "planned_spending으로 지출을 계획해요", "normal", 300),
                    ("가격 비교 해보기", "comparing_prices 활동을 해봐요", "easy", 200),
                    ("충동 구매 참기", "delayed_gratification 활동을 해봐요", "hard", 700),
                ]
                cursor.executemany(
                    """
                    INSERT INTO mission_templates (parent_code, title, description, difficulty, reward_amount, is_active)
                    VALUES (NULL, ?, ?, ?, ?, 1)
                    """,
                    templates,
                )
                conn.commit()

            # 기본 배지
            cursor.execute("SELECT COUNT(*) as cnt FROM badges")
            if int(cursor.fetchone()["cnt"] or 0) == 0:
                badges = [
                    ("xp_10", "새싹 경제가", "활동을 10번 완료했어요", "🌱", 10),
                    ("xp_50", "성실한 저축가", "활동을 50번 완료했어요", "💎", 50),
                    ("xp_100", "금융 마스터", "활동을 100번 완료했어요", "🏆", 100),
                ]
                cursor.executemany(
                    "INSERT INTO badges (code, title, description, icon, required_xp) VALUES (?, ?, ?, ?, ?)",
                    badges,
                )
                conn.commit()
        finally:
            conn.close()

    def create_custom_mission(self, parent_code: str, title: str, description: str, difficulty: str, reward_amount: float, created_by: int) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO mission_templates (parent_code, title, description, difficulty, reward_amount, is_active, created_by)
                VALUES (?, ?, ?, ?, ?, 1, ?)
                """,
                (parent_code, title, description, difficulty, reward_amount, created_by),
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_custom_missions(self, parent_code: str):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT * FROM mission_templates WHERE parent_code = ? AND is_active = 1 ORDER BY created_at DESC",
                (parent_code,),
            )
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def assign_daily_missions_if_needed(self, user_id: int, date_str: str):
        """해당 날짜에 일일 미션이 없으면 3개 배정"""
        self.seed_default_missions_and_badges()
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT COUNT(*) as cnt FROM mission_assignments WHERE user_id = ? AND cycle = 'daily' AND assigned_date = ?",
                (user_id, date_str),
            )
            if int(cursor.fetchone()["cnt"] or 0) > 0:
                return
            cursor.execute(
                "SELECT id FROM mission_templates WHERE is_active = 1 AND parent_code IS NULL ORDER BY RANDOM() LIMIT 3"
            )
            templates = [r["id"] for r in cursor.fetchall()]
            cursor.executemany(
                """
                INSERT INTO mission_assignments (user_id, template_id, cycle, assigned_date, status)
                VALUES (?, ?, 'daily', ?, 'active')
                """,
                [(user_id, tid, date_str) for tid in templates],
            )
            conn.commit()
        finally:
            conn.close()

    def get_missions_for_user(self, user_id: int, date_str: str = None, active_only: bool = True):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            q = """
                SELECT a.*, t.title, t.description, t.difficulty, t.reward_amount
                FROM mission_assignments a
                JOIN mission_templates t ON a.template_id = t.id
                WHERE a.user_id = ?
            """
            params = [user_id]
            if date_str:
                q += " AND a.assigned_date = ?"
                params.append(date_str)
            if active_only:
                q += " AND a.status = 'active'"
            q += " ORDER BY a.assigned_date DESC, a.id DESC"
            cursor.execute(q, params)
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def complete_mission(self, assignment_id: int) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE mission_assignments SET status='completed', completed_at=CURRENT_TIMESTAMP WHERE id = ? AND status='active'",
                (assignment_id,),
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    # ========== 배지/성장 ==========

    def get_xp(self, user_id: int) -> int:
        """XP(가중치): behaviors 개수 + 완료 미션 난이도 가중 합"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) as cnt FROM behaviors WHERE user_id = ?", (user_id,))
            bcnt = int(cursor.fetchone()["cnt"] or 0)
            # missions: difficulty join (없으면 count fallback)
            try:
                cursor.execute(
                    """
                    SELECT COALESCE(SUM(
                        CASE COALESCE(t.difficulty,'normal')
                            WHEN 'easy' THEN 5
                            WHEN 'hard' THEN 12
                            ELSE 8
                        END
                    ),0) as xp
                    FROM mission_assignments a
                    JOIN mission_templates t ON a.template_id = t.id
                    WHERE a.user_id = ? AND a.status='completed'
                    """,
                    (user_id,),
                )
                mxp = int((cursor.fetchone() or {}).get("xp") or 0)
            except Exception:
                cursor.execute(
                    "SELECT COUNT(*) as cnt FROM mission_assignments WHERE user_id = ? AND status='completed'",
                    (user_id,),
                )
                mxp = int(cursor.fetchone()["cnt"] or 0)
            return int(bcnt + mxp)
        finally:
            conn.close()

    def award_badges_if_needed(self, user_id: int):
        self.seed_default_missions_and_badges()
        xp = self.get_xp(user_id)
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT badge_id FROM user_badges WHERE user_id = ?", (user_id,))
            owned = {int(r["badge_id"]) for r in cursor.fetchall()}
            cursor.execute("SELECT * FROM badges ORDER BY required_xp ASC")
            for b in cursor.fetchall():
                bid = int(b["id"])
                if bid in owned:
                    continue
                if xp >= int(b["required_xp"] or 0):
                    cursor.execute("INSERT INTO user_badges (user_id, badge_id) VALUES (?, ?)", (user_id, bid))
            conn.commit()
        finally:
            conn.close()

    def get_user_badges(self, user_id: int):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT ub.earned_at, b.*
                FROM user_badges ub
                JOIN badges b ON ub.badge_id = b.id
                WHERE ub.user_id = ?
                ORDER BY ub.earned_at DESC
                """,
                (user_id,),
            )
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # ========== 학습 진행 ==========

    def upsert_learning_progress(self, user_id: int, lesson_code: str, progress: float):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO learning_progress (user_id, lesson_code, progress)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, lesson_code) DO UPDATE SET
                    progress=excluded.progress,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (user_id, lesson_code, progress),
            )
            conn.commit()
        finally:
            conn.close()

    def get_learning_progress(self, user_id: int):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM learning_progress WHERE user_id = ?", (user_id,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # ========== 감정 기록 ==========

    def create_emotion_log(
        self,
        user_id: int,
        context: str,
        emotion: str,
        note: str = None,
        related_behavior_id: int = None,
    ) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO emotion_logs (user_id, context, emotion, note, related_behavior_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    int(user_id),
                    str(context or "").strip(),
                    str(emotion or "").strip(),
                    (note or None),
                    (int(related_behavior_id) if related_behavior_id else None),
                ),
            )
            conn.commit()
            return int(cursor.lastrowid or 0)
        finally:
            conn.close()

    def get_emotion_logs(self, user_id: int, limit: int = 30) -> List[Dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT *
                FROM emotion_logs
                WHERE user_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (int(user_id), int(limit)),
            )
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_family_emotion_logs(self, parent_code: str, limit: int = 80) -> List[Dict]:
        """부모 코드 기준: 자녀들의 감정 기록(최근)"""
        if not parent_code:
            return []
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT e.*, u.name as child_name, u.username as child_username
                FROM emotion_logs e
                JOIN users u ON e.user_id = u.id
                WHERE u.parent_code = ?
                  AND u.user_type = 'child'
                ORDER BY e.created_at DESC, e.id DESC
                LIMIT ?
                """,
                (str(parent_code), int(limit)),
            )
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # ========== 리스크 시그널(충동구매 감지/멈추기) ==========

    def create_risk_signal(
        self,
        user_id: int,
        signal_type: str,
        score: int = 0,
        context: str = None,
        note: str = None,
    ) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO risk_signals (user_id, signal_type, score, context, note)
                VALUES (?, ?, ?, ?, ?)
                """,
                (int(user_id), str(signal_type), int(score or 0), (context or None), (note or None)),
            )
            conn.commit()
            return int(cursor.lastrowid or 0)
        finally:
            conn.close()

    def get_latest_risk_signal(self, user_id: int, within_minutes: int = 60) -> Optional[Dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT *
                FROM risk_signals
                WHERE user_id = ?
                  AND created_at >= datetime('now', ?)
                ORDER BY created_at DESC, id DESC
                LIMIT 1
                """,
                (int(user_id), f"-{int(within_minutes)} minutes"),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_family_risk_signals(self, parent_code: str, limit: int = 80) -> List[Dict]:
        if not parent_code:
            return []
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT rs.*, u.name as child_name, u.username as child_username
                FROM risk_signals rs
                JOIN users u ON rs.user_id = u.id
                WHERE u.parent_code = ?
                  AND u.user_type = 'child'
                ORDER BY rs.created_at DESC, rs.id DESC
                LIMIT ?
                """,
                (str(parent_code), int(limit)),
            )
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
    
    def _get_connection(self):
        """데이터베이스 연결 반환"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    # ========== 사용자 관리 ==========
    
    def create_user(
        self,
        username: str,
        password: str,
        name: str,
        age: int,
        parent_code: str,
        user_type: str = "child",
        parent_ssn: str = None,
        phone_number: str = None,
        birth_date: str = None,  # YYYY-MM-DD
        character_code: str = None,
        character_nickname: str = None,
        character_skin_code: str = None,
    ) -> int:
        """새 사용자 생성"""
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # 주민등록번호 암호화 (간단한 해시, 실제로는 더 강력한 암호화 필요)
        if parent_ssn:
            import hashlib
            parent_ssn_hash = hashlib.sha256(parent_ssn.encode('utf-8')).hexdigest()
        else:
            parent_ssn_hash = None
        
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # 기존 테이블에 컬럼이 없을 수 있으므로 ALTER TABLE 시도
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN user_type TEXT DEFAULT 'child'")
                conn.commit()
            except sqlite3.OperationalError:
                pass
            
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN parent_ssn TEXT")
                conn.commit()
            except sqlite3.OperationalError:
                pass
            
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN phone_number TEXT")
                conn.commit()
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE users ADD COLUMN birth_date TEXT")
                conn.commit()
            except sqlite3.OperationalError:
                pass
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN character_code TEXT")
                conn.commit()
            except sqlite3.OperationalError:
                pass
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN character_nickname TEXT")
                conn.commit()
            except sqlite3.OperationalError:
                pass
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN character_skin_code TEXT")
                conn.commit()
            except sqlite3.OperationalError:
                pass
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN coins INTEGER NOT NULL DEFAULT 0")
                conn.commit()
            except sqlite3.OperationalError:
                pass
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN last_reward_level INTEGER NOT NULL DEFAULT 0")
                conn.commit()
            except sqlite3.OperationalError:
                pass
            
            cursor.execute("""
                INSERT INTO users (
                    username, password_hash, name, age,
                    birth_date, character_code, character_nickname, character_skin_code,
                    coins, last_reward_level,
                    parent_code, user_type, parent_ssn, phone_number
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?, ?, ?, ?)
            """, (
                username,
                password_hash,
                name,
                age,
                birth_date,
                character_code,
                character_nickname,
                character_skin_code,
                parent_code,
                user_type,
                parent_ssn_hash,
                phone_number,
            ))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def update_user_birth_date(self, user_id: int, birth_date: str) -> bool:
        """생년월일 업데이트(YYYY-MM-DD)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE users SET birth_date = ? WHERE id = ?", (birth_date, user_id))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def update_user_character_code(self, user_id: int, character_code: str) -> bool:
        """캐릭터 코드 업데이트"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE users SET character_code = ? WHERE id = ?", (character_code, user_id))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def update_user_character_nickname(self, user_id: int, character_nickname: str) -> bool:
        """캐릭터 별명/이름 업데이트"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE users SET character_nickname = ? WHERE id = ?", (character_nickname, user_id))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def update_user_character_skin_code(self, user_id: int, character_skin_code: str) -> bool:
        """캐릭터 스킨 코드 업데이트"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE users SET character_skin_code = ? WHERE id = ?", (character_skin_code, user_id))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def add_coins(self, user_id: int, amount: int) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE users SET coins = COALESCE(coins,0) + ? WHERE id = ?", (int(amount), user_id))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def unlock_skin(self, user_id: int, skin_code: str) -> bool:
        """스킨 해금(중복 방지)"""
        if not skin_code:
            return False
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT OR IGNORE INTO user_skins (user_id, skin_code) VALUES (?, ?)",
                (int(user_id), str(skin_code)),
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def get_unlocked_skins(self, user_id: int) -> list[str]:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT skin_code FROM user_skins WHERE user_id = ? ORDER BY unlocked_at DESC", (int(user_id),))
            return [str(r["skin_code"]) for r in cursor.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def _level_from_xp(xp: int) -> int:
        return max(1, int(xp) // 20 + 1)

    def grant_level_rewards_if_needed(self, user_id: int) -> dict:
        """
        레벨업 보상 지급(중복 방지)
        - coins: 레벨당 10코인 + (5레벨마다 추가 50코인)
        - skins: 캐릭터별 스킨(required_level) 자동 해금
        """
        user = self.get_user_by_id(int(user_id)) or {}
        xp = 0
        try:
            xp = int(self.get_xp(int(user_id)) or 0)
        except Exception:
            xp = 0
        level_now = self._level_from_xp(xp)
        last_paid = int(user.get("last_reward_level") or 0)
        coins_before = int(user.get("coins") or 0)
        coins_gain = 0
        skins_unlocked: list[str] = []

        if level_now <= last_paid:
            return {
                "level_now": level_now,
                "levels_gained": 0,
                "coins_gained": 0,
                "coins_now": coins_before,
                "skins_unlocked": [],
            }

        for lv in range(last_paid + 1, level_now + 1):
            coins_gain += 10
            if lv % 5 == 0:
                coins_gain += 50

        if coins_gain:
            self.add_coins(int(user_id), coins_gain)

        # 스킨 해금: 기본 스킨만(상점 스킨은 구매)
        ccode = (user.get("character_code") or "").strip()
        if ccode:
            for skin in get_skins_for_character(ccode):
                if int(skin.get("price") or 0) != 0:
                    continue
                req = int(skin.get("required_level") or 9999)
                if req <= level_now:
                    if self.unlock_skin(int(user_id), skin.get("code")):
                        skins_unlocked.append(str(skin.get("code")))

        # last_reward_level 업데이트
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE users SET last_reward_level = ? WHERE id = ?", (int(level_now), int(user_id)))
            conn.commit()
        finally:
            conn.close()

        # coins_now 재조회(간단)
        updated = self.get_user_by_id(int(user_id)) or {}
        coins_now = int(updated.get("coins") or 0)

        return {
            "level_now": level_now,
            "levels_gained": int(level_now - last_paid),
            "coins_gained": int(coins_gain),
            "coins_now": coins_now,
            "skins_unlocked": skins_unlocked,
        }

    # ========== 리마인더(예약 알림) ==========

    def create_reminder(self, user_id: int, title: str, body: str, due_at: str) -> int:
        """due_at: 'YYYY-MM-DD HH:MM:SS'"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO reminders (user_id, title, body, due_at, is_sent)
                VALUES (?, ?, ?, ?, 0)
                """,
                (int(user_id), title, body, due_at),
            )
            conn.commit()
            return int(cursor.lastrowid or 0)
        finally:
            conn.close()

    def run_due_reminders(self) -> int:
        """
        due_at <= now 인 예약 리마인더를 notifications로 발행하고 is_sent=1 처리.
        - 스케줄러가 없으므로 앱 실행/페이지 진입 시 호출하는 방식
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        sent = 0
        try:
            cursor.execute(
                """
                SELECT id, user_id, title, body
                FROM reminders
                WHERE is_sent = 0
                  AND datetime(due_at) <= datetime('now')
                ORDER BY due_at ASC
                LIMIT 50
                """
            )
            rows = cursor.fetchall()
            for r in rows:
                uid = int(r["user_id"])
                cursor.execute(
                    "INSERT INTO notifications (user_id, title, body, level) VALUES (?, ?, ?, ?)",
                    (uid, r["title"], r["body"], "info"),
                )
                cursor.execute("UPDATE reminders SET is_sent = 1 WHERE id = ?", (int(r["id"]),))
                sent += 1
            conn.commit()
            return sent
        except Exception:
            try:
                conn.commit()
            except Exception:
                pass
            return sent
        finally:
            conn.close()

    def purchase_skin(self, user_id: int, skin_code: str, price: int, required_level: int) -> tuple[bool, str]:
        """스킨 구매(코인 차감 + 해금 + 적용)"""
        user = self.get_user_by_id(int(user_id)) or {}
        coins = int(user.get("coins") or 0)
        xp = 0
        try:
            xp = int(self.get_xp(int(user_id)) or 0)
        except Exception:
            xp = 0
        lvl = self._level_from_xp(xp)
        if lvl < int(required_level or 1):
            return False, f"레벨 {required_level} 이상이 필요해요."
        if coins < int(price or 0):
            return False, "코인이 부족해요."

        # 이미 해금?
        try:
            unlocked = set(self.get_unlocked_skins(int(user_id)))
            if skin_code in unlocked:
                return False, "이미 보유한 스킨이에요."
        except Exception:
            pass

        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE users SET coins = COALESCE(coins,0) - ? WHERE id = ? AND COALESCE(coins,0) >= ?", (int(price), int(user_id), int(price)))
            if cursor.rowcount <= 0:
                conn.commit()
                return False, "코인이 부족해요."
            conn.commit()
        finally:
            conn.close()

        self.unlock_skin(int(user_id), skin_code)
        self.update_user_character_skin_code(int(user_id), skin_code)
        return True, "구매 완료! 스킨을 적용했어요."
    
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
    
    def get_user_by_phone(self, phone_number: str) -> Optional[Dict]:
        """휴대폰번호로 사용자 조회"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            phone_clean = phone_number.replace('-', '').replace(' ', '')
            cursor.execute("SELECT * FROM users WHERE phone_number = ? OR phone_number = ?", (phone_number, phone_clean))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
    
    def get_users_by_phone(self, phone_number: str) -> List[Dict]:
        """휴대폰번호로 모든 사용자 조회 (같은 번호로 여러 계정 가능)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            phone_clean = phone_number.replace('-', '').replace(' ', '')
            cursor.execute("SELECT * FROM users WHERE phone_number = ? OR phone_number = ?", (phone_number, phone_clean))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()
    
    def verify_parent_ssn(self, parent_ssn: str, phone_number: str) -> Optional[Dict]:
        """부모 주민등록번호와 휴대폰번호로 부모 사용자 확인"""
        import hashlib
        parent_ssn_hash = hashlib.sha256(parent_ssn.encode('utf-8')).hexdigest()
        phone_clean = phone_number.replace('-', '').replace(' ', '')
        
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT * FROM users 
                WHERE parent_ssn = ? 
                AND (phone_number = ? OR phone_number = ?)
                AND user_type = 'parent'
                LIMIT 1
            """, (parent_ssn_hash, phone_number, phone_clean))
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
    
    def get_users_by_parent_code_all(self, parent_code: str) -> List[Dict]:
        """부모 코드로 연결된 모든 사용자 조회 (부모 포함)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM users WHERE parent_code = ? ORDER BY name", (parent_code,))
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

    def find_parent_by_invite_code(self, invite_code: str) -> Optional[Dict]:
        """
        자녀 회원가입용: 6자리(부모코드 마지막 6자리) 또는 8자리(전체) 코드로 부모 조회
        - 저장된 parent_code는 8자리(UUID 앞 8)
        """
        code = (invite_code or "").strip().upper()
        if len(code) not in (6, 8):
            return None
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # SQLite: UPPER / SUBSTR 사용
            cursor.execute(
                """
                SELECT *
                FROM users
                WHERE user_type = 'parent'
                  AND (
                        UPPER(parent_code) = ?
                        OR UPPER(SUBSTR(parent_code, -6)) = ?
                  )
                LIMIT 1
                """,
                (code, code),
            )
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
    
    def get_user_conversations_by_date(self, user_id: int) -> List[Dict]:
        """사용자의 날짜별 대화 목록 조회"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT 
                    c.id as conversation_id,
                    DATE(c.created_at) as date,
                    COUNT(m.id) as message_count,
                    MIN(m.timestamp) as first_message_time,
                    MAX(m.timestamp) as last_message_time
                FROM conversations c
                LEFT JOIN messages m ON c.id = m.conversation_id
                WHERE c.user_id = ?
                GROUP BY c.id, DATE(c.created_at)
                ORDER BY c.created_at DESC
            """, (user_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()
    
    def get_conversation_by_id(self, conversation_id: int) -> Optional[Dict]:
        """대화 세션 정보 조회"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT * FROM conversations WHERE id = ?
            """, (conversation_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
    
    def get_all_messages_by_conversation(self, conversation_id: int) -> List[Dict]:
        """대화의 모든 메시지 조회"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT role, content, timestamp
                FROM messages
                WHERE conversation_id = ?
                ORDER BY timestamp ASC
            """, (conversation_id,))
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

    def save_behavior_v2(
        self,
        user_id: int,
        behavior_type: str,
        amount: float = None,
        description: str = None,
        category: str = None,
        related_request_id: int = None,
    ):
        """확장 행동 기록 저장(category/request 연동)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO behaviors (user_id, behavior_type, amount, category, description, related_request_id)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, behavior_type, amount, category, description, related_request_id),
            )
            conn.commit()
            # 자동저축: 용돈(allowance) 발생 시 n%를 저축으로 자동 기록
            try:
                if str(behavior_type or "").strip() == "allowance" and float(amount or 0) > 0:
                    stg = self.get_auto_saving_setting(int(user_id))
                    if stg and int(stg.get("is_active") or 0) == 1:
                        pct = int(stg.get("percent") or 0)
                        if pct > 0:
                            save_amt = int(round(float(amount) * (pct / 100.0)))
                            if save_amt > 0:
                                cursor.execute(
                                    """
                                    INSERT INTO behaviors (user_id, behavior_type, amount, category, description, related_request_id)
                                    VALUES (?, 'saving', ?, ?, ?, ?)
                                    """,
                                    (int(user_id), float(save_amt), "자동저축", f"자동저축 {pct}%", None),
                                )
                                conn.commit()
            except Exception:
                pass
        finally:
            conn.close()

    # ========== 자동저축 ==========

    def get_auto_saving_setting(self, user_id: int) -> Optional[Dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM auto_saving_settings WHERE user_id = ? LIMIT 1", (int(user_id),))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def set_auto_saving_setting(self, user_id: int, percent: int, is_active: bool) -> bool:
        percent = max(0, min(100, int(percent or 0)))
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO auto_saving_settings (user_id, percent, is_active, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                    percent = excluded.percent,
                    is_active = excluded.is_active,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (int(user_id), int(percent), 1 if is_active else 0),
            )
            conn.commit()
            return True
        finally:
            conn.close()

    def try_grant_autosave_weekly_bonus(self, user_id: int, bonus_coins: int = 20) -> tuple[bool, str]:
        """
        자동저축 주간 보상(간단 버전)
        - 지난 주(월~일) 기준
        - 해당 주에 용돈(allowance)이 1건 이상 있었고
        - 자동저축(category='자동저축') 합계가 예상치(allowance*percent) 이상이면
        - 아직 해당 week_key로 보상을 안 받았을 때 코인 지급
        """
        stg = self.get_auto_saving_setting(int(user_id)) or {}
        if int(stg.get("is_active") or 0) != 1:
            return False, "자동저축이 꺼져 있어요."
        pct = int(stg.get("percent") or 0)
        if pct <= 0:
            return False, "자동저축 비율이 0%예요."

        today = _date.today()
        # 이번 주 월요일
        this_monday = today - _timedelta(days=today.weekday())
        # 지난 주 월~일
        last_monday = this_monday - _timedelta(days=7)
        last_sunday = this_monday - _timedelta(days=1)
        iso = last_monday.isocalendar()
        week_key = f"{iso.year}-W{int(iso.week):02d}"

        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # 이미 보상 받았나?
            cursor.execute(
                "SELECT 1 FROM auto_saving_weekly_rewards WHERE user_id = ? AND week_key = ? LIMIT 1",
                (int(user_id), week_key),
            )
            if cursor.fetchone():
                return False, "이미 지난주 보상을 받았어요."

            start = last_monday.isoformat()
            end = last_sunday.isoformat()

            cursor.execute(
                """
                SELECT COALESCE(SUM(amount),0) as s
                FROM behaviors
                WHERE user_id = ?
                  AND behavior_type = 'allowance'
                  AND date(timestamp) BETWEEN ? AND ?
                """,
                (int(user_id), start, end),
            )
            allow_sum = float((cursor.fetchone() or {}).get("s") or 0)
            if allow_sum <= 0:
                return False, "지난주에 받은 용돈이 없어서 보상이 없어요."

            cursor.execute(
                """
                SELECT COALESCE(SUM(amount),0) as s
                FROM behaviors
                WHERE user_id = ?
                  AND behavior_type = 'saving'
                  AND COALESCE(category,'') = '자동저축'
                  AND date(timestamp) BETWEEN ? AND ?
                """,
                (int(user_id), start, end),
            )
            auto_save_sum = float((cursor.fetchone() or {}).get("s") or 0)
            expected = allow_sum * (pct / 100.0)
            if auto_save_sum + 0.0001 < expected:
                return False, "지난주 자동저축 달성이 부족해요."

            # 보상 지급(코인)
            cursor.execute(
                "UPDATE users SET coins = COALESCE(coins,0) + ? WHERE id = ?",
                (int(bonus_coins), int(user_id)),
            )
            cursor.execute(
                "INSERT INTO auto_saving_weekly_rewards (user_id, week_key) VALUES (?, ?)",
                (int(user_id), week_key),
            )
            cursor.execute(
                "INSERT INTO notifications (user_id, title, body, level) VALUES (?, ?, ?, ?)",
                (int(user_id), "주간 자동저축 보상! 🪙", f"지난주 자동저축 달성으로 코인 +{int(bonus_coins)}", "success"),
            )
            conn.commit()
            return True, f"지난주 보상으로 코인 +{int(bonus_coins)} 지급!"
        except Exception:
            try:
                conn.commit()
            except Exception:
                pass
            return False, "보상 처리에 실패했어요."
        finally:
            conn.close()

    # ========== 챌린지 ==========

    def create_challenge_template(
        self,
        parent_code: str | None,
        title: str,
        challenge_type: str,
        params: dict | None = None,
        reward_amount: float = 0,
        reward_coins: int = 0,
        created_by: int | None = None,
    ) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO challenge_templates (parent_code, title, challenge_type, params_json, reward_amount, reward_coins, created_by, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    parent_code,
                    str(title or "").strip(),
                    str(challenge_type or "").strip(),
                    _json.dumps(params or {}, ensure_ascii=False),
                    float(reward_amount or 0),
                    int(reward_coins or 0),
                    int(created_by) if created_by is not None else None,
                ),
            )
            conn.commit()
            return int(cursor.lastrowid or 0)
        finally:
            conn.close()

    def start_challenge(self, user_id: int, template_id: int, start_date: str, end_date: str) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO challenge_instances (user_id, template_id, start_date, end_date, status)
                VALUES (?, ?, ?, ?, 'active')
                """,
                (int(user_id), int(template_id), str(start_date), str(end_date)),
            )
            conn.commit()
            return int(cursor.lastrowid or 0)
        finally:
            conn.close()

    def get_challenge_instances(self, user_id: int, status: str | None = None, limit: int = 50) -> list[Dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            q = """
                SELECT i.*, t.title as template_title, t.challenge_type, t.params_json, t.reward_amount, t.reward_coins
                FROM challenge_instances i
                JOIN challenge_templates t ON t.id = i.template_id
                WHERE i.user_id = ?
            """
            params: list = [int(user_id)]
            if status:
                q += " AND i.status = ?"
                params.append(str(status))
            q += " ORDER BY i.created_at DESC LIMIT ?"
            params.append(int(limit))
            cursor.execute(q, params)
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def create_challenge_checkin(self, instance_id: int, checkin_date: str, value: float = 1.0, note: str | None = None) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO challenge_checkins (instance_id, checkin_date, value, note)
                VALUES (?, ?, ?, ?)
                """,
                (int(instance_id), str(checkin_date), float(value or 0), note),
            )
            conn.commit()
            return True
        finally:
            conn.close()

    def _sum_spend_in_range(self, user_id: int, start_date: str, end_date: str, category: str | None = None) -> float:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            q = """
                SELECT COALESCE(SUM(amount),0) as s
                FROM behaviors
                WHERE user_id = ?
                  AND behavior_type IN ('planned_spending','impulse_buying','spend')
                  AND date(timestamp) BETWEEN ? AND ?
            """
            params = [int(user_id), str(start_date), str(end_date)]
            if category:
                q += " AND COALESCE(category,'') = ?"
                params.append(str(category))
            cursor.execute(q, params)
            return float((cursor.fetchone() or {}).get("s") or 0)
        finally:
            conn.close()

    def _sum_saving_on_date(self, user_id: int, day: str) -> float:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT COALESCE(SUM(amount),0) as s
                FROM behaviors
                WHERE user_id = ?
                  AND behavior_type = 'saving'
                  AND date(timestamp) = ?
                """,
                (int(user_id), str(day)),
            )
            return float((cursor.fetchone() or {}).get("s") or 0)
        finally:
            conn.close()

    def compute_challenge_progress(self, inst: Dict) -> Dict:
        """
        inst: get_challenge_instances()의 row(dict)
        return: {"progress":0~1, "summary":str, "can_finalize":bool, "is_success":bool|None}
        """
        ctype = str(inst.get("challenge_type") or "").strip()
        start_date = str(inst.get("start_date") or "")
        end_date = str(inst.get("end_date") or "")
        params = {}
        try:
            params = _json.loads(inst.get("params_json") or "{}") or {}
        except Exception:
            params = {}

        uid = int(inst.get("user_id"))
        today = _date.today().isoformat()
        can_finalize = today > end_date

        if ctype == "spend_cap":
            cap = float(params.get("cap_amount") or 0)
            spent = self._sum_spend_in_range(uid, start_date, min(today, end_date))
            prog = 0.0 if cap <= 0 else min(1.0, spent / cap)
            remaining = cap - spent
            is_success = None
            if can_finalize:
                total = self._sum_spend_in_range(uid, start_date, end_date)
                is_success = bool(total <= cap)
            return {
                "progress": float(prog),
                "summary": f"소비 {int(spent):,}원 / 목표 {int(cap):,}원 · 남은 {int(max(0, remaining)):,}원",
                "can_finalize": bool(can_finalize),
                "is_success": is_success,
            }

        if ctype == "reduce_category":
            cat = str(params.get("category") or "").strip()
            baseline = float(params.get("baseline_amount") or 0)
            pct = float(params.get("reduction_pct") or 10)
            target = baseline * (1.0 - (pct / 100.0))
            cur = self._sum_spend_in_range(uid, start_date, min(today, end_date), category=cat or None)
            prog = 0.0 if target <= 0 else min(1.0, cur / target)
            is_success = None
            if can_finalize:
                total = self._sum_spend_in_range(uid, start_date, end_date, category=cat or None)
                is_success = bool(total <= target)
            label = cat or "카테고리"
            return {
                "progress": float(prog),
                "summary": f"{label} 소비 {int(cur):,}원 / 목표 {int(target):,}원(기준 {int(baseline):,}원 대비 {int(pct)}%↓)",
                "can_finalize": bool(can_finalize),
                "is_success": is_success,
            }

        if ctype in ("daily_save_fixed", "daily_save_increasing"):
            try:
                s = _date.fromisoformat(start_date)
                e = _date.fromisoformat(end_date)
            except Exception:
                return {"progress": 0.0, "summary": "기간 정보가 올바르지 않아요.", "can_finalize": False, "is_success": None}

            days_total = max(1, (e - s).days + 1)
            met = 0
            required_today = 0
            for i in range(days_total):
                d = (s + _timedelta(days=i)).isoformat()
                if d > today:
                    continue
                saved = self._sum_saving_on_date(uid, d)
                if ctype == "daily_save_fixed":
                    req = float(params.get("daily_amount") or 0)
                else:
                    start_amt = float(params.get("start_amount") or 500)
                    inc = float(params.get("daily_increment") or 100)
                    req = start_amt + inc * i
                if d == today:
                    required_today = int(req)
                if saved >= req and req > 0:
                    met += 1

            prog = min(1.0, met / float(days_total))
            is_success = None
            if can_finalize:
                # 모든 날짜 충족했는지 재평가(전체)
                met_all = 0
                for i in range(days_total):
                    d = (s + _timedelta(days=i)).isoformat()
                    saved = self._sum_saving_on_date(uid, d)
                    if ctype == "daily_save_fixed":
                        req = float(params.get("daily_amount") or 0)
                    else:
                        start_amt = float(params.get("start_amount") or 500)
                        inc = float(params.get("daily_increment") or 100)
                        req = start_amt + inc * i
                    if saved >= req and req > 0:
                        met_all += 1
                is_success = bool(met_all >= days_total)

            title = "하루 저축" if ctype == "daily_save_fixed" else "점점 늘리는 저축"
            return {
                "progress": float(prog),
                "summary": f"{title} · 달성 {met}/{days_total}일 (오늘 목표 {int(required_today):,}원)",
                "can_finalize": bool(can_finalize),
                "is_success": is_success,
            }

        if ctype == "habit_custom":
            target = int(params.get("target_count") or 7)
            conn = self._get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """
                    SELECT COUNT(*) as cnt
                    FROM challenge_checkins c
                    WHERE c.instance_id = ?
                      AND c.checkin_date BETWEEN ? AND ?
                    """,
                    (int(inst.get("id")), start_date, min(today, end_date)),
                )
                cnt = int((cursor.fetchone() or {}).get("cnt") or 0)
            finally:
                conn.close()
            prog = 0.0 if target <= 0 else min(1.0, cnt / float(target))
            is_success = None
            if can_finalize:
                is_success = bool(cnt >= target)
            return {
                "progress": float(prog),
                "summary": f"체크 {cnt}/{target}회",
                "can_finalize": bool(can_finalize),
                "is_success": is_success,
            }

        return {"progress": 0.0, "summary": "지원되지 않는 챌린지 타입이에요.", "can_finalize": False, "is_success": None}

    def finalize_challenge_if_due(self, instance_id: int) -> Optional[Dict]:
        """기간 종료 후 정산(완료/실패 처리 + 보상 지급)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT i.*, t.title as template_title, t.challenge_type, t.params_json, t.reward_amount, t.reward_coins
                FROM challenge_instances i
                JOIN challenge_templates t ON t.id = i.template_id
                WHERE i.id = ?
                LIMIT 1
                """,
                (int(instance_id),),
            )
            row = cursor.fetchone()
            if not row:
                return None
            inst = dict(row)
            if str(inst.get("status")) != "active":
                return inst

            prog = self.compute_challenge_progress(inst)
            if not prog.get("can_finalize"):
                return inst
            is_success = prog.get("is_success")
            if is_success is None:
                return inst

            new_status = "completed" if is_success else "failed"
            cursor.execute(
                "UPDATE challenge_instances SET status = ?, completed_at = CURRENT_TIMESTAMP WHERE id = ?",
                (new_status, int(instance_id)),
            )
            # 보상 지급(성공 시)
            if is_success:
                r_amount = float(inst.get("reward_amount") or 0)
                r_coins = int(inst.get("reward_coins") or 0)
                uid = int(inst.get("user_id"))
                if r_amount > 0:
                    cursor.execute(
                        """
                        INSERT INTO behaviors (user_id, behavior_type, amount, category, description)
                        VALUES (?, 'allowance', ?, '챌린지', ?)
                        """,
                        (uid, float(r_amount), f"챌린지 보상: {inst.get('template_title') or ''}"),
                    )
                if r_coins > 0:
                    cursor.execute("UPDATE users SET coins = COALESCE(coins,0) + ? WHERE id = ?", (r_coins, uid))
                cursor.execute(
                    "INSERT INTO notifications (user_id, title, body, level) VALUES (?, ?, ?, ?)",
                    (uid, "챌린지 성공! 🎉", f"{inst.get('template_title')} 보상을 받았어요!", "success"),
                )
            conn.commit()
            inst["status"] = new_status
            return inst
        finally:
            conn.close()

    # ========== 요청(아이→부모) ==========

    def create_request(
        self,
        child_id: int,
        parent_code: str,
        request_type: str,
        amount: float,
        category: str = None,
        reason: str = None,
    ) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO requests (child_id, parent_code, request_type, amount, category, reason)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (child_id, parent_code, request_type, amount, category, reason),
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_requests_for_parent(self, parent_code: str, status: str = "pending"):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT r.*, u.name as child_name, u.username as child_username
                FROM requests r
                JOIN users u ON r.child_id = u.id
                WHERE r.parent_code = ? AND r.status = ?
                ORDER BY r.created_at DESC
                """,
                (parent_code, status),
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def get_requests_for_child(self, child_id: int, limit: int = 50):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT *
                FROM requests
                WHERE child_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (child_id, limit),
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def decide_request(self, request_id: int, decided_by: int, status: str):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE requests
                SET status = ?, decided_by = ?, decided_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (status, decided_by, request_id),
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    # ========== 정기 용돈 ==========

    def create_recurring_allowance(
        self,
        parent_id: int,
        child_id: int,
        amount: float,
        frequency: str,
        day_of_week: int = None,
        day_of_month: int = None,
        next_run: str = None,
        memo: str = None,
    ) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO recurring_allowances
                (parent_id, child_id, amount, frequency, day_of_week, day_of_month, next_run, memo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (parent_id, child_id, amount, frequency, day_of_week, day_of_month, next_run, memo),
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_recurring_allowances(self, parent_id: int):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT ra.*, u.name as child_name, u.username as child_username
                FROM recurring_allowances ra
                JOIN users u ON ra.child_id = u.id
                WHERE ra.parent_id = ?
                ORDER BY ra.created_at DESC
                """,
                (parent_id,),
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def set_recurring_allowance_active(self, recurring_id: int, is_active: bool):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE recurring_allowances SET is_active = ? WHERE id = ?",
                (1 if is_active else 0, recurring_id),
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    # ========== 목표 ==========

    def create_goal(self, user_id: int, title: str, target_amount: float) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO goals (user_id, title, target_amount)
                VALUES (?, ?, ?)
                """,
                (user_id, title, target_amount),
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_goals(self, user_id: int, active_only: bool = False):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            if active_only:
                cursor.execute(
                    "SELECT * FROM goals WHERE user_id = ? AND is_active = 1 ORDER BY created_at DESC",
                    (user_id,),
                )
            else:
                cursor.execute(
                    "SELECT * FROM goals WHERE user_id = ? ORDER BY created_at DESC",
                    (user_id,),
                )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def add_goal_contribution(self, goal_id: int, amount: float, note: str = None) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO goal_contributions (goal_id, amount, note) VALUES (?, ?, ?)",
                (goal_id, amount, note),
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_goal_progress(self, goal_id: int) -> float:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT SUM(amount) as total FROM goal_contributions WHERE goal_id = ?", (goal_id,))
            row = cursor.fetchone()
            return float(row["total"] or 0)
        finally:
            conn.close()

    def set_goal_active(self, goal_id: int, is_active: bool):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE goals SET is_active = ? WHERE id = ?", (1 if is_active else 0, goal_id))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    # ========== 알림 ==========

    def create_notification(self, user_id: int, title: str, body: str = None, level: str = "info") -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO notifications (user_id, title, body, level) VALUES (?, ?, ?, ?)",
                (user_id, title, body, level),
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_notifications(self, user_id: int, unread_only: bool = True, limit: int = 20):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            if unread_only:
                cursor.execute(
                    """
                    SELECT * FROM notifications
                    WHERE user_id = ? AND is_read = 0
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (user_id, limit),
                )
            else:
                cursor.execute(
                    """
                    SELECT * FROM notifications
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (user_id, limit),
                )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def mark_notification_read(self, notification_id: int) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE notifications SET is_read = 1 WHERE id = ?", (notification_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    # ========== 정기 용돈 자동 실행 ==========

    def _next_run_for_recurring(self, row: Dict, today: _date) -> _date:
        freq = row.get("frequency")
        if freq == "weekly":
            dow = int(row.get("day_of_week") or 0)  # 0=월..6=일
            delta = (dow - today.weekday()) % 7
            if delta == 0:
                delta = 7
            return today + _timedelta(days=delta)
        # monthly
        dom = int(row.get("day_of_month") or 1)
        y, m = today.year, today.month
        # pick this month if in future, else next month
        def _safe_date(yy, mm, dd):
            # clamp day
            if mm == 2:
                dd = min(dd, 28)
            elif mm in (4, 6, 9, 11):
                dd = min(dd, 30)
            else:
                dd = min(dd, 31)
            return _date(yy, mm, dd)
        cand = _safe_date(y, m, dom)
        if cand > today:
            return cand
        if m == 12:
            y, m = y + 1, 1
        else:
            m += 1
        return _safe_date(y, m, dom)

    def run_due_recurring_allowances(self) -> int:
        """
        정기 용돈: next_run <= today 인 항목을 자동 지급.
        - 스케줄러가 없으므로 앱 실행/페이지 진입 시 호출하는 방식
        - 지급 후 next_run 갱신
        """
        today = _date.today()
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT ra.*, u.name as child_name
                FROM recurring_allowances ra
                JOIN users u ON ra.child_id = u.id
                WHERE ra.is_active = 1
                  AND ra.next_run IS NOT NULL
                  AND date(ra.next_run) <= date('now')
                ORDER BY ra.next_run ASC
                """
            )
            due = [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()

        processed = 0
        for r in due:
            rid = int(r["id"])
            child_id = int(r["child_id"])
            amount = float(r.get("amount") or 0)
            freq = r.get("frequency")
            memo = r.get("memo") or ""

            # 지급 기록 + 알림
            self.save_behavior_v2(
                child_id,
                "allowance",
                amount,
                description=f"정기 용돈 지급({('매주' if freq=='weekly' else '매월')}) {memo}".strip(),
                category="정기용돈",
            )
            self.create_notification(child_id, "정기 용돈이 들어왔어요!", f"{int(amount):,}원을 받았어요.", level="success")

            # next_run 갱신
            try:
                next_run = self._next_run_for_recurring(r, today)
            except Exception:
                next_run = today + _timedelta(days=7)

            conn2 = self._get_connection()
            cur2 = conn2.cursor()
            try:
                cur2.execute("UPDATE recurring_allowances SET next_run = ? WHERE id = ?", (next_run.isoformat(), rid))
                conn2.commit()
            finally:
                conn2.close()

            processed += 1

        return processed
    
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

    # ========== 홈 통계 ==========

    def get_children_monthly_savings(self, parent_code: str) -> List[Dict]:
        """부모 코드로 연결된 모든 자녀의 최근 6개월간 월별 저축 합계 조회"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT 
                    strftime('%m', b.timestamp) as month,
                    SUM(b.amount) as total_amount
                FROM behaviors b
                JOIN users u ON b.user_id = u.id
                WHERE u.parent_code = ? 
                AND u.user_type = 'child'
                AND b.behavior_type = 'saving'
                AND b.timestamp >= date('now', '-6 months')
                GROUP BY month
                ORDER BY month ASC
            """, (parent_code,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def get_children_behavior_stats_this_month(self, parent_code: str) -> Dict:
        """이번 달 자녀들의 금융 활동 통계 조회"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # 이번 달 저축 총액, 어제 저축액, 현재 잔액(가상)
            cursor.execute("""
                SELECT 
                    SUM(CASE WHEN behavior_type = 'saving' THEN amount ELSE 0 END) as monthly_total,
                    SUM(CASE WHEN behavior_type = 'saving' AND date(timestamp) = date('now', '-1 day') THEN amount ELSE 0 END) as yesterday_total
                FROM behaviors b
                JOIN users u ON b.user_id = u.id
                WHERE u.parent_code = ? 
                AND u.user_type = 'child'
                AND strftime('%m', b.timestamp) = strftime('%m', 'now')
                AND strftime('%Y', b.timestamp) = strftime('%Y', 'now')
            """, (parent_code,))
            row = cursor.fetchone()
            return dict(row) if row else {"monthly_total": 0, "yesterday_total": 0}
        finally:
            conn.close()

    def get_child_stats(self, user_id: int) -> Dict:
        """개별 자녀의 통계 정보 조회"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT 
                    COUNT(*) as activity_count,
                    SUM(CASE WHEN behavior_type = 'saving' THEN amount ELSE 0 END) as total_savings
                FROM behaviors
                WHERE user_id = ?
            """, (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else {"activity_count": 0, "total_savings": 0}
        finally:
            conn.close()
