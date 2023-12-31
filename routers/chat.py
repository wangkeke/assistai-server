import os
from datetime import date
import logging
from typing import Annotated
from fastapi import Depends, status, HTTPException, APIRouter
from sqlalchemy.orm import Session
import json
from sse_starlette.sse import EventSourceResponse
from orm import schemas, crud
from dependencies import get_db, get_current_user
from agents.openai_agent import chat_completion


router = APIRouter(
    prefix="/chat", 
    tags=["chat"], 
    responses={404 : {"description": "Not Found"}}
)

log = logging.getLogger(__name__)

DATA_PATH = os.getenv("DATA_PATH", "/home/lighthouse/workspace/data/")
if not os.path.exists(DATA_PATH):
    os.makedirs(DATA_PATH, exist_ok=True)

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
            detail="Today messages have been exhausted."
        )
    return user_chat_stats, rpd_amount


# 添加聊天记录
@router.post("/{topic_id}/add", response_model=schemas.TopicChat)
def add_chat(topic_id: str, chat_create: schemas.TopicChatCreate, current_user: Annotated[schemas.User, Depends(get_current_user)], db: Session = Depends(get_db)):
    check_request_limit(db, current_user=current_user)
    topic_chat = crud.create_topic_chat(db, topic_chat=chat_create, topic_id=topic_id)
    topic_chat.attachs = crud.create_topic_chat_attach(db=db, attachs=chat_create.attachs, topic_chat_id=topic_chat.id)
    return topic_chat


# 删除聊天信息
@router.get('/{topic_id}/remove')
def remove_chat(topic_id: str, id: str , current_user: Annotated[schemas.User, Depends(get_current_user)], db: Session = Depends(get_db)):
    crud.remove_topic_chat(db, topic_id=topic_id, chat_id=id)

# 流式响应函数
async def event_publisher(message, chat_id: int, stats_count: int):
    yield dict(event='start', data= message.get("role"))
    content = message.get("content")
    for i in range(len(content)):
        yield dict(event='stream', data=content[i].replace('\n', '\\n'))
    yield dict(event='end', data=json.dumps({"chat_id" : chat_id, "remain_num": stats_count}))




# 流式响应函数
async def event_publisher(chunks, db: Session, topic_id: str, remain_num: int):
    collected_messages = []
    role = "assistant"
    yield dict(event="start", data=role)
    for chunk in chunks:
        if chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            collected_messages.append(content)
            yield dict(event='stream', data=content.replace('\n', '\\n'))
    content_type = 'text'
    content = ''.join(collected_messages)
    topic_chat = crud.create_topic_chat(db, topic_chat=schemas.TopicChatCreate(role=role, content=content), topic_id=topic_id, content_type=content_type)
    end_data = json.dumps({"id" : topic_chat.id, "remain_num": remain_num})
    yield dict(event='end', data=end_data)

# 聊天交互接口
@router.post("/{topic_id}/conversation")
def chat(topic_id: str, topic_chats: list[schemas.TopicChatCreate], current_user: Annotated[schemas.User, Depends(get_current_user)], db: Session = Depends(get_db)):
    user_chat_stats, rpd_amount = check_request_limit(db, current_user=current_user)
    try:
        import hashlib
        user_dir = hashlib.md5(current_user.username.encode()).hexdigest()
        response = chat_completion(
            user_id=current_user.id, 
            user_partition=os.getenv("DATA_PATH")+user_dir, 
            topic_chats=topic_chats
            )
        return EventSourceResponse(event_publisher(response, db=db, topic_id=topic_id, remain_num=rpd_amount - user_chat_stats.stats_value - 1))
    finally: 
        crud.increase_user_chat_stats(db, id=user_chat_stats.id)

# 聊天交互测试接口
@router.post("/{topic_id}/conversation_test")
async def chats(topic_id: str, chat_creates: list[schemas.TopicChatCreate], current_user: Annotated[schemas.User, Depends(get_current_user)], db: Session = Depends(get_db)):
    user_chat_stats, rpd_amount = check_request_limit(db, current_user=current_user)
    try:
        # role = "assistant"
        # testValue = "下面是一个用Python写的斐波那契函数，其参数是n：\n\n```python\n def fibonacci(n):\n    if n <= 0:\n        return []\n    elif n == 1:\n        return [0]\n    else:\n        sequence = [0, 1]\n        while len(sequence) < n:\n            next_number = sequence[-1] + sequence[-2]\n            sequence.append(next_number)\n        return sequence\n```\n\n这个函数将返回一个包含n个斐波那契数列的列表。如果n小于等于0，将返回一个空列表。如果n等于1，将返回一个只包含0的列表。否则，函数将使用循环构建斐波那契数列，直到列表达到n个元素。\n\n "
        async def text_event_publisher(db: Session, topic_id: str, stats_count: int):
            collected_messages = []
            role = "assistant"
            # testValue = "以下是针对“AI应用产品研发：从市场调研->产品设计->软件开发->投入市场”的目录大纲：\n\n1. 引言\n   - 研发概览\n   - AI应用的市场趋势\n\n2. 市场调研\n   - 目标市场分析\n     - 客户需求调研\n     - 竞争对手分析\n     - 市场容量和增长预测\n   - 技术趋势评估\n     - 当前AI技术发展状态\n     - 预见未来技术演进\n\n3. 产品设计\n   - 概念构想\n     - 产品定位\n     - 功能规划\n     - 用户体验设计\n   - 技术实现规划\n     - AI模型选择\n     - 系统架构设计\n     - 数据安全和隐私保护\n\n4. 软件开发\n   - AI模型开发\n     - 数据收集与处理\n     - 模型训练与验证\n     - 模型优化与部署\n   - 应用程序开发\n     - 界面设计与实现\n     - 功能编程\n     - 测试与质量保证\n\n5. 投入市场\n   - 市场策略制定\n     - 定价策略\n     - 渠道选择\n     - 营销推广\n   - 用户支持和服务\n     - 客户服务体系构建\n     - 用户反馈收集与产品迭代\n     - 售后支持与服务\n\n6. 结论\n   - 项目回顾\n   - 成功要素分析\n   - 未来展望\n\n这个大纲覆盖了AI应用产品的研发流程的各个阶段，从初始市场调研到产品设计，再到软件开发，最后的市场投入。每个阶段都包含了关键活动与决策点，旨在帮助读者梳理AI产品开发过程中的主要步骤和考虑因素。"
            # testValue = "下面是一个用Python写的斐波那契函数，其参数是n：\n\n```python\n def fibonacci(n):\n    if n <= 0:\n        return []\n    elif n == 1:\n        return [0]\n    else:\n        sequence = [0, 1]\n        while len(sequence) < n:\n            next_number = sequence[-1] + sequence[-2]\n            sequence.append(next_number)\n        return sequence\n```\n\n这个函数将返回一个包含n个斐波那契数列的列表。如果n小于等于0，将返回一个空列表。如果n等于1，将返回一个只包含0的列表。否则，函数将使用循环构建斐波那契数列，直到列表达到n个元素。\n\n "
            # testValue = "## Tables\n\n| Option | Description |\n| ------ | ----------- |\n| data   | path to data files to supply the data that will be passed into templates. |\n| engine | engine to be used for processing templates. Handlebars is the default. |\n| ext    | extension to be used for dest files. |\n\n"
            # testValue = "1. First ordered list item\n2. Another item\n⋅⋅* Unordered sub-list.\n1. Actual numbers don't matter, just that it's a number\n⋅⋅1. Ordered sub-list\n4. And another item.⋅⋅⋅You can have properly indented paragraphs within list items.\n\n⋅⋅⋅To have a line break without a paragraph, you will need to use two trailing spaces.⋅⋅\n\n"
            testValue = 'Inline-style:![alt text](https://github.com/adam-p/markdown-here/raw/master/src/common/images/icon48.png "Logo Title Text 1")\n\n'
            yield dict(event='start', data= role)
            for i in range(len(testValue)):
                collected_messages.append(testValue[i])
                yield dict(event='stream', data=testValue[i].replace('\n', '\\n'))
            content = ''.join(collected_messages)
            topic_chat = crud.create_topic_chat(db, topic_chat=schemas.TopicChatCreate(role=role, content=content), topic_id=topic_id)
            end_data = json.dumps({"id" : topic_chat.id, "remain_num": stats_count})
            yield dict(event='end', data=end_data)
        # assistant_chat = crud.create_topic_chat(db, topic_chat=schemas.TopicChatCreate(role=role, content=testValue), topic_id=topic_id)
        # return schemas.TopicChatExtend(topic_chat=assistant_chat, remain_count=rpd_amount - user_chat_stats.stats_value - 1)
        return EventSourceResponse(text_event_publisher(db=db, topic_id=topic_id, stats_count=rpd_amount - user_chat_stats.stats_value - 1))
    finally: 
        crud.increase_user_chat_stats(db, id=user_chat_stats.id)
        
# 添加问题反馈
@router.post("/{chat_id}/issue/create", response_model=schemas.TopicChatIssue)
def create_chat_issue(chat_id: int, chat_issue: schemas.TopicChatIssueCreate, current_user: Annotated[schemas.User, Depends(get_current_user)], db: Session = Depends(get_db)):
    chat_issue = crud.create_topic_chat_issue(db, user_id=current_user.id, chat_id=chat_id, topic_chat_issue=chat_issue)
    return chat_issue

# 修改问题反馈
@router.post("/{chat_id}/issue/update", response_model=schemas.TopicChatIssue)
def update_chat_issue(issue_update: schemas.TopicChatIssueUpdate, current_user: Annotated[schemas.User, Depends(get_current_user)], db: Session = Depends(get_db)):
    return crud.update_topic_chat_issue(db, topic_chat_issue=issue_update)

