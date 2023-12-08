import os
import json
from agents.core import client, logger
from agents.tools import tools, tool_functions
from orm import schemas
from agents.util import encode_image



def chat_completion(topic_chats: list[schemas.TopicChatCreate]):
    model_name = os.environ.get("MODEL_NAME")
    messages = [{"role":"system","content":'1. Never ignore the results of the tool.\n2. In the case of an image, use the following format to display it: ![Image Alt](Image Link "Image Title")'}]
    last_topic_chat = topic_chats[-1]
    if last_topic_chat.attachs and len(last_topic_chat.attachs) > 0:
        for topic_chat in topic_chats:
            role = topic_chat.role
            content = []
            content.append({"type": "text", "text": topic_chat.content})
            for attach in topic_chat.attachs:
                    if attach.content_type.startswith('image/'):
                        content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(image_url=attach.file_url)}"}})
            messages.append({"role": role, "content": content})
        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=messages,
            max_tokens=1500,
            stream=True       
        )
        return response
    
    for topic_chat in topic_chats:
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
    for tool_call in tool_calls:
        function_name = tool_call.function.name
        function_to_call = tool_functions[function_name]
        function_args = json.loads(tool_call.function.arguments)
        function_response = function_to_call(function_args)
        messages.append(
            {
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": function_response,
            }
        )  
    return client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        #model=model_name,
        messages=messages,
        stream=True
    )  
