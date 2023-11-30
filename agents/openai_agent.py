import os
import json
from agents.core import client, logger
from agents.tools import tools, tool_functions
from orm import schemas


def chat_completion(topic_chats: list[schemas.TopicChatCreate]):
    model_name = os.environ.get("MODEL_NAME")
    messages = []
    last_topic_chat = topic_chats[-1]
    if last_topic_chat.attachs and len(last_topic_chat.attachs) > 0:
        for topic_chat in topic_chats:
            role = topic_chat.role
            content = []
            content.append({"type": "text", "text": topic_chat.content})
            for attach in topic_chat.attachs:
                    if attach.content_type.startswith('image/'):
                        content.append({"type": "image_url", "image_url": {"url": attach.file_url}})
            messages.append({"role": role, "content": content})
        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=messages,
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
    tool_content = []
    is_function_call = False
    role = "assistant"

    for chunk in response:
        logger.warn(f"~~~~~~~~ chunk = {chunk}")
    return
    for chunk in response:
        logger.warn(f"chunk={chunk}")
        if is_function_call or chunk.choices[0].finish_reason == "tool_calls":
            is_function_call = True
            if chunk.choices[0].delta.content:
                tool_content.append(chunk.choices[0].delta.content)
            if chunk.choices[0].delta.role:
                role = chunk.choices[0].delta.role
        else:
            break
    if not is_function_call:
        return response


    # response_message = response.choices[0].message
    # if response_message.content is None:
    #     response_message.content = ""
    # if response_message.function_call is None:
    #     del response_message.function_call
    # tool_calls = response_message.tool_calls
    # if tool_calls:
    #     messages.append(response_message)  
    #     for tool_call in tool_calls:
    #         function_name = tool_call.function.name
    #         function_to_call = tool_functions[function_name]
    #         function_args = json.loads(tool_call.function.arguments)
    #         function_response = function_to_call(function_args)
    #         messages.append(
    #             {
    #                 "tool_call_id": tool_call.id,
    #                 "role": "tool",
    #                 "name": function_name,
    #                 "content": function_response,
    #             }
    #         )  
    # second_response = client.chat.completions.create(
    #     model=model_name,
    #     messages=messages,
    # )  
    # second_response_message = second_response.choices[0].message
    # return {"role": second_response_message.role, "content": second_response_message.content}