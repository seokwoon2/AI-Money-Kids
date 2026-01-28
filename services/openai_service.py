from openai import OpenAI
from typing import List, Dict
from config import Config

class OpenAIService:
    def __init__(self, api_key: str = None):
        self.client = OpenAI(api_key=api_key or Config.OPENAI_API_KEY)
        self.model = "gpt-4.1-mini"  # 안정적이고 빠름

    def chat_with_context(self, messages: List[Dict[str, str]], user_name=None, user_age=None) -> str:
        try:
            response = self.client.responses.create(
                model=self.model,
                input=[
                    {
                        "role": "system",
                        "content": "너는 아이 금융 교육 코치야. 쉽고 친절하게 설명해줘."
                    },
                    *messages
                ],
            )

            return response.output_text

        except Exception as e:
            return f"AI 호출 오류: {e}"

    def generate_parent_coaching(self, prompt: str) -> str:
        try:
            response = self.client.responses.create(
                model=self.model,
                input=prompt
            )
            return response.output_text
        except Exception as e:
            return f"코칭 오류: {e}"
