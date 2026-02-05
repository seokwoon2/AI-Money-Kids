from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, Iterator, Optional

from database.db_manager import DatabaseManager


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


class _DbFacade:
    def __init__(self):
        self._dbm = DatabaseManager()
        self.emotions = _EmotionsCollection(self._dbm)


def get_db() -> _DbFacade:
    """
    MongoDB(pymongo)처럼 보이는 API를 제공합니다.

    - get_db().emotions.count_documents({...})
    - get_db().emotions.insert_one({...})
    - get_db().emotions.find({...}).sort(...).limit(...)

    내부 구현은 기존 SQLite(emotion_logs 테이블)를 사용합니다.
    """
    return _DbFacade()

