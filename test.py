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


def test():
    """这是一个测试函数"""
    print("This is test")

print(test.__name__)
print(test.__doc__)

import json
from fastapi.encoders import jsonable_encoder

json_args = json.loads("{\"location\": \"Boston, MA\", \"array\":[1,2,3]}")

def function(args: dict):
    print(args)
    print(args.get("location"))
    print(args.get("test"))

print(function(json_args))

chats = []
chats.append({"role":"user", "content": "text"})

chats_encoder = jsonable_encoder(chats)
print(chats_encoder[0].__class__)


supported_file_suffixes = (
    ".jpg",".jpeg",".png",".webp",".gif",
    ".doc",".docx",".xls",".xlsx",".ppt",".pptx",".csv",".pdf",
    ".txt",".sql",".json",".java",".py",".mq4",".mq5",".mqh",".js",".ts",".log",".html",".htm",".md",".vue"
    )
file_name = "卢新.jpg"
print(file_name.endswith(supported_file_suffixes))

filename = 'example.jpg'
ext_pos = filename.rfind('.') + 1
ext = filename[ext_pos:]
print(ext) # 'jpg'

from datetime import date, datetime


print(datetime.now().strftime("%Y%m%d%H%M%S%f"))

import hashlib

print(hashlib.md5(b"wangkeke565@163.com").hexdigest())
print(hashlib.md5(b"wangkeke565@126.com").hexdigest())
print(hashlib.md5(b"wangkeke565@qq.com").hexdigest())
print(hashlib.md5(b"wangkeke565@zenking.com").hexdigest())
print(hashlib.md5("wangkeke565@zenking.com".encode()).hexdigest())