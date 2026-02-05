from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, Iterator, Optional

from database.db_manager import DatabaseManager
from utils.auth import generate_parent_code, hash_password


def _to_sqlite_ts(dt: Any) -> str:
    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return str(dt or "").strip()


def _from_sqlite_ts(s: Any) -> datetime:
    raw = str(s or "").strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
        try:
            return datetime.strptime(raw, fmt)
        except Exception:
            pass
    try:
        return datetime.fromisoformat(raw)
    except Exception:
        return datetime.min


@dataclass
class _InsertOneResult:
    inserted_id: int


class _EmotionsQuery:
    def __init__(self, dbm: DatabaseManager, filt: Dict[str, Any]):
        self._dbm = dbm
        self._filt = filt or {}
        self._sort_field = "created_at"
        self._sort_dir = -1
        self._limit: Optional[int] = None

    def sort(self, field: str, direction: int):
        self._sort_field = str(field or "created_at")
        self._sort_dir = int(direction or -1)
        return self

    def limit(self, n: int):
        self._limit = int(n) if n is not None else None
        return self

    def __iter__(self) -> Iterator[Dict[str, Any]]:
        user_id = int(self._filt.get("user_id") or 0)
        if not user_id:
            return iter(())

        # filters
        emo_in = None
        if isinstance(self._filt.get("emotion"), dict) and "$in" in self._filt["emotion"]:
            emo_in = list(self._filt["emotion"]["$in"] or [])
        elif isinstance(self._filt.get("emotion"), str):
            emo_in = [self._filt["emotion"]]

        created_gte = None
        if isinstance(self._filt.get("created_at"), dict) and "$gte" in self._filt["created_at"]:
            created_gte = self._filt["created_at"]["$gte"]

        where = ["user_id = ?"]
        params: list[Any] = [user_id]

        if emo_in:
            where.append("emotion IN ({})".format(",".join(["?"] * len(emo_in))))
            params.extend([str(x) for x in emo_in])

        if created_gte:
            where.append("datetime(created_at) >= datetime(?)")
            params.append(_to_sqlite_ts(created_gte))

        order_dir = "DESC" if self._sort_dir < 0 else "ASC"
        order_by = "datetime(created_at) " + order_dir if self._sort_field == "created_at" else "datetime(created_at) " + order_dir

        sql = f"""
        SELECT id, user_id, context, emotion, note, created_at
        FROM emotion_logs
        WHERE {' AND '.join(where)}
        ORDER BY {order_by}
        """
        if self._limit is not None:
            sql += " LIMIT ?"
            params.append(int(self._limit))

        conn = self._dbm._get_connection()  # pylint: disable=protected-access
        cur = conn.cursor()
        try:
            cur.execute(sql, tuple(params))
            rows = cur.fetchall() or []
            for r in rows:
                # sqlite3.Row or tuple
                if isinstance(r, (tuple, list)):
                    _id, uid, ctx, emo, note, created_at = r
                else:
                    _id = r["id"]
                    uid = r["user_id"]
                    ctx = r["context"]
                    emo = r["emotion"]
                    note = r["note"]
                    created_at = r["created_at"]
                yield {
                    "_id": int(_id or 0),
                    "user_id": int(uid or 0),
                    "type": str(ctx or ""),
                    "emotion": str(emo or ""),
                    "memo": str(note or ""),
                    "created_at": _from_sqlite_ts(created_at),
                }
        finally:
            conn.close()


class _EmotionsCollection:
    def __init__(self, dbm: DatabaseManager):
        self._dbm = dbm

    def count_documents(self, filt: Dict[str, Any]) -> int:
        filt = filt or {}
        user_id = int(filt.get("user_id") or 0)
        if not user_id:
            return 0

        emo_in = None
        if isinstance(filt.get("emotion"), dict) and "$in" in filt["emotion"]:
            emo_in = list(filt["emotion"]["$in"] or [])
        elif isinstance(filt.get("emotion"), str):
            emo_in = [filt["emotion"]]

        created_gte = None
        if isinstance(filt.get("created_at"), dict) and "$gte" in filt["created_at"]:
            created_gte = filt["created_at"]["$gte"]

        where = ["user_id = ?"]
        params: list[Any] = [user_id]

        if emo_in:
            where.append("emotion IN ({})".format(",".join(["?"] * len(emo_in))))
            params.extend([str(x) for x in emo_in])

        if created_gte:
            where.append("datetime(created_at) >= datetime(?)")
            params.append(_to_sqlite_ts(created_gte))

        sql = f"SELECT COUNT(*) AS cnt FROM emotion_logs WHERE {' AND '.join(where)}"
        conn = self._dbm._get_connection()  # pylint: disable=protected-access
        cur = conn.cursor()
        try:
            cur.execute(sql, tuple(params))
            row = cur.fetchone()
            if not row:
                return 0
            try:
                return int(row["cnt"] or 0)
            except Exception:
                return int((row[0] if isinstance(row, (tuple, list)) else 0) or 0)
        finally:
            conn.close()

    def insert_one(self, doc: Dict[str, Any]) -> _InsertOneResult:
        doc = doc or {}
        user_id = int(doc.get("user_id") or 0)
        ctx = str(doc.get("type") or "").strip()
        emo = str(doc.get("emotion") or "").strip()
        memo = (doc.get("memo") or "").strip() or None
        created_at = doc.get("created_at") or datetime.now()
        created_s = _to_sqlite_ts(created_at)

        conn = self._dbm._get_connection()  # pylint: disable=protected-access
        cur = conn.cursor()
        try:
            cur.execute(
                """
                INSERT INTO emotion_logs (user_id, context, emotion, note, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, ctx, emo, memo, created_s),
            )
            conn.commit()
            return _InsertOneResult(inserted_id=int(cur.lastrowid or 0))
        finally:
            conn.close()

    def find(self, filt: Dict[str, Any]) -> _EmotionsQuery:
        return _EmotionsQuery(self._dbm, filt or {})


class _UsersCollection:
    """
    MongoDB(pymongo) 스타일의 users 컬렉션 API를 흉내냅니다.
    내부 구현은 기존 SQLite(users 테이블)입니다.
    """

    def __init__(self, dbm: DatabaseManager):
        self._dbm = dbm

    def find_one(self, filt: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        filt = filt or {}

        username = filt.get("username")
        if username:
            try:
                row = self._dbm.get_user_by_username(str(username))
                if not row:
                    return None
                d = dict(row)
                d["_id"] = int(d.get("id") or 0)
                return d
            except Exception:
                return None

        # Mongo 예시 호환: 부모 초대코드(invite_code)로 parent 검색
        # 현재 앱은 users.parent_code(8자리) + 마지막 6자리로도 검색합니다.
        if filt.get("user_type") == "parent" and filt.get("invite_code"):
            code = str(filt.get("invite_code") or "").strip().upper()
            if not code:
                return None
            try:
                row = self._dbm.find_parent_by_invite_code(code) if hasattr(self._dbm, "find_parent_by_invite_code") else None
                if not row:
                    return None
                d = dict(row)
                d["_id"] = int(d.get("id") or 0)
                return d
            except Exception:
                return None

        return None

    def insert_one(self, doc: Dict[str, Any]) -> _InsertOneResult:
        doc = doc or {}

        username = str(doc.get("username") or "").strip()
        name = str(doc.get("name") or "").strip()
        user_type = str(doc.get("user_type") or "child").strip().lower()
        if user_type in ("부모", "부모님", "parent", "guardian"):
            user_type = "parent"
        elif user_type in ("아이", "자녀", "child", "kid"):
            user_type = "child"
        if user_type not in ("parent", "child"):
            user_type = "child"

        # 비밀번호: doc['password']가 bcrypt hash면 그대로 저장, 아니면 해싱
        pw = doc.get("password") or ""
        pw_s = str(pw)
        if pw_s.startswith("$2a$") or pw_s.startswith("$2b$") or pw_s.startswith("$2y$"):
            password_hash = pw_s
        else:
            password_hash = hash_password(pw_s)

        # ✅ 이 앱의 DB 구조: parent_code 필수
        parent_code = str(doc.get("parent_code") or "").strip().upper()
        if user_type == "parent":
            parent_code = parent_code or generate_parent_code()
        else:
            parent_id = doc.get("parent_id")
            if parent_id:
                # parent_id를 받았으면, 찾아서 parent_code로 변환
                try:
                    p = self._dbm.get_user_by_id(int(parent_id))
                    parent_code = str((p or {}).get("parent_code") or "").strip().upper()
                except Exception:
                    parent_code = parent_code or ""
            if not parent_code:
                # child는 반드시 parent_code가 필요(연동)
                parent_code = "UNKNOWN"

        # 중복 방지(최종 방어)
        existing = None
        try:
            existing = self._dbm.get_user_by_username(username)
        except Exception:
            existing = None
        if existing:
            raise ValueError("이미 사용 중인 아이디입니다")

        # sqlite 직접 insert(users)
        conn = self._dbm._get_connection()  # pylint: disable=protected-access
        cur = conn.cursor()
        try:
            cur.execute(
                """
                INSERT INTO users (username, password_hash, name, age, parent_code, user_type, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    username,
                    password_hash,
                    name,
                    None,
                    parent_code,
                    user_type,
                    _to_sqlite_ts(doc.get("created_at") or datetime.now()),
                ),
            )
            conn.commit()
            return _InsertOneResult(inserted_id=int(cur.lastrowid or 0))
        finally:
            conn.close()

    def update_one(self, filt: Dict[str, Any], update: Dict[str, Any]) -> int:
        """
        최소 구현: 현재 프로젝트에서는 회원가입에서만 간단히 사용 가능하도록 제공.
        return: modified_count(대략)
        """
        filt = filt or {}
        update = update or {}
        _id = filt.get("_id") or filt.get("id")
        if not _id:
            return 0
        # $set만 지원
        set_obj = update.get("$set") if isinstance(update.get("$set"), dict) else {}
        if not set_obj:
            return 0

        cols = []
        params: list[Any] = []
        for k, v in set_obj.items():
            if k not in ("name", "phone_number", "birth_date", "parent_code"):
                continue
            cols.append(f"{k} = ?")
            params.append(v)
        if not cols:
            return 0

        params.append(int(_id))
        conn = self._dbm._get_connection()  # pylint: disable=protected-access
        cur = conn.cursor()
        try:
            cur.execute(f"UPDATE users SET {', '.join(cols)} WHERE id = ?", tuple(params))
            conn.commit()
            return int(cur.rowcount or 0)
        finally:
            conn.close()


class _DbFacade:
    def __init__(self):
        self._dbm = DatabaseManager()
        self.emotions = _EmotionsCollection(self._dbm)
        self.users = _UsersCollection(self._dbm)


def get_db() -> _DbFacade:
    """
    MongoDB(pymongo)처럼 보이는 API를 제공합니다.

    - get_db().emotions.count_documents({...})
    - get_db().emotions.insert_one({...})
    - get_db().emotions.find({...}).sort(...).limit(...)

    내부 구현은 기존 SQLite(emotion_logs 테이블)를 사용합니다.
    """
    return _DbFacade()


def get_database() -> _DbFacade:
    """
    문서/템플릿 코드 호환용 별칭.
    - get_database().users.find_one(...)
    - get_database().users.insert_one(...)
    """
    return get_db()

