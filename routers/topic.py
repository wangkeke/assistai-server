from datetime import date, timedelta
from typing import Annotated
from fastapi import Depends, status, HTTPException, APIRouter
from sqlalchemy.orm import Session
from orm import schemas, crud
from dependencies import get_db, get_current_user

router = APIRouter(
    prefix="/topic", 
    tags=["topic"], 
    responses={404 : {"description": "Not Found"}}
    )


# 查询话题列表
@router.get("/list", response_model=schemas.TimeTopicList)
async def get_topics(current_user: Annotated[schemas.User, Depends(get_current_user)], db: Session = Depends(get_db)):
    topics = crud.get_topics(db, user_id=current_user.id, skip=0, limit=100)
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
@router.post("/create", response_model=schemas.Topic)
def create_topic(topic_create: schemas.TopicCreate, current_user: Annotated[schemas.User, Depends(get_current_user)], db: Session = Depends(get_db)):
    topic = crud.create_topic(db, topic=topic_create, user_id=current_user.id)
    return topic

# 更新话题标题
@router.post("/update/{topic_id}")
async def update_topic(topic_id: str , topic_update: schemas.TopicUpdate, current_user: Annotated[schemas.User, Depends(get_current_user)], db: Session = Depends(get_db)):
    crud.update_topic(db, topic=topic_update, user_id=current_user.id)

# 删除话题
@router.get('/remove/{topic_id}')
async def remove_topic(topic_id: str, current_user: Annotated[schemas.User, Depends(get_current_user)], db: Session = Depends(get_db)):
    crud.delete_topic(db, topic_id=topic_id, user_id=current_user.id)

# 查询话题详情
@router.get("/get/{topic_id}", response_model=schemas.Topic)
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
@router.get("/{topic_id}/chats", response_model=list[schemas.TopicChat])
async def page_topic_chats(topic_id: str, current_user: Annotated[schemas.User, Depends(get_current_user)], next_chat_id: int = None, limit: int = None, db: Session = Depends(get_db)):
    return crud.get_topic_chats(db, topic_id=topic_id, next_chat_id=next_chat_id, limit=limit)
