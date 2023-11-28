import os
import openai

client = openai.OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY", "1234567890"),
    max_retries=0,
    # base_url="http://43.153.6.89:8000/agent/openai",
)