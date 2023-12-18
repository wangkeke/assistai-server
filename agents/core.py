import os
import openai
import logging
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI

FORMAT = '%(asctime)s %(clientip)-15s %(user)-8s %(message)s'
logging.basicConfig(format=FORMAT)

logger = logging.getLogger("agents")

base_url = "http://43.153.6.89:8000/agent/openai"


client = openai.OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY", "1234567890"),
    base_url=base_url,
    max_retries=0,
)

aclient = openai.AsyncOpenAI(
    api_key=os.environ.get("OPENAI_API_KEY", "1234567890"),
    base_url=base_url,
    max_retries=0,
)

embeddings = OpenAIEmbeddings(
    api_key=os.environ.get("OPENAI_API_KEY", "1234567890"),
    base_url=base_url,
    max_retries=0,
) 

chat_open_ai = ChatOpenAI(max_retries=0, 
           base_url=base_url, 
           api_key=os.environ.get("OPENAI_API_KEY", "1234567890")
           )

chat_open_ai_16k = ChatOpenAI(max_retries=0, 
           base_url=base_url, 
           api_key=os.environ.get("OPENAI_API_KEY", "1234567890"),
           model_name="gpt-3.5-turbo-16k",
           )