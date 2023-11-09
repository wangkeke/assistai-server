import os
from datetime import datetime, timedelta
from typing import Annotated
from fastapi import Depends, status, HTTPException
from orm.database import SessionLocal
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from orm import schemas


# 获取数据库连接依赖
def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/token")
# 获取当前登录用户依赖
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    try:
        payload = jwt.decode(token, os.getenv("OAUTH2_SECRET_KEY"), algorithms=[os.getenv("OAUTH2_ALGORITHM")])
        return schemas.User(id=int(payload.get('sub')), username=payload.get('name'))
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的登陆凭证", headers={"WWW-Authenticate": "Bearer"})

# 创建token
def create_access_token(payload: dict, expires_delta: timedelta | None = None):
    to_encode = payload.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, os.getenv("OAUTH2_SECRET_KEY"), algorithm=os.getenv("OAUTH2_ALGORITHM"))
    return encoded_jwt