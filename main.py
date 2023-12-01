import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from orm import models
from orm.database import engine
from fastapi.openapi.docs import (
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.middleware.cors import CORSMiddleware
from routers import user, topic, chat, upload, agent

# 默认，免费用户每日请求最大次数
os.environ["DEFAULT_REQUEST_PER_DAY"] = "10"
# Oauth2+JWT登录认证
OAUTH2_SECRET_KEY = "fbaab29d8bdf2c43ec4488aab4e56c1a1bbc3cc4d8402eabb80131662760f1c4"
os.environ["OAUTH2_SECRET_KEY"] = OAUTH2_SECRET_KEY
os.environ["OAUTH2_ALGORITHM"] = "HS256"
# openai默认日志等级
os.environ.setdefault("OPENAI_LOG", "debug")
os.environ["OPENAI_LOG"] = "debug"
# os.environ["MODEL_NAME"] = "gpt-4-1106-preview"
# os.environ["MODEL_NAME"] = "gpt-3.5-turbo-1106"
os.environ["MODEL_NAME"] = os.environ.get("MODEL_NAME", "gpt-3.5-turbo-1106")

# 生成数据库表结构
models.Base.metadata.create_all(bind=engine)

# 创建应用服务
app = FastAPI(docs_url=None, redoc_url=None)
DATA_PATH = os.getenv("DATA_PATH", "/home/lighthouse/workspace/data/")
if not os.path.exists(DATA_PATH):
    os.makedirs(DATA_PATH, exist_ok=True)
app.mount(path="/static", app=StaticFiles(directory=DATA_PATH), name="static")
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
app.include_router(upload.router)
app.include_router(agent.router)

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui.css",
    )

@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)