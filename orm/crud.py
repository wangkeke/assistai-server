from datetime import datetime
import uuid, sys
from sqlalchemy.orm import Session
from . import models, schemas

def get_email_code(db: Session, email: str, type: str, state: int):
    return db.query(models.EmailCode).filter(models.EmailCode.email == email, models.EmailCode.type == type, models.EmailCode.state == state).order_by(models.EmailCode.id.desc()).first()

def create_email_code(db: Session, email_code_create: schemas.EmailCodeCreate):
    db_email_code = models.EmailCode(**email_code_create.dict())
    db_email_code.create_time = datetime.now()
    db_email_code.state = 0
    db.add(db_email_code)
    db.commit()
    db.refresh(db_email_code)

def update_email_code(db: Session, email_code_update: schemas.EmailCodeUpdate):
    db.query(models.EmailCode).filter(models.EmailCode.id == email_code_update.id).update({'state': email_code_update.state})

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user_create: schemas.UserCreate):
    db_user = models.User(username=user_create.username, nickname=user_create.nickname, password=user_create.password)
    db_user.create_time = datetime.now()
    db_user.disabled = False
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate):
    update_columns = {}
    if user_update.nickname:
        update_columns['nickname'] = user_update.nickname
    if user_update.head_url:
        update_columns['head_url'] = user_update.head_url
    if user_update.last_login_time:
        update_columns['last_login_time'] = user_update.last_login_time
    if user_update.password:
        update_columns['password'] = user_update.password
    db.query(models.User).filter(models.User.id == user_id).update(update_columns)
    # db.commit()

def update_user_nickname(db: Session, user_id: int, nickname: str):
    db.query(models.User).filter(models.User.id == user_id).update({"nickname": nickname})
    # db.commit()

def update_user_last_login_time(db: Session, user_id: int):
    db.query(models.User).filter(models.User.id == user_id).update({"last_login_time": datetime.now()})
    # db.commit()

def create_user_set(db: Session, user_id: int, user_set_creates: list[schemas.UserSetCreate]):
    db_user_sets = []
    for usc in user_set_creates:
        db_user_set = models.UserSet(set_key=usc.set_key, set_value=usc.set_value, user_id=user_id)
        db_user_set.create_time = datetime.now()
        db_user_sets.append(db_user_set)
    db.add_all(db_user_sets)
    db.commit()
    return db_user_sets

def update_user_set(db: Session, user_id: int, user_set_update: schemas.UserSetUpdate):
    db.query(models.UserSet).filter(models.User.id == user_id, models.UserSet.set_key == user_set_update.set_key).update({"set_value": user_set_update.set_value})

def get_user_set(db: Session, user_id: int, set_key: str):
    if set_key:
        return db.query(models.UserSet).filter(models.UserSet.user_id == user_id).all()
    else:
        return db.query(models.UserSet).filter(models.UserSet.user_id == user_id, models.UserSet.set_key == set_key).all()

def get_topics(db: Session, user_id: int, skip: int = 0, limit: int = 10):
    return db.query(models.Topic).add_columns(models.Topic.id, models.Topic.title, models.Topic.last_active_time).filter(models.Topic.user_id==user_id, models.Topic.flag == True).order_by(models.Topic.last_active_time.desc()).offset(skip).limit(limit).all()

def get_topic_by_id(db: Session, user_id: int, topic_id: str):
    return db.query(models.Topic).filter(models.Topic.id==topic_id, models.Topic.user_id==user_id, models.Topic.flag == True).first()

def create_topic(db: Session, topic: schemas.TopicCreate, user_id: int):
    db_topic = models.Topic(**topic.dict(), id=str(uuid.uuid1()), flag= True, user_id= user_id, create_time=datetime.now(), last_active_time=datetime.now())
    db.add(db_topic)
    db.commit()
    db.refresh(db_topic)
    return db_topic

def update_topic(db: Session, topic: schemas.TopicUpdate, user_id: int):
    db.query(models.Topic).filter(models.Topic.id==topic.id, models.Topic.user_id==user_id).update({"title": topic.title, "turn": topic.turn})
    # db.commit()

def update_topic_last_active_time(db: Session, user_id: int, topic_id: str):
    db.query(models.Topic).filter(models.Topic.id==topic_id, models.Topic.user_id==user_id).update({"last_active_time": datetime.now()})
    # db.commit()

def delete_topic(db: Session, topic_id: str, user_id: int):
    db.query(models.Topic).filter(models.Topic.id==topic_id, models.Topic.user_id==user_id).update({"flag": False})
    # db.commit()

def get_topic_chats(db: Session, topic_id: str, next_chat_id: int = None, limit: int = 20):
    if next_chat_id:
        return db.query(models.TopicChat).filter(models.TopicChat.topic_id==topic_id, models.TopicChat.id < next_chat_id, models.TopicChat.flag == True).order_by(models.TopicChat.id.desc()).offset(0).limit(limit).all()
    else:
        return db.query(models.TopicChat).filter(models.TopicChat.topic_id==topic_id, models.TopicChat.flag == True).order_by(models.TopicChat.id.desc()).offset(0).limit(limit).all()

def create_topic_chat(db: Session, topic_chat: schemas.TopicChatCreate, topic_id: str, content_type: str = 'text'):
    topic_chat = models.TopicChat(role=topic_chat.role, content_type=content_type, content=topic_chat.content, topic_id=topic_id, create_time=datetime.now(), flag=True)
    db.add(topic_chat)
    db.commit()
    db.refresh(topic_chat)
    return topic_chat

def remove_topic_chat(db: Session, topic_id: str, chat_id: int):
    db.query(models.TopicChat).filter(models.TopicChat.topic_id==topic_id, models.TopicChat.id==chat_id, models.TopicChat.flag == True).update({"flag": False})
    # db.commit()

def create_topic_chat_issue(db: Session, user_id: int, topic_chat_issue: schemas.TopicChatIssueCreate):
    db_topic_chat_issue = models.TopicChatIssue(**topic_chat_issue.dict(), user_id=user_id, create_time=datetime.now())
    db.add(db_topic_chat_issue)
    db.commit()
    db.refresh(db_topic_chat_issue)
    return db_topic_chat_issue

def update_topic_chat_issue(db: Session, topic_chat_issue: schemas.TopicChatIssueUpdate):
    db.query(models.TopicChatIssue).filter(models.TopicChatIssue.id==topic_chat_issue.id).update({"type": topic_chat_issue.type, "detail": topic_chat_issue.detail})
    # db.commit()

def create_user_chat_stats(db: Session, user_id: int, user_chat_stats_create: schemas.UserChatStatsCreate):
    db_user_chat_stats = models.UserChatStats(user_id=user_id, stats_date = user_chat_stats_create.stats_date, 
                                              stats_key = user_chat_stats_create.stats_key,
                                              stats_value = user_chat_stats_create.stats_value)
    db_user_chat_stats.create_time = datetime.now()
    db.add(db_user_chat_stats)
    db.commit()
    db.refresh(db_user_chat_stats)
    return db_user_chat_stats

def increase_user_chat_stats(db: Session, id: int):
    db.query(models.UserChatStats).filter(models.UserChatStats.id == id).update({"stats_value": models.UserChatStats.stats_value+1})

def get_user_chat_stats(db: Session, user_id: int, stats_date: datetime, stats_key: str):
    return db.query(models.UserChatStats).filter(models.UserChatStats.user_id == user_id, models.UserChatStats.stats_date == stats_date,
                                          models.UserChatStats.stats_key == stats_key).first()