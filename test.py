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






from openai import OpenAI
import json
import logging

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY", "1234567890"),
    max_retries=0,
    base_url="http://43.153.6.89:8000/agent/openai"
    )

# Example dummy function hard coded to return the same weather
# In production, this could be your backend API or an external API
def get_current_weather(args: dict):
    """Get the current weather in a given location"""
    location = args.get("location")
    unit="fahrenheit"
    if args.get("unit"):
        unit = args.get("unit")
    if "tokyo" in location.lower():
        return json.dumps({"location": "Tokyo", "temperature": "10", "unit": "celsius"})
    elif "san francisco" in location.lower():
        return json.dumps({"location": "San Francisco", "temperature": "72", "unit": "fahrenheit"})
    elif "paris" in location.lower():
        return json.dumps({"location": "Paris", "temperature": "22", "unit": "celsius"})
    else:
        return json.dumps({"location": location, "temperature": "unknown"})

def generate_image(args: dict):
    """Generate an image based on the prompt"""
    prompt: str = args.get("prompt")
    return json.dumps({"prompt": prompt, "image_url": f'https://cdn.openai.com/API/images/guides/image_generation_simple.webp'})

def understanding_image(args: dict):
    """Understand images based on user description"""
    text: str = args.get("text")
    image_urls: list[str] = args.get("image_urls")
    return "这是一段python代码的截图：\n\n下面是一个用Python写的斐波那契函数，其参数是n：\n\n```python\n def fibonacci(n):\n    if n <= 0:\n        return []\n    elif n == 1:\n        return [0]\n    else:\n        sequence = [0, 1]\n        while len(sequence) < n:\n            next_number = sequence[-1] + sequence[-2]\n            sequence.append(next_number)\n        return sequence\n```\n\n这个函数将返回一个包含n个斐波那契数列的列表。如果n小于等于0，将返回一个空列表。如果n等于1，将返回一个只包含0的列表。否则，函数将使用循环构建斐波那契数列，直到列表达到n个元素。\n\n "

def run_conversation():
    # Step 1: send the conversation and available functions to the model
    # messages = [{"role": "user", "content": "What's the weather like in San Francisco, Tokyo, and Paris?"}]
    messages = [{"role": "user", "content": "Generate a picture of a white cat."}]
    # messages = [{"role": "user", "content": "Depending on whether a function call is required as described below, the generated message can only answer yes or no: Hello!"}]
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_current_weather",
                "description": "Get the current weather in a given location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA",
                        },
                        "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                    },
                    "required": ["location"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": generate_image.__name__,
                "description": generate_image.__doc__,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "a detailed prompt to generate an image",
                        },
                    },
                    "required": ["prompt"],
                },
            }
        },
        {
            "type": "function",
            "function": {
                "name": understanding_image.__name__,
                "description": understanding_image.__doc__,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "image_urls": {"type": "array", "items": {"type": "string"}, "description": "List of urls for images"},
                        "text": {"type": "string", "description": "Other text content"},
                    },
                    "required": ["text", "image_urls"],
                },
            }
        },
    ]
    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=messages,
        tools=tools,
        tool_choice="auto",  # auto is default, but we'll be explicit
    )
    print(response)
    response_message = response.choices[0].message
    if response_message.content is None:
        response_message.content = ""
    if response_message.function_call is None:
        del response_message.function_call
    tool_calls = response_message.tool_calls
    # Step 2: check if the model wanted to call a function
    if tool_calls:
        # Step 3: call the function
        # Note: the JSON response may not always be valid; be sure to handle errors
        available_functions = {
            "get_current_weather": get_current_weather,
            "generate_image": generate_image,
            "understanding_image": understanding_image
        }  # only one function in this example, but you can have multiple
        messages.append(response_message)  # extend conversation with assistant's reply
        # Step 4: send the info for each function call and function response to the model
        print(messages)
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            function_response = function_to_call(function_args)
            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                }
            )  # extend conversation with function response
        second_response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=messages,
        )  # get a new response from the model where it can see the function response
        return second_response
print(run_conversation())



new_messages = [{"role": "user"}]
print(new_messages[0]["role"])



import orm.schemas
import orm.models
import json
from datetime import datetime

topic_chat = orm.models.TopicChat(role="role", content_type="content_type", content="topic_chat.content", 
                                  topic_id="topic_id", 
                                  create_time=datetime.now(), 
                                  flag=True,
                                  id= 1
                                  )
print(json.dumps({"id" : topic_chat.id, "role": "assistant", "content": "dsadsada","content_type": "text", "create_time": datetime.now().isoformat(), "remain_num": 3}))






from openai import OpenAI

client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4-vision-preview",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What’s in this image?"},
                {
                    "type": "image_url",
                    "image_url": "https://www.uassistant.net/api/static/upload/7b8ea8096943efb4ae9c221395803ec1/29124d19-764a-4cea-844d-1bd7645ed622.jpg",
                },
            ],
        }
    ],
    max_tokens=300,
)

print(response.choices[0])




curl https://api.openai.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
    "model": "gpt-4-vision-preview",
    "messages": [
      {
        "role": "user",
        "content": [
          {
            "type": "text",
            "text": "What’s in this image?"
          },
          {
            "type": "image_url",
            "image_url": {
              "url": "https://www.uassistant.net/api/static/upload/7b8ea8096943efb4ae9c221395803ec1/6855dd9a-1cc3-43b3-894a-d01a0bfc1e46.png"
            }
          }
        ]
      }
    ],
    "max_tokens": 300
  }'

# openai.BadRequestError: Error code: 400 - {'error': {'code': 'content_policy_violation', 'message': 'This request has been blocked by our content filters.', 'param': None, 'type': 'invalid_request_error'}}