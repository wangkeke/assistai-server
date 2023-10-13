from datetime import datetime
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, DateTime, TIMESTAMP
from sqlalchemy.orm import relationship
from .database import Base

class EmailCode(Base):
    __tablename__ = "email_code"
    
    id = Column(Integer, primary_key=True)
    email = Column(String(50), index=True)
    type = Column(String(50), index=True)
    code = Column(Integer)
    state = Column(Integer)
    update_time = Column(TIMESTAMP)
    create_time = Column(TIMESTAMP)

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), index=True)
    nickname = Column(String(50), index=True)
    password = Column(String(255))
    head_url = Column(String(50))
    disabled = Column(Boolean)
    last_login_time = Column(DateTime)
    update_time = Column(TIMESTAMP)
    create_time = Column(TIMESTAMP)
    sets = relationship("UserSet", back_populates="user")

class UserSet(Base):
    __tablename__ = 'user_set'

    id = Column(Integer, primary_key=True)
    set_key = Column(String(50), index=True)
    set_value = Column(String(255))
    update_time = Column(TIMESTAMP)
    create_time = Column(TIMESTAMP)
    user_id = Column(Integer, ForeignKey("user.id"))
    user = relationship("User", back_populates="sets")

class Topic(Base):
    __tablename__ = 'topic'

    id = Column(String(50), primary_key=True)
    title = Column(Text)
    turn = Column(Integer)
    flag = Column(Boolean)
    last_active_time = Column(DateTime)
    update_time = Column(TIMESTAMP)
    create_time = Column(TIMESTAMP)
    user_id = Column(Integer, ForeignKey("user.id"))

class TopicChat(Base):
    __tablename__ = 'topic_chat'

    id = Column(Integer, primary_key=True)
    role = Column(String(20))
    content_type = Column(String(50))
    content = Column(Text)
    flag = Column(Boolean)
    create_time = Column(TIMESTAMP)
    topic_id = Column(String(50), ForeignKey("topic.id"))
    topic = relationship("Topic")
    topic_chat_issues = relationship("TopicChatIssue", back_populates="topic_chat")

class TopicChatIssue(Base):
    __tablename__ = 'topic_chat_issue'

    id = Column(Integer, primary_key=True)
    type = Column(String(50))
    detail = Column(Text)
    update_time = Column(TIMESTAMP)
    create_time = Column(TIMESTAMP)
    user_id = Column(Integer, ForeignKey("user.id"))
    user = relationship("User")
    topic_chat_id = Column(Integer, ForeignKey("topic_chat.id"))
    topic_chat = relationship("TopicChat", back_populates="topic_chat_issues")
