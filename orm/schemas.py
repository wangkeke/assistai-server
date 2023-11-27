from datetime import datetime, date
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

class UserSetUpdate(UserSetBase):
    pass

class TopicChatAttachBase(BaseModel):
    file_etag: str = Query(max_length=255)
    file_name: str = Query(min_length=3, max_length=255)
    file_size: int = Query(min=0)
    file_url: str = Query(min_length=1, max_length=500)
    content_type: str = None
    file_format: str = Query(min_length=1)

class TopicChatAttach(TopicChatAttachBase):
    id: int
    class Config:
        orm_mode = True

class TopicBase(BaseModel):
    title: str | None = Query(max_length=500)
    turn: int | None = Query(max = 10, min = 0)

class TopicCreate(TopicBase):
    attachs: list[TopicChatAttachBase] = []

class TopicUpdate(TopicBase):
    id: str

class TopicChatBase(BaseModel):
    role: str = Query(default="user", regex="^(system)|(assistant)|(user)$")
    content: str | None

class TopicChatCreate(TopicChatBase):
    attachs: list[TopicChatAttachBase] = []
    class Config:
        orm_mode = True

class TopicChatDelete(BaseModel):
    id: int

class TopicChatIssueBase(BaseModel):
    type: str = Query(max_length=50)
    detail: str

class TopicChatIssueCreate(TopicChatIssueBase):
    pass

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
    attachs: list[TopicChatAttach] = []
    class Config:
        orm_mode = True

class TopicChatExtend(BaseModel):
    topic_chat: TopicChat
    remain_count: int = None
    class Config:
        orm_mode = True

class Topic(TopicBase):
    id: str
    last_active_time: datetime = None
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

class UserChatStatsBase(BaseModel):
    stats_date: date
    stats_key: str
    stats_value: int

class UserChatStatsCreate(UserChatStatsBase):
    pass
    
class Message(BaseModel):
    role: str = Query(default="user", regex="^(system)|(assistant)|(user)$")
    content: str = Query(default=...)
