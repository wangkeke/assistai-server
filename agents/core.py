import os
import openai

client = openai.OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY", "1234567890"),
    max_retries=0
)