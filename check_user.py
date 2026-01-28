"""사용자 계정 확인 스크립트"""
from database.db_manager import DatabaseManager

db = DatabaseManager()

# seokwoon 계정 확인
seokwoon_user = db.get_user_by_username("seokwoon")

if seokwoon_user:
    print(f"✅ seokwoon 계정을 찾았습니다!")
    print(f"   ID: {seokwoon_user['id']}")
    print(f"   이름: {seokwoon_user['name']}")
    print(f"   사용자명: {seokwoon_user['username']}")
    print(f"   현재 타입: {seokwoon_user.get('user_type', 'child')}")
    print(f"   부모 코드: {seokwoon_user.get('parent_code', 'N/A')}")
    print(f"   나이: {seokwoon_user.get('age', 'N/A')}")
    
    # 타입이 child인 경우 parent로 변경
    if seokwoon_user.get('user_type', 'child') == 'child':
        print("\n⚠️  현재 타입이 'child'입니다. 'parent'로 변경하시겠습니까?")
        response = input("변경하려면 'yes'를 입력하세요: ")
        if response.lower() == 'yes':
            if db.update_user_type(seokwoon_user['id'], 'parent'):
                print("✅ 계정 타입이 'parent'로 변경되었습니다!")
            else:
                print("❌ 계정 타입 변경에 실패했습니다.")
        else:
            print("변경이 취소되었습니다.")
    else:
        print("\n✅ 계정 타입이 이미 'parent'로 설정되어 있습니다.")
else:
    print("❌ seokwoon 계정을 찾을 수 없습니다.")
    
    # 모든 사용자 목록 출력
    print("\n📋 등록된 모든 사용자:")
    all_users = db.get_all_users()
    for u in all_users:
        print(f"   - {u['username']} ({u['name']}) - 타입: {u.get('user_type', 'child')}")
