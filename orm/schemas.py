from datetime import datetime
from pydantic import BaseModel, EmailStr
from fastapi import Query

class EmailCodeBase(BaseModel):
    email: EmailStr

class EmailCodeCreate(EmailCodeBase):
    type: str
    code: int

class EmailCodeUpdate(EmailCodeBase):
    id: int
    state: int

class UserBase(BaseModel):
    username: str

class UserSetBase(BaseModel):
    set_key: str
    set_value: str

class UserCreate(UserBase):
    nickname: str = Query(min_length=1, max_length=50)
    password: str = Query(min_length=6, max_length=50)

class UserUpdate(UserBase):
    nickname: str | None = Query(min_length=1, max_length=50)
    password: str | None = Query(min_length=6, max_length=50)
    head_url: str | None = Query(max_length=255)
    last_login_time: datetime | None

class User(UserBase):
    id: int
    nickname: str | None = Query(min_length=1, max_length=50)
    password: str | None = Query(min_length=6, max_length=50)
    head_url: str | None
    last_login_time: datetime | None
    sets: list[UserSetBase] = []
    class Config:
        orm_mode = True

class UserSetCreate(UserSetBase):
    pass

class TopicBase(BaseModel):
    title: str = Query(max_length=500)
    turn: int | None = Query(max = 10, min = 0)

class TopicCreate(TopicBase):
    pass

class TopicUpdate(TopicBase):
    id: str

class TopicChatBase(BaseModel):
    role: str = Query(default="user", regex="^(system)|(assistant)|(user)$")
    content: str = Query(default=..., min_length=1)

class TopicChatCreate(TopicChatBase):
    pass

class TopicChatDelete(BaseModel):
    id: int

class TopicChatIssueBase(BaseModel):
    type: str = Query(max_length=50)
    detail: str

class TopicChatIssueCreate(TopicChatIssueBase):
    topic_chat_id: int

class TopicChatIssueUpdate(TopicChatIssueBase):
    id: int

class TopicChatIssue(TopicChatIssueBase):
    id: int
    topic_chat_id: int
    create_time: datetime
    class Config:
        orm_mode = True

class TopicChat(TopicChatBase):
    id: int
    content_type: str = None
    create_time: datetime
    topic_chat_issues: list[TopicChatIssue] = []
    class Config:
        orm_mode = True

class Topic(TopicBase):
    id: str
    last_active_time: datetime
    class Config:
        orm_mode = True

class TopicChats(BaseModel):
    topic: Topic = None
    chats: list[TopicChat] = []

class TimeTopicList(BaseModel):
    todayTopics: list[Topic] = []
    weekTopics: list[Topic] = []
    monthTopics: list[Topic] = []
    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    name: str
    username: str

class SendEmail(BaseModel):
    email: EmailStr

class VerifyEmail(SendEmail):
    captcha: int = Query(min=100000, max=999999)