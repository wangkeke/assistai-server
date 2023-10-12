import os
from datetime import datetime, date, timedelta
import logging
import openai
from typing import Dict, List, Annotated
from fastapi import FastAPI, Cookie, Depends, Query, Request, status, HTTPException
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse
from orm import schemas, models, crud
from orm.database import SessionLocal, engine
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import jwt, JWTError
import smtplib
from email.mime.text import MIMEText
import random
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "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")
DOMAIN_NAME = os.environ.get("DOMAIN_NAME", "127.0.0.1:8000")
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-3.5-turbo")

# 配置日志
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARN)
logger = logging.getLogger(__name__)


# 生成数据库表结构
models.Base.metadata.create_all(bind=engine)
# 数据库连接依赖
def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


# Oauth2+JWT登录认证
SECRET_KEY = "fbaab29d8bdf2c43ec4488aab4e56c1a1bbc3cc4d8402eabb80131662760f1c4"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTE = 5 * 24 * 60
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(payload: dict, expires_delta: timedelta | None = None):
    to_encode = payload.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return schemas.User(id=int(payload.get('sub')), username=payload.get('name'))
    except JWTError as e:
        logger.error(e)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的登陆凭证", headers={"WWW-Authenticate": "Bearer"})


# 创建应用服务
app = FastAPI()
# 添加SessionMiddleware
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
templates = Jinja2Templates(directory="templates")
# 添加跨域中间件
origin = os.getenv("ORIGIN", "http://localhost:3000")
origins = [
    origin,
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 登录接口
@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):
        user = crud.get_user_by_username(db, username=form_data.username)
        if not user or not pwd_context.verify(form_data.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if user.disabled: 
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="账户已被停用",
            )
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTE)
        access_token = create_access_token(
            payload={"sub": str(user.id), "name": user.username}, expires_delta=access_token_expires
        )
        crud.update_user_last_login_time(db, user_id=user.id)
        return {"access_token": access_token, "username": user.username, "name": user.nickname, "auth_type": "bearer"}
        

# 发送邮箱验证码
# gmail: ykgk vzpk owed qdrv
# 163: MTHXNMDQCTAPMLZW
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.163.com")
EMAIL_SENDER = os.getenv("EMAIL_SENDER", "Assisai@163.com")
EMAIL_SECRET = os.getenv("EMAIL_SECRET", "TPTHAWIXNHHHRHRI") 
EMAIL_PORT = os.getenv("EMAIL_PORT", 25) 
async def send_email_captcha(to_email: str):
    # 生成6位随机验证码  
    code = random.randint(100000, 999999)
    msg = MIMEText(f"您的验证码是：{code}", 'plain', 'utf-8')
    msg['Subject'] = f"您的验证码是：{code}"
    msg['From'] = EMAIL_SENDER
    msg['To'] = to_email
    # 发送邮件
    with smtplib.SMTP_SSL(host=SMTP_SERVER, port=EMAIL_PORT) as server:
        server.login(EMAIL_SENDER, EMAIL_SECRET) 
        server.sendmail(
            EMAIL_SENDER, 
            to_email, 
            msg.as_string()
        )
    return code

# 发送邮箱注册码
@app.post('/send_email_regist_code')
async def send_email_regist_code(request: Request, send_email: schemas.SendEmail, db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, username=send_email.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )
    try:
        code = await send_email_captcha(to_email=send_email.email)
        crud.create_email_code(db, email_code_create=schemas.EmailCodeCreate(email=send_email.email, type="regist", code=code))
    except smtplib.SMTPException as e:
        logger.error(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="验证码发送失败，请检查邮箱是否正确"
        )

# 校验邮箱注册码
@app.post("/verify_email_regist_code")
async def verify_email_regist_code(request: Request, verify_email: schemas.VerifyEmail, db: Session = Depends(get_db)):
    email_code = crud.get_email_code(db, email=verify_email.email, type="regist", state=0)
    if not email_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱未验证"
        )
    if email_code.code != verify_email.captcha:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="验证码错误"
        )
    crud.update_email_code(db, email_code_update=schemas.EmailCodeUpdate(email=verify_email.email, id=email_code.id, state=1))

# 注册用户
@app.post("/regist_user")
async def regist_user(request: Request, user_create: schemas.UserCreate, db: Session = Depends(get_db)):
    email_code = crud.get_email_code(db, email=user_create.username, type="regist", state=1)
    if not email_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱未验证"
        )
    user = crud.get_user_by_username(db, username=user_create.username)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )
    user_create.password = pwd_context.hash(user_create.password)
    crud.create_user(db, user_create=user_create)

# 找回密码
@app.post('/send_email_reset_code')
async def send_email_reset_code(request: Request, send_email: schemas.SendEmail, db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, username=send_email.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该邮箱未注册"
        )
    try:
        code = await send_email_captcha(to_email=send_email.email)
        crud.create_email_code(db, email_code_create=schemas.EmailCodeCreate(email=send_email.email, type="reset", code=code))
    except smtplib.SMTPException as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请检查邮箱是否正确"
        )

# 校验邮箱验证码
@app.post("/verify_email_reset_code")
async def verify_email_reset_code(request: Request, verify_email: schemas.VerifyEmail, db: Session = Depends(get_db)):
    email_code = crud.get_email_code(db, email=verify_email.email, type="reset", state=0)
    if not email_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱未验证"
        )
    if email_code.code != verify_email.captcha:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="验证码错误"
        )
    crud.update_email_code(db, email_code_update=schemas.EmailCodeUpdate(email=verify_email.email, id=email_code.id, state=1))

# 重设密码
@app.post("/reset_password")
async def reset_password(request: Request, user_update: schemas.UserUpdate, db: Session = Depends(get_db)):
    email_code = crud.get_email_code(db, email=user_update.username, type="reset", state=1)
    if not email_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱未验证"
        )
    user = crud.get_user_by_username(db, username=user_update.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请检查邮箱是否正确"
        )
    user_update.password = pwd_context.hash(user_update.password)
    user_update.head_url = None
    user_update.last_login_time = None
    user_update.nickname = None
    crud.update_user(db, user_id=user.id, user_update=user_update)

# 修改昵称
@app.post("/modify_nickname")
async def modify_nickname(request: Request, nickname: str, current_user: Annotated[schemas.User, Depends(get_current_user)], db: Session = Depends(get_db)):
    crud.update_user_nickname(db, user_id=current_user.id, nickname=nickname)
    return {"name": nickname}

# 查询话题列表
@app.get("/get_topics", response_model=schemas.TimeTopicList)
async def get_topics(current_user: Annotated[schemas.User, Depends(get_current_user)], db: Session = Depends(get_db)):
    topics = crud.get_topics(db, user_id=current_user.id, skip=0, limit=50)
    today = date.today()
    week_ago = today - timedelta(weeks=1)
    todayTopics = []
    weekTopics = []
    monthTopics = []
    for topic in topics:
        if topic.last_active_time.date() >= today:
            todayTopics.append(topic)
        elif topic.last_active_time.date() >= week_ago:
            weekTopics.append(topic)
        else:
            monthTopics.append(topic)
    return {"todayTopics": todayTopics, "weekTopics": weekTopics, "monthTopics": monthTopics}


# 创建话题
@app.post("/create_topic", response_model=schemas.Topic)
def create_topic(topic_create: schemas.TopicCreate, current_user: Annotated[schemas.User, Depends(get_current_user)], db: Session = Depends(get_db)):
    topic = crud.create_topic(db, topic=topic_create, user_id=current_user.id)
    return topic

# 更新话题标题
@app.post("/update_topic/{topic_id}")
async def update_topic(topic_id: str , topic_update: schemas.TopicUpdate, current_user: Annotated[schemas.User, Depends(get_current_user)], db: Session = Depends(get_db)):
    crud.update_topic(db, topic=topic_update, user_id=current_user.id)

# 删除话题
@app.get('/remove_topic/{topic_id}')
async def remove_topic(topic_id: str, current_user: Annotated[schemas.User, Depends(get_current_user)], db: Session = Depends(get_db)):
    crud.delete_topic(db, topic_id=topic_id, user_id=current_user.id)

# 查询话题详情
@app.get("/topic/{topic_id}", response_model=schemas.Topic)
async def get_topic(topic_id: str, current_user: Annotated[schemas.User, Depends(get_current_user)], db: Session = Depends(get_db)):
    crud.update_topic_last_active_time(db, user_id=current_user.id, topic_id=topic_id)
    topic = crud.get_topic_by_id(db, user_id=current_user.id, topic_id=topic_id)
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="话题不存在或已删除"
        )
    return topic

# 查询话题下的聊天记录分页列表
@app.get("/topic/{topic_id}/chat", response_model=list[schemas.TopicChat])
async def page_topic_chats(topic_id: str, current_user: Annotated[schemas.User, Depends(get_current_user)], next_chat_id: int = None, limit: int = None, db: Session = Depends(get_db)):
    return crud.get_topic_chats(db, topic_id=topic_id, next_chat_id=next_chat_id, limit=limit)

# 添加聊天记录
@app.post("/topic/{topic_id}/add_chat")
def add_chat(topic_id: str, chat_create: schemas.TopicChatCreate, current_user: Annotated[schemas.User, Depends(get_current_user)], db: Session = Depends(get_db)):
    return crud.create_topic_chat(db, topic_chat=chat_create, topic_id=topic_id)

# 删除聊天信息
@app.get('/topic/{topic_id}/remove_chat')
def remove_chat(topic_id: str, id: str , current_user: Annotated[schemas.User, Depends(get_current_user)], db: Session = Depends(get_db)):
    crud.remove_topic_chat(db, topic_id=topic_id, chat_id=id)

# 生成图像函数
def create_image(prompt: str):
    """Generate images for user"""
    response = openai.Image.create(
        api_key= OPENAI_API_KEY,
        prompt= prompt,
        n=1,
        size="512x512",
        response_format="b64_json"
    )
    return response['data'][0]['b64_json']

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
def event_publisher(chunks, db: Session, topic_id: str):
    collected_messages = []
    role = None
    for chunk in chunks:
        logger.info(chunk)
        delta = chunk['choices'][0]['delta']
        if delta.get('role'):
            role = delta.get('role')
            yield dict(event='start', data= role)
        if delta.get('content'):
            content = delta.get('content')
            collected_messages.append(content)
            yield dict(event='stream', data=content.replace('\n', '\\n'))
    contents = ''.join(collected_messages)
    assistant_chat = crud.create_topic_chat(db, topic_chat=schemas.TopicChatCreate(role=role, content=contents), topic_id=topic_id)
    yield dict(event='end', data=assistant_chat.id)

# 聊天交互接口
@app.post("/topic/{topic_id}/chat_conversation")
def chat(topic_id: str, chat_creates: list[schemas.TopicChatCreate], current_user: Annotated[schemas.User, Depends(get_current_user)], db: Session = Depends(get_db)):
    response = openai.ChatCompletion.create(model = MODEL_NAME, 
                                 api_key = OPENAI_API_KEY,
                                 messages = jsonable_encoder(chat_creates),
                                 stream = True,
                                 functions = functions,
                                 function_call = "auto"
                                 )
    return EventSourceResponse(event_publisher(response, db=db, topic_id=topic_id))

# 聊天交互测试接口
@app.post("/topic/{topic_id}/chat_conversation_test")
def chats(topic_id: str, chat_creates: list[schemas.TopicChatCreate], current_user: Annotated[schemas.User, Depends(get_current_user)], db: Session = Depends(get_db)):
    def gp(db: Session, topic_id: str):
        collected_messages = []
        role = "assistant"
        testValue = "下面是一个用Python写的斐波那契函数，其参数是n：\n\n```python\ndef fibonacci(n):\n    if n <= 0:\n        return []\n    elif n == 1:\n        return [0]\n    else:\n        sequence = [0, 1]\n        while len(sequence) < n:\n            next_number = sequence[-1] + sequence[-2]\n            sequence.append(next_number)\n        return sequence\n```\n\n这个函数将返回一个包含n个斐波那契数列的列表。如果n小于等于0，将返回一个空列表。如果n等于1，将返回一个只包含0的列表。否则，函数将使用循环构建斐波那契数列，直到列表达到n个元素。\n"
        yield dict(event='start', data= jsonable_encoder(chat_creates))
        for i in range(len(testValue)):
            collected_messages.append(testValue[i])
            yield dict(event='stream', data=testValue[i].replace('\n', '\\n'))
        contents = ''.join(collected_messages)
        assistant_chat = crud.create_topic_chat(db, topic_chat=schemas.TopicChatCreate(role=role, content=contents), topic_id=topic_id)
        yield dict(event='end', data=assistant_chat.id)
    return EventSourceResponse(gp(db=db, topic_id=topic_id))
        

# 添加问题反馈
@app.post("/create_chat_issue", response_model=schemas.TopicChatIssue)
def create_chat_issue(chat_issue: schemas.TopicChatIssueCreate, current_user: Annotated[schemas.User, Depends(get_current_user)], db: Session = Depends(get_db)):
    chat_issue = crud.create_topic_chat_issue(db, user_id=current_user.id, topic_chat_issue=chat_issue)
    return chat_issue

# 修改问题反馈
@app.post("/update_chat_issue")
def update_chat_issue(issue_update: schemas.TopicChatIssueUpdate, current_user: Annotated[schemas.User, Depends(get_current_user)], db: Session = Depends(get_db)):
    crud.update_topic_chat_issue(db, topic_chat_issue=issue_update)





if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)