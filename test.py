DEEPSEEK_API_KEY="sk-6354c8ca45114d82ae5a87f2170b14c8"
DEEPSEEK_API_BASE="https://api.deepseek.com/v1"


import openai
from openai import OpenAI

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_API_BASE)

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Hello"},
    ],
    stream=False
)

print(response.choices[0].message.content)
