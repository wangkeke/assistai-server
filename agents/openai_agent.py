import os
import json
from typing import List
from agents.core import client, logger
from agents.tools import tools, tool_functions
from orm import schemas
from agents.util import execute
import asyncio


def chat_completion(user_id: int, user_partition: str, topic_chats: list[schemas.TopicChatCreate]):
    model_name = os.environ.get("MODEL_NAME")
    messages = [{"role":"system","content":'1. Never ignore the results of the tool.\n2. In the case of an image, use the following format to display it: ![Image Alt](Image Link "Image Title")'}]
    last_topic_chat = topic_chats[-1]
    attachs = []
    for i, attach in enumerate(last_topic_chat.attachs):
        attachs.append(f"{i+1}. {attach.file_url}")
    text = last_topic_chat.content
    if len(attachs)>0:
        last_topic_chat.content = text + "\n\nList of uploaded files：" + "\n".join(attachs)
    character_count = 0
    for topic_chat in topic_chats:
        character_count += len(topic_chat.content)
        messages.append({"role": topic_chat.role, "content": topic_chat.content})

    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        tools=tools,
        tool_choice="auto",  # auto is default, but we'll be explicit
        stream=True
    )
    is_function_call = False
    tool_calls = []
    role = None
    for chunk in response:
        if not role and chunk.choices[0].delta.role:
            role = chunk.choices[0].delta.role
        if is_function_call or chunk.choices[0].delta.tool_calls:
            is_function_call = True
            if chunk.choices[0].delta.tool_calls:
                if chunk.choices[0].delta.tool_calls[0].id:
                    tool_calls.append(chunk.choices[0].delta.tool_calls[0])
                else:
                    tool_calls[-1].function.arguments += chunk.choices[0].delta.tool_calls[0].function.arguments
        else:
            break

    if not is_function_call:
        return response
    
    messages.append({"role": role, "content": "", "tool_calls": tool_calls})
    logger.warn(f"tool_calls : {len(tool_calls)} = {tool_calls}, messages = {messages}")
    tool_function_messages = []
    for tool_call in tool_calls:
        function_name = tool_call.function.name
        function_to_call = tool_functions[function_name]
        function_args = json.loads(tool_call.function.arguments)
        tool_function_messages.append(
            {
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "funciton_call": function_to_call(user_id=user_id, user_partition=user_partition, content=text, tool_args=function_args),
            }
        )
    results = asyncio.run(
        execute(*list(tool_function_message["funciton_call"] 
                      for tool_function_message in tool_function_messages)))
    for i, result in enumerate(results):
        character_count += len(result)
        tool_function_messages[i]["content"] = result
        del tool_function_messages[i]["funciton_call"]
    messages.extend(tool_function_messages)
    model = "gpt-3.5-turbo-1106"
    if character_count>4000:
        model = "gpt-3.5-turbo-16k"
    return client.chat.completions.create(
        model= model,
        #model=model_name,
        messages=messages,
        stream=True
    )  