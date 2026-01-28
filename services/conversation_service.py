from database.db_manager import DatabaseManager
from services.gemini_service import GeminiService
from typing import List, Dict
import re

class ConversationService:
    """대화 관리 서비스"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.gemini_service = GeminiService()
    
    def get_or_create_conversation(self, user_id: int) -> int:
        """오늘 날짜의 대화 세션 조회 또는 생성"""
        return self.db.get_or_create_today_conversation(user_id)
    
    def get_conversation_history(self, conversation_id: int, limit: int = 10) -> List[Dict]:
        """대화 히스토리 조회"""
        messages = self.db.get_conversation_messages(conversation_id, limit)
        # OpenAI API 형식으로 변환
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in messages
        ]
    
    def save_message(self, conversation_id: int, role: str, content: str):
        """메시지 저장"""
        self.db.save_message(conversation_id, role, content)
    
    def chat(self, user_id: int, user_message: str, user_name: str = None, user_age: int = None, user_type: str = 'child') -> str:
        """사용자 메시지에 대한 AI 응답 생성"""
        # 대화 세션 가져오기 또는 생성
        conversation_id = self.get_or_create_conversation(user_id)
        
        # 사용자 메시지 저장
        self.save_message(conversation_id, "user", user_message)
        
        # 대화 히스토리 가져오기 (최근 10개)
        history = self.get_conversation_history(conversation_id, limit=10)
        
        # Gemini API 호출
        response = self.gemini_service.chat_with_context(
            history,
            user_name=user_name,
            user_age=user_age,
            user_type=user_type
        )
        
        # AI 응답 저장
        self.save_message(conversation_id, "assistant", response)
        
        # 행동 자동 분류 및 저장 (아이인 경우에만)
        if user_type == 'child':
            self._detect_and_save_behavior(user_id, user_message, response)
        
        return response
    
    def _detect_and_save_behavior(self, user_id: int, user_message: str, ai_response: str):
        """메시지에서 금융 행동 감지 및 저장"""
        message_lower = (user_message + " " + ai_response).lower()
        
        # 저축 관련 키워드
        saving_keywords = ['저축', '저금', '모았', '모으', '적금', '통장', '돈 모', '아껴']
        if any(keyword in message_lower for keyword in saving_keywords):
            # 금액 추출 시도
            amount = self._extract_amount(message_lower)
            self.db.save_behavior(user_id, "saving", amount=amount, description="대화에서 저축 언급")
        
        # 충동 구매 관련 키워드
        impulse_keywords = ['그냥 사', '바로 사', '즉시 사', '충동', '참지 못', '당장 사']
        if any(keyword in message_lower for keyword in impulse_keywords):
            amount = self._extract_amount(message_lower)
            self.db.save_behavior(user_id, "impulse_buying", amount=amount, description="대화에서 충동구매 언급")
        
        # 계획적 소비 관련 키워드
        planned_keywords = ['계획', '생각해', '고민해', '비교해', '검토', '준비']
        if any(keyword in message_lower for keyword in planned_keywords):
            amount = self._extract_amount(message_lower)
            self.db.save_behavior(user_id, "planned_spending", amount=amount, description="대화에서 계획적 소비 언급")
        
        # 인내심/만족 지연 관련 키워드
        patience_keywords = ['기다려', '참아', '나중에', '인내', '지연', '기다리']
        if any(keyword in message_lower for keyword in patience_keywords):
            self.db.save_behavior(user_id, "delayed_gratification", description="대화에서 인내심 언급")
        
        # 가격 비교 관련 키워드
        compare_keywords = ['비교', '더 싼', '더 저렴', '가격', '어디가 싸']
        if any(keyword in message_lower for keyword in compare_keywords):
            self.db.save_behavior(user_id, "comparing_prices", description="대화에서 가격 비교 언급")
    
    def _extract_amount(self, text: str) -> float:
        """텍스트에서 금액 추출"""
        # 숫자 + 원, 만원, 천원 등 패턴 찾기
        patterns = [
            r'(\d+)\s*원',
            r'(\d+)\s*만원',
            r'(\d+)\s*천원',
            r'(\d+)\s*만\s*원',
            r'(\d+)\s*천\s*원',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                amount = float(match.group(1))
                if '만' in pattern:
                    amount *= 10000
                elif '천' in pattern:
                    amount *= 1000
                return amount
        
        return None
    
    def get_all_messages(self, conversation_id: int) -> List[Dict]:
        """대화의 모든 메시지 조회"""
        return self.db.get_conversation_messages(conversation_id, limit=1000)
