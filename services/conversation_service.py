from database.db_manager import DatabaseManager
from services.gemini_service import GeminiService
from typing import List, Dict
import re
import google.generativeai as genai

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
        return self.db.get_all_messages_by_conversation(conversation_id)
    
    def get_user_conversations_by_date(self, user_id: int) -> List[Dict]:
        """사용자의 날짜별 대화 목록 조회"""
        return self.db.get_user_conversations_by_date(user_id)
    
    def summarize_conversation(self, conversation_id: int) -> str:
        """대화 내용을 요약"""
        messages = self.db.get_all_messages_by_conversation(conversation_id)
        
        if not messages:
            return "대화 내용이 없습니다."
        
        # 대화 내용을 텍스트로 변환 (너무 길면 잘라내기)
        conversation_text = ""
        for msg in messages[:20]:  # 최대 20개 메시지만 사용
            role_kr = "사용자" if msg['role'] == 'user' else "AI"
            content = msg['content'][:500]  # 메시지당 최대 500자
            conversation_text += f"{role_kr}: {content}\n\n"
        
        if len(messages) > 20:
            conversation_text += f"\n... (총 {len(messages)}개 메시지 중 일부만 표시)"
        
        # Gemini API로 요약 생성
        try:
            prompt = f"""다음 대화 내용을 간단하게 요약해주세요. 주요 질문과 답변의 핵심 내용을 2-3문장으로 요약해주세요.

대화 내용:
{conversation_text}

요약:"""
            
            # Gemini API 호출 (최신 google.genai 사용)
            response = self.gemini_service.client.models.generate_content(
                model="gemini-1.5-flash", # 직접 모델명 지정 (404 오류 해결 시도)
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            error_msg = str(e)
            if "Connection" in error_msg or "network" in error_msg.lower():
                return "요약 생성 중 네트워크 연결 오류가 발생했습니다. 인터넷 연결을 확인해주세요."
            else:
                return f"요약 생성 중 오류가 발생했습니다: {error_msg[:100]}"
