import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from orm import models
from orm.database import engine
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from routers import user, topic, chat

# 默认，免费用户每日请求最大次数
os.environ["DEFAULT_REQUEST_PER_DAY"] = "2"
# Oauth2+JWT登录认证
OAUTH2_SECRET_KEY = "fbaab29d8bdf2c43ec4488aab4e56c1a1bbc3cc4d8402eabb80131662760f1c4"
os.environ["OAUTH2_SECRET_KEY"] = OAUTH2_SECRET_KEY
os.environ["OAUTH2_ALGORITHM"] = "HS256"

# 生成数据库表结构
models.Base.metadata.create_all(bind=engine)

# 创建应用服务
app = FastAPI()
STATIC_PATH = "/static"
DISK_PATH = os.getenv("DISK_PATH", "/home/data")
DEFAULT_TEMP_PATH = os.getenv("DEFAULT_TEMP_PATH", "/opt/render/project/src")
if not os.path.exists(DEFAULT_TEMP_PATH):
    os.makedirs(DEFAULT_TEMP_PATH)
os.environ["STATIC_PATH"] = STATIC_PATH
app.mount(path=STATIC_PATH, app=StaticFiles(directory=DISK_PATH), name="static")
app.mount(path="/public", app=StaticFiles(directory=DEFAULT_TEMP_PATH), name="public")
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

app.include_router(user.router)
app.include_router(topic.router)
app.include_router(chat.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)