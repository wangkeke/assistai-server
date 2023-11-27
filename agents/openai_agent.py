import os
import json
from agents.core import client
from agents.tools import tools, tool_functions


def chat_completion(messages: list[dict], turn_count: int = 0):
    model_name = os.environ.get("MODEL_NAME")
    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        tools=tools,
        tool_choice="auto",  # auto is default, but we'll be explicit
    )
    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls
    # Step 2: check if the model wanted to call a function
    if tool_calls and turn_count < len(tool_calls)+1:
        # Step 3: call the function
        # Note: the JSON response may not always be valid; be sure to handle errors
        messages.append(response_message)  # extend conversation with assistant's reply
        # Step 4: send the info for each function call and function response to the model
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
            )  # extend conversation with function response
        turn_count += 1
        return chat_completion(messages=messages, turn_count=turn_count)
    else:
        return response_message
