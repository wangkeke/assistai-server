import logging
from fastapi import Request, Depends, APIRouter
from agents.core import client


router = APIRouter(
    prefix="/agent", 
    tags=["agent"], 
    responses={404 : {"description": "Not Found"}}
)

log = logging.getLogger(__name__)

# openai代理
@router.post("/openai/chat/completions")
async def openai_agent(request: Request):
    json_data = await request.json()
    model_name = json_data['model']
    messages = json_data['messages']
    stream = False
    if json_data.get("stream"):
        stream = json_data.get("stream")
    if json_data.get("tools"):
        tool_choice = "auto"
        if json_data.get("tool_choice"):
            tool_choice = json_data.get("tool_choice")
        return client.chat.completions.create(
            model=model_name,
            messages=messages,
            tools=json_data.get("tools"),
            tool_choice=tool_choice,
            stream=stream
        )
    else:
        return client.chat.completions.create(
            model=model_name,
            messages=messages,
            stream=stream
        )