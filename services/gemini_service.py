import google.generativeai as genai
from typing import List, Dict
from config import Config

class GeminiService:
    """Google Gemini API 서비스 클래스"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or Config.GEMINI_API_KEY
        if not self.api_key:
            error_msg = "Gemini API 키가 설정되지 않았습니다. "
            try:
                import streamlit as st
                if hasattr(st, 'secrets'):
                    error_msg += "Streamlit Cloud의 Secrets에서 GEMINI_API_KEY를 설정해주세요."
                else:
                    error_msg += ".env 파일 또는 환경 변수를 확인하세요."
            except:
                error_msg += ".env 파일 또는 환경 변수를 확인하세요."
            raise ValueError(error_msg)
        
        # API 키 형식 확인
        if not self.api_key.startswith("AIza"):
            raise ValueError(f"잘못된 API 키 형식입니다. Gemini API 키는 'AIza...'로 시작해야 합니다. (현재: {self.api_key[:10]}...)")
        
        genai.configure(api_key=self.api_key)
        
        # 사용 가능한 모델 확인 및 설정
        # google-generativeai 패키지에서는 모델 이름에 'models/' 접두사 없이 사용
        self.model_name = Config.MODEL
    
    def _get_system_prompt(self, user_name: str = None, user_age: int = None, user_type: str = 'child') -> str:
        """사용자 타입에 맞는 시스템 프롬프트 생성"""
        if user_type == 'parent':
            # 부모용 프롬프트
            name_context = f"{user_name}님, " if user_name else ""
            return f"""당신은 부모의 자녀 금융 교육을 돕는 전문 AI 상담사입니다.

{name_context}자녀의 금융 교육에 대한 조언과 가이드를 제공해주세요.

원칙:
1. 전문적이고 실용적인 조언을 제공하세요
2. 자녀의 나이와 발달 단계를 고려한 교육 방법을 제시하세요
3. 구체적이고 실행 가능한 방법을 제안하세요
4. 긍정적이고 격려하는 톤을 유지하세요
5. 자녀와의 대화 방법, 저축 습관 기르기, 용돈 관리 등 실용적인 팁을 제공하세요
6. 금융 교육의 중요성과 장기적인 효과를 설명하세요

부모가 자녀의 금융습관, 교육 방법, 문제 해결 등에 대해 질문하면 구체적이고 실용적인 답변을 제공하세요."""
        else:
            # 아이용 프롬프트
            age_context = ""
            if user_age:
                if user_age < 8:
                    age_context = "매우 쉽고 간단한 단어로 설명해주세요. 예시를 많이 들어주세요."
                elif user_age < 12:
                    age_context = "쉬운 단어로 설명하되, 구체적인 예시를 들어주세요."
                else:
                    age_context = "명확하고 이해하기 쉽게 설명해주세요."
            
            name_context = f"{user_name}야, " if user_name else ""
            
            return f"""당신은 아이들의 금융 교육을 돕는 친절한 AI 코치입니다.

{name_context}아이들이 돈에 대해 배우고 좋은 습관을 기를 수 있도록 도와주세요.

원칙:
1. 항상 긍정적이고 격려하는 톤으로 대화하세요
2. {age_context}
3. 실생활 예시를 들어 설명하세요
4. 아이의 질문에 정직하고 이해하기 쉽게 답변하세요
5. 저축, 계획적 소비, 인내심의 중요성을 자연스럽게 전달하세요
6. 복잡한 금융 용어는 피하고 쉬운 말로 바꿔 설명하세요

대화 중에 아이가 저축, 소비, 계획, 인내심 등에 대해 언급하면 자연스럽게 긍정적으로 반응하세요."""
    
    def chat_with_context(
        self, 
        messages: List[Dict[str, str]], 
        user_name: str = None,
        user_age: int = None,
        user_type: str = 'child'
    ) -> str:
        """컨텍스트를 포함한 대화 생성"""
        system_prompt = self._get_system_prompt(user_name, user_age, user_type)
        
        try:
            # 시스템 프롬프트와 함께 모델 생성
            model = genai.GenerativeModel(
                self.model_name,
                system_instruction=system_prompt
            )
            
            # 채팅 히스토리 구성
            chat_history = []
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                
                if role == "user":
                    chat_history.append({"role": "user", "parts": [content]})
                elif role == "assistant":
                    chat_history.append({"role": "model", "parts": [content]})
            
            # 채팅 세션 시작
            chat = model.start_chat(history=chat_history[:-1] if len(chat_history) > 1 else [])
            
            # 마지막 사용자 메시지 전송
            last_user_message = None
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    last_user_message = msg.get("content", "")
                    break
            
            if last_user_message:
                response = chat.send_message(last_user_message)
            else:
                # 사용자 메시지가 없으면 첫 인사
                response = chat.send_message("안녕하세요!")
            
            return response.text.strip()
        except Exception as e:
            return f"죄송해요, 오류가 발생했어요. 다시 시도해주세요. (오류: {str(e)})"
    
    def generate_parent_coaching(
        self,
        child_name: str,
        impulsivity_score: float,
        saving_tendency: float,
        patience_score: float,
        recent_behaviors: List[Dict]
    ) -> str:
        """부모용 코칭 메시지 생성"""
        
        # 행동 요약
        behavior_summary = ""
        if recent_behaviors:
            saving_count = sum(1 for b in recent_behaviors if b.get('behavior_type') == 'saving')
            impulse_count = sum(1 for b in recent_behaviors if b.get('behavior_type') == 'impulse_buying')
            planned_count = sum(1 for b in recent_behaviors if b.get('behavior_type') == 'planned_spending')
            
            behavior_summary = f"""
최근 행동 요약:
- 저축 행동: {saving_count}회
- 충동 구매: {impulse_count}회
- 계획적 소비: {planned_count}회
"""
        
        prompt = f"""당신은 금융 교육 전문가입니다. 부모에게 자녀의 금융습관에 대한 코칭 조언을 제공하세요.

자녀 이름: {child_name}

금융습관 점수:
- 충동성: {impulsivity_score:.1f}/100 (낮을수록 좋음)
- 저축성향: {saving_tendency:.1f}/100 (높을수록 좋음)
- 인내심: {patience_score:.1f}/100 (높을수록 좋음)

{behavior_summary}

다음 내용을 포함한 코칭 메시지를 작성해주세요:
1. 자녀의 강점 (긍정적인 부분 강조)
2. 개선이 필요한 영역 (구체적으로)
3. 가정에서 실천할 수 있는 구체적인 방법 (3-5가지)

친절하고 실용적인 톤으로 작성하되, 자녀를 격려하는 방향으로 제시하세요."""

        try:
            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=800,
                )
            )
            
            return response.text.strip()
        except Exception as e:
            return f"코칭 메시지를 생성하는 중 오류가 발생했습니다: {str(e)}"
