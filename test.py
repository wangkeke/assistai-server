import urllib.request
import uuid
import os
from datetime import date, datetime 

# response = urllib.request.urlopen("https://cdn.openai.com/API/images/guides/image_generation_simple.webp")
# data = response.read()
# os.makedirs("/home/data/images")
# image_path = f"/images/{str(uuid.uuid4())}.webp"
# with open("/home/data" + image_path, 'wb') as f: 
#     f.write(data)
# print("写入完成")

# os.makedirs(f"/home/data/images", exist_ok=True)

print(date.today())

chunk = {"message": True}

print(list(chunk.keys())[0])

print(str(chunk.get(list(chunk.keys())[0])))

#
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate

llm = ChatOpenAI(temperature=0, 
                 openai_api_key="123456789", 
                 openai_api_base="https://assistai-server.onrender.com/openai_agent")
prompt = PromptTemplate.from_template("Tell me a joke about {topic}")

chain = prompt | llm

print( chain.invoke({"topic": "bears"}) )

# 
from langchain.chat_models import ChatOpenAI, ChatAnthropic
from unittest.mock import patch
from openai.error import RateLimitError
openai_llm = ChatOpenAI(max_retries=0)
anthropic_llm = ChatAnthropic()
llm = openai_llm.with_fallbacks([anthropic_llm])
with patch("openai.ChatCompletion.create", side_effect=RateLimitError()):
    try:
        print(llm.invoke("Why did the chicken cross the road?"))
    except:
        print("Hit error")