import uuid
from database.db_manager import DatabaseManager

def generate_parent_code() -> str:
    """부모 코드 생성 (UUID)"""
    return str(uuid.uuid4())[:8].upper()

def validate_parent_code(parent_code: str) -> bool:
    """부모 코드 유효성 검증"""
    # 부모 코드(8자리) 또는 초대용 축약 코드(마지막 6자리) 허용
    if not parent_code or len(parent_code) not in (6, 8):
        return False
    return True
