import uuid
from database.db_manager import DatabaseManager
import bcrypt

def generate_parent_code() -> str:
    """부모 코드 생성 (UUID)"""
    return str(uuid.uuid4())[:8].upper()

def validate_parent_code(parent_code: str) -> bool:
    """부모 코드 유효성 검증"""
    # 부모 코드(8자리) 또는 초대용 축약 코드(마지막 6자리) 허용
    if not parent_code or len(parent_code) not in (6, 8):
        return False
    return True


def hash_password(password: str) -> str:
    """
    비밀번호 해시(bcrypt).
    - DB 저장용으로 문자열 hash를 반환합니다.
    """
    p = str(password or "")
    return bcrypt.hashpw(p.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """
    bcrypt 비밀번호 검증.
    """
    try:
        return bcrypt.checkpw(str(password or "").encode("utf-8"), str(password_hash or "").encode("utf-8"))
    except Exception:
        return False
