import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.environ["GROQ_API_KEY"])

resp = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "Sadece 'tamam' yaz."}],
    temperature=0,
    seed=42,
)
print(resp.choices[0].message.content)