from openai import OpenAI
from typing import List, Dict
from config import Config

class OpenAIService:
    """OpenAI API 서비스 클래스"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or Config.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OpenAI API 키가 설정되지 않았습니다. .env 파일을 확인하세요.")
        self.client = OpenAI(api_key=self.api_key)
        self.model = Config.MODEL
    
    def _get_system_prompt(self, user_name: str = None, user_age: int = None) -> str:
        """아이 친화적인 시스템 프롬프트 생성"""
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
        user_age: int = None
    ) -> str:
        """컨텍스트를 포함한 대화 생성"""
        system_prompt = self._get_system_prompt(user_name, user_age)
        
        # OpenAI API 형식으로 변환
        formatted_messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        for msg in messages:
            formatted_messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
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
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "당신은 금융 교육 전문가입니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"코칭 메시지를 생성하는 중 오류가 발생했습니다: {str(e)}"
