import os
import json
import logging
from agents.core import client
from agents.tools import tools, tool_functions

log = logging.getLogger(__name__)

def chat_completion(messages: list[dict]):
    model_name = os.environ.get("MODEL_NAME")
    log.info(f"model_name = {model_name}, messages={messages}")
    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        tools=tools,
        tool_choice="auto",  # auto is default, but we'll be explicit
    )
    log.info(f"response = {response}")
    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls
    function_responses = []
    # Step 2: check if the model wanted to call a function
    if tool_calls:
        # Step 3: call the function
        # Note: the JSON response may not always be valid; be sure to handle errors
        new_messages = []
        new_messages.append(response_message)  # extend conversation with assistant's reply
        # Step 4: send the info for each function call and function response to the model
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = tool_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            function_response = function_to_call(function_args)
            # function_responses.append(function_response)
            new_messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                }
            )  # extend conversation with function response
        second_response = client.chat.completions.create(
            model=model_name,
            messages=new_messages,
        )  # get a new response from the model where it can see the function response
        second_response_message = second_response.choices[0].message
        return {"role": second_response_message.role, "content": second_response_message.content}
        # return {"role": response_message.role, "content": "\n\n".join(function_responses)}
    else:
        return {"role": response_message.role, "content": response_message.content}