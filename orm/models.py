from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, DateTime, TIMESTAMP, Date, BigInteger
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
    attachs: list = relationship("TopicChatAttach", back_populates="topic_chat")
    topic_chat_issues: list = relationship("TopicChatIssue", back_populates="topic_chat")

class TopicChatAttach(Base):
    __tablename__ = 'topic_chat_attach'
    
    id = Column(Integer, primary_key=True)
    file_etag = Column(String(255))
    file_name = Column(String(255))
    file_size = Column(BigInteger)
    file_url = Column(String(500))
    content_type = Column(String(255))
    file_format = Column(String(20))
    topic_chat_id = Column(Integer, ForeignKey("topic_chat.id"))
    topic_chat = relationship("TopicChat", back_populates="attachs")


class UserChatStats(Base):
    __tablename__ = 'user_chat_stats'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    stats_date = Column(Date)
    stats_key = Column(String(50))
    stats_value = Column(Integer)
    update_time = Column(TIMESTAMP)
    create_time = Column(TIMESTAMP)

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

class UserFile(Base):
    """用户上传到平台的文件表"""
    __tablename__ = "user_file"

    id = Column(Integer, primary_key=True)
    file_etag = Column(String(255))
    file_name = Column(String(255))
    content_type = Column(String(255))
    file_format = Column(String(20))
    file_size = Column(BigInteger)
    file_url = Column(String(255))
    flag = Column(Boolean)
    update_time = Column(TIMESTAMP)
    create_time = Column(TIMESTAMP)
    user_id = Column(Integer, ForeignKey("user.id"))

class UserImage(Base):
    """用户生成的图片"""
    __tablename__ = "user_image"

    id = Column(Integer, primary_key=True)
    prompt = Column(Text)
    quality = Column(String(20))
    size = Column(String(20))
    style=Column(String(20))
    revised_prompt = Column(Text)
    image_url = Column(String(255))
    update_time = Column(TIMESTAMP)
    create_time = Column(TIMESTAMP)
    user_id = Column(Integer, ForeignKey("user.id"))
