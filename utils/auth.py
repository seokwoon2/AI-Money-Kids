import uuid
from database.db_manager import DatabaseManager

def generate_parent_code() -> str:
    """부모 코드 생성 (UUID)"""
    return str(uuid.uuid4())[:8].upper()

def validate_parent_code(parent_code: str) -> bool:
    """부모 코드 유효성 검증"""
    if not parent_code or len(parent_code) != 8:
        return False
    return True
