import os
import json
from datetime import date
import urllib.request
import uuid
import openai
from typing import Annotated
from fastapi import Depends, Request, status, HTTPException, APIRouter
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from sse_starlette.sse import EventSourceResponse
from orm import schemas, crud
from dependencies import get_db, get_current_user

# 环境变量
DOMAIN_NAME = os.environ.get("DOMAIN_NAME", "127.0.0.1:8000")
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-3.5-turbo-1106")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "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")

router = APIRouter(
    prefix="/chat", 
    tags=["chat"], 
    responses={404 : {"description": "Not Found"}}
    )

# 检查请求限制
def check_request_limit(db: Session, current_user: schemas.User):
    # 检查是否超出使用限制
    rpd_amount = int(os.getenv("DEFAULT_REQUEST_PER_DAY"))
    user_sets = crud.get_user_set(db, current_user.id, "RPD")
    if user_sets:
        rpd_amount = int(user_sets[0].set_value)
    rpd_count = 0
    user_chat_stats = crud.get_user_chat_stats(db, user_id=current_user.id, stats_date=date.today(), stats_key="RPD")
    if not user_chat_stats:
        user_chat_stats_create = schemas.UserChatStatsCreate(stats_date=date.today(), stats_key="RPD", stats_value=0)
        user_chat_stats = crud.create_user_chat_stats(db, user_chat_stats_create=user_chat_stats_create, user_id=current_user.id)
    else:
        rpd_count = user_chat_stats.stats_value
    if rpd_count >= rpd_amount:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="你已经超出今日使用限制！"
        )
    return user_chat_stats

# 添加聊天记录
@router.post("/{topic_id}/add")
def add_chat(topic_id: str, chat_create: schemas.TopicChatCreate, current_user: Annotated[schemas.User, Depends(get_current_user)], db: Session = Depends(get_db)):
    check_request_limit(db, current_user=current_user)
    return crud.create_topic_chat(db, topic_chat=chat_create, topic_id=topic_id)

# 删除聊天信息
@router.get('/{topic_id}/remove')
def remove_chat(topic_id: str, id: str , current_user: Annotated[schemas.User, Depends(get_current_user)], db: Session = Depends(get_db)):
    crud.remove_topic_chat(db, topic_id=topic_id, chat_id=id)

# 读取网络地址图片并写入本地磁盘
def save_image(url: str):
    disk_path = os.getenv('DISK_PATH')
    os.makedirs(f"{disk_path}/images", exist_ok=True)
    response = urllib.request.urlopen(url)
    data = response.read()
    image_path = f"/images/{str(uuid.uuid4())}.webp"
    with open(disk_path + image_path, 'wb') as f: 
        f.write(data)
    return image_path

# 生成图像函数
def create_image(prompt: str):
    """Generate images for user"""
    response_format = "url"
    response = openai.Image.create(
        api_key= OPENAI_API_KEY,
        prompt= prompt,
        n=1,
        response_format=response_format
    )
    return save_image(url=response['data'][0][response_format])

# 生成图像测试函数
def create_image_test(prompt: str):
    """Generate images for user"""
    return "/images/360fbc24-c154-4e30-9b82-060362baecbe.webp"

# 定义模型函数调用
functions = [ 
  {
    "name": "create_image",
    "description": "generate images for user",
    "parameters": {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "Prompt for the image the user wants to generate",
            },
        },
        "required": ["prompt"],
    },
  }
]

# 流式响应函数
async def event_publisher(chunks, db: Session, topic_id: str):
    collected_messages = []
    role = None
    finish_reason = None
    
    function_call = None
    function_call_name = None
    function_call_arguments = []
    
    for chunk in chunks:
        delta = chunk['choices'][0]['delta']
        if delta.get('role'):
            role = delta.get('role')
            yield dict(event='start', data= role)
        if delta.get('content'):
            content = delta.get('content')
            collected_messages.append(content)
            yield dict(event='stream', data=content.replace('\n', '\\n'))
        if delta.get('function_call'):
            function_call = delta.get('function_call')
            if function_call.get('name'):
                function_call_name = function_call.get('name')
            if function_call.get('arguments'):
                function_call_arguments.append(function_call.get('arguments'))
        finish_reason = chunk['choices'][0]['finish_reason']
    
    content_type = 'text'
    content = None
    if finish_reason == 'function_call':
        if function_call_name == 'create_image':
            content_type = 'image'
            yield dict(event='prepare', data=content_type)
            prompt = json.loads(''.join(function_call_arguments))["prompt"]
            content = os.getenv('STATIC_PATH') + create_image(prompt=prompt)
            content = f"url={content}, prompt={prompt}"
            yield dict(event='image', data=content)
    else:
        content = ''.join(collected_messages)
    assistant_chat = crud.create_topic_chat(db, topic_chat=schemas .TopicChatCreate(role=role, content=content), topic_id=topic_id, content_type=content_type)
    yield dict(event='end', data=assistant_chat.id)

# 聊天交互接口
@router.post("/{topic_id}/conversation")
def chat(topic_id: str, chat_creates: list[schemas.TopicChatCreate], current_user: Annotated[schemas.User, Depends(get_current_user)], db: Session = Depends(get_db)):
    user_chat_stats = check_request_limit(db, current_user=current_user)
    try: 
        response = openai.ChatCompletion.create(model = MODEL_NAME, 
                                    api_key = OPENAI_API_KEY,
                                    messages = jsonable_encoder(chat_creates),
                                    stream = True,
                                    functions = functions,
                                    function_call = "auto"
                                    )
        return EventSourceResponse(event_publisher(response, db=db, topic_id=topic_id))
    finally: 
        crud.increase_user_chat_stats(db, id=user_chat_stats.id)

# 聊天交互测试接口
@router.post("/{topic_id}/conversation_test")
def chats(topic_id: str, chat_creates: list[schemas.TopicChatCreate], current_user: Annotated[schemas.User, Depends(get_current_user)], db: Session = Depends(get_db)):
    user_chat_stats = check_request_limit(db, current_user=current_user)
    try:
        def text_event_publisher(db: Session, topic_id: str):
            collected_messages = []
            role = "assistant"
            testValue = "下面是一个用Python写的斐波那契函数，其参数是n：\n\n```python\ndef fibonacci(n):\n    if n <= 0:\n        return []\n    elif n == 1:\n        return [0]\n    else:\n        sequence = [0, 1]\n        while len(sequence) < n:\n            next_number = sequence[-1] + sequence[-2]\n            sequence.append(next_number)\n        return sequence\n```\n\n这个函数将返回一个包含n个斐波那契数列的列表。如果n小于等于0，将返回一个空列表。如果n等于1，将返回一个只包含0的列表。否则，函数将使用循环构建斐波那契数列，直到列表达到n个元素。\n"
            yield dict(event='start', data= jsonable_encoder(chat_creates))
            for i in range(len(testValue)):
                collected_messages.append(testValue[i])
                yield dict(event='stream', data=testValue[i].replace('\n', '\\n'))

            content = ''.join(collected_messages)
            assistant_chat = crud.create_topic_chat(db, topic_chat=schemas.TopicChatCreate(role=role, content=content), topic_id=topic_id)
            yield dict(event='end', data=assistant_chat.id)
        
        def image_event_publisher(db: Session, topic_id: str):
            role = "assistant"
            testValue = "下面是一个用Python写的斐波那契函数，其参数是n：\n\n```python\ndef fibonacci(n):\n    if n <= 0:\n        return []\n    elif n == 1:\n        return [0]\n    else:\n        sequence = [0, 1]\n        while len(sequence) < n:\n            next_number = sequence[-1] + sequence[-2]\n            sequence.append(next_number)\n        return sequence\n```\n\n这个函数将返回一个包含n个斐波那契数列的列表。如果n小于等于0，将返回一个空列表。如果n等于1，将返回一个只包含0的列表。否则，函数将使用循环构建斐波那契数列，直到列表达到n个元素。\n"
            yield dict(event='start', data= jsonable_encoder(chat_creates))
            # 测试生成图像
            content_type = 'image'
            yield dict(event='prepare', data=content_type)
            prompt = chat_creates[len(chat_creates)-1].content
            content = os.getenv('STATIC_PATH') + create_image_test(prompt=prompt)
            content = f"url={content}, prompt={prompt}"
            yield dict(event='image', data=content)
            
            assistant_chat = crud.create_topic_chat(db, topic_chat=schemas.TopicChatCreate(role=role, content=content), topic_id=topic_id, content_type=content_type)
            yield dict(event='end', data=assistant_chat.id)
        return EventSourceResponse(image_event_publisher(db=db, topic_id=topic_id))
    finally: 
        crud.increase_user_chat_stats(db, id=user_chat_stats.id)
        
# 添加问题反馈
@router.post("/{chat_id}/issue/create", response_model=schemas.TopicChatIssue)
def create_chat_issue(chat_id: int, chat_issue: schemas.TopicChatIssueCreate, current_user: Annotated[schemas.User, Depends(get_current_user)], db: Session = Depends(get_db)):
    chat_issue = crud.create_topic_chat_issue(db, user_id=current_user.id, chat_id=chat_id, topic_chat_issue=chat_issue)
    return chat_issue

# 修改问题反馈
@router.post("/{chat_id}/issue/update")
def update_chat_issue(issue_update: schemas.TopicChatIssueUpdate, current_user: Annotated[schemas.User, Depends(get_current_user)], db: Session = Depends(get_db)):
    crud.update_topic_chat_issue(db, topic_chat_issue=issue_update)

# openai代理
@router.post("/openai_agent/chat/completions")
async def openai_agent(request: Request):
    json_data = await request.json()
    model_name = json_data['model']
    messages = json_data['messages']
    if json_data.get("functions"):
        function_call = "auto"
        if json_data.get("function_call"):
            function_call = json_data.get("function_call")
        return openai.ChatCompletion.create(
            model = model_name,
            api_key = OPENAI_API_KEY,
            messages=messages,
            functions=json_data.get("functions"),
            function_call=function_call,  # auto is default, but we'll be explicit
        )
    else:
        return openai.ChatCompletion.create(
            model = model_name, 
            api_key = OPENAI_API_KEY,
            messages = messages
        )