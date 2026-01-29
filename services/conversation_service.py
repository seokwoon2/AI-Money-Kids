"""대화 관리 서비스 - Gemini AI와 데이터베이스를 연결"""
from typing import List, Dict, Optional
from database.db_manager import DatabaseManager
from services.gemini_service import GeminiService


class ConversationService:
    """대화 세션 및 메시지 관리 서비스"""
    
    def __init__(self):
        self.db = DatabaseManager()
        try:
            self.gemini_service = GeminiService()
        except Exception as e:
            # API 키가 없어도 서비스는 초기화되도록 함
            self.gemini_service = None
            import streamlit as st
            if hasattr(st, 'session_state'):
                pass  # 나중에 에러 처리
    
    def get_or_create_conversation(self, user_id: int) -> int:
        """사용자의 대화 세션 가져오기 또는 생성"""
        # 오늘 날짜의 대화 세션 사용
        return self.db.get_or_create_today_conversation(user_id)
    
    def get_all_messages(self, conversation_id: int) -> List[Dict]:
        """대화의 모든 메시지 가져오기"""
        # 충분히 큰 limit으로 모든 메시지 가져오기
        return self.db.get_conversation_messages(conversation_id, limit=1000)
    
    def chat(
        self,
        user_id: int,
        user_message: str,
        user_name: str = None,
        user_age: int = None,
        user_type: str = 'child'
    ) -> str:
        """사용자 메시지 처리 및 AI 응답 생성"""
        if not self.gemini_service:
            return "죄송해요, AI 서비스가 준비되지 않았어요. API 키를 확인해주세요."
        
        # 대화 세션 가져오기
        conversation_id = self.get_or_create_conversation(user_id)
        
        # 사용자 메시지 저장
        self.db.save_message(conversation_id, "user", user_message)
        
        # 이전 메시지 가져오기 (컨텍스트용)
        previous_messages = self.get_all_messages(conversation_id)
        
        # 메시지 형식 변환 (GeminiService가 기대하는 형식)
        messages_for_ai = []
        for msg in previous_messages:
            messages_for_ai.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # AI 응답 생성
        try:
            ai_response = self.gemini_service.chat_with_context(
                messages=messages_for_ai,
                user_name=user_name,
                user_age=user_age,
                user_type=user_type
            )
            
            # AI 응답 저장
            self.db.save_message(conversation_id, "assistant", ai_response)
            
            return ai_response
        except Exception as e:
            error_msg = str(e)
            if len(error_msg) > 200:
                error_msg = error_msg[:200] + "..."
            return f"죄송해요, 오류가 발생했어요: {error_msg}"
