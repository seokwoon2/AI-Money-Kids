from groq import Groq
from config import Config

client = Groq(api_key=Config.GROQ_API_KEY)

print("AI 연결 테스트 중...")

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {"role": "user", "content": "저축은 왜 중요해?"}
    ]
)

print("\nAI 답변:")
print(response.choices[0].message.content)
