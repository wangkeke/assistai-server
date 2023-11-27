import os
from datetime import timedelta
from typing import Annotated
from fastapi import Depends, Request, status, HTTPException, APIRouter
from sqlalchemy.orm import Session
from orm import schemas, crud
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext
import smtplib
from email.mime.text import MIMEText
import random
from dependencies import get_db, create_access_token, get_current_user

# 发送邮箱验证码
# gmail: ykgk vzpk owed qdrv
# 163: MTHXNMDQCTAPMLZW
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.163.com")
EMAIL_SENDER = os.getenv("EMAIL_SENDER", "Assisai@163.com")
EMAIL_SECRET = os.getenv("EMAIL_SECRET", "TPTHAWIXNHHHRHRI") 
EMAIL_PORT = os.getenv("EMAIL_PORT", 25) 

router = APIRouter(
    prefix="/user", 
    tags=["user"], 
    responses={404 : {"description": "Not Found"}}
    )

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# 用户登录
@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):
        user = crud.get_user_by_username(db, username=form_data.username)
        if not user or not pwd_context.verify(form_data.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email or password is incorrect.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if user.disabled: 
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email has been disabled.",
            )
        access_token_expires = timedelta(minutes=5 * 24 * 60)
        access_token = create_access_token(
            payload={"sub": str(user.id), "name": user.username}, expires_delta=access_token_expires
        )
        crud.update_user_last_login_time(db, user_id=user.id)
        return {"access_token": access_token, "username": user.username, "name": user.nickname, "auth_type": "bearer"}

# 发送邮箱验证码
async def send_email_captcha(to_email: str):
    # 生成6位随机验证码  
    code = random.randint(100000, 999999)
    msg = MIMEText(f"Your verification code is {code}", 'plain', 'utf-8')
    msg['Subject'] = f"Your verification code is {code}"
    msg['From'] = EMAIL_SENDER
    msg['To'] = to_email
    # 发送邮件
    if EMAIL_PORT == 25:
        with smtplib.SMTP(host=SMTP_SERVER, port=EMAIL_PORT) as smtp:
            smtp.login(EMAIL_SENDER,EMAIL_SECRET)
            smtp.sendmail(EMAIL_SENDER, to_email, msg.as_string())
    else:
        with smtplib.SMTP_SSL(host=SMTP_SERVER, port=EMAIL_PORT) as server:
            server.login(EMAIL_SENDER, EMAIL_SECRET) 
            server.sendmail(
                EMAIL_SENDER, 
                to_email, 
                msg.as_string()
            )
    return code

# 发送邮箱注册码
@router.post('/send_email_regist_code')
async def send_email_regist_code(request: Request, send_email: schemas.SendEmail, db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, username=send_email.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email has been registered."
        )
    try:
        code = await send_email_captcha(to_email=send_email.email)
        crud.create_email_code(db, email_code_create=schemas.EmailCodeCreate(email=send_email.email, type="regist", code=code))
    except smtplib.SMTPException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The verification code failed to be sent, please check whether the email is correct."
        )

# 校验邮箱注册码
@router.post("/verify_email_regist_code")
async def verify_email_regist_code(request: Request, verify_email: schemas.VerifyEmail, db: Session = Depends(get_db)):
    email_code = crud.get_email_code(db, email=verify_email.email, type="regist", state=0)
    if not email_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is not verified."
        )
    if email_code.code != verify_email.captcha:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Regist code error."
        )
    crud.update_email_code(db, email_code_update=schemas.EmailCodeUpdate(email=verify_email.email, id=email_code.id, state=1))

# 注册用户
@router.post("/regist_user")
async def regist_user(request: Request, user_create: schemas.UserCreate, db: Session = Depends(get_db)):
    email_code = crud.get_email_code(db, email=user_create.username, type="regist", state=1)
    if not email_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is not verified."
        )
    user = crud.get_user_by_username(db, username=user_create.username)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email has been registered."
        )
    user_create.password = pwd_context.hash(user_create.password)
    user = crud.create_user(db, user_create=user_create)
    crud.create_user_set(db, user_id=user.id, user_set_creates=[schemas.UserSetCreate(set_key='RPD', set_value=int(os.getenv("DEFAULT_REQUEST_PER_DAY")))])

# 找回密码
@router.post('/send_email_reset_code')
async def send_email_reset_code(request: Request, send_email: schemas.SendEmail, db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, username=send_email.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is not registered."
        )
    try:
        code = await send_email_captcha(to_email=send_email.email)
        crud.create_email_code(db, email_code_create=schemas.EmailCodeCreate(email=send_email.email, type="reset", code=code))
    except smtplib.SMTPException as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The verification code failed to be sent, please check whether the email is correct."
        )

# 校验邮箱验证码
@router.post("/verify_email_reset_code")
async def verify_email_reset_code(request: Request, verify_email: schemas.VerifyEmail, db: Session = Depends(get_db)):
    email_code = crud.get_email_code(db, email=verify_email.email, type="reset", state=0)
    if not email_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is not verified."
        )
    if email_code.code != verify_email.captcha:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Captcha error."
        )
    crud.update_email_code(db, email_code_update=schemas.EmailCodeUpdate(email=verify_email.email, id=email_code.id, state=1))

# 重设密码
@router.post("/reset_password")
async def reset_password(request: Request, user_update: schemas.UserUpdate, db: Session = Depends(get_db)):
    email_code = crud.get_email_code(db, email=user_update.username, type="reset", state=1)
    if not email_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is not verified."
        )
    user = crud.get_user_by_username(db, username=user_update.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is not registered."
        )
    user_update.password = pwd_context.hash(user_update.password)
    user_update.head_url = None
    user_update.last_login_time = None
    user_update.nickname = None
    crud.update_user(db, user_id=user.id, user_update=user_update)

# 修改昵称
@router.post("/modify_nickname")
async def modify_nickname(request: Request, nickname: str, current_user: Annotated[schemas.User, Depends(get_current_user)], db: Session = Depends(get_db)):
    crud.update_user_nickname(db, user_id=current_user.id, nickname=nickname)
    return {"name": nickname}