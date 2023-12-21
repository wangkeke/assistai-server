import os
import base64
import asyncio
import tiktoken
import nest_asyncio
nest_asyncio.apply()


# Function to encode the image
def encode_image(image_path: str):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

def abatch_tasks(tool_functions: list):
  return asyncio.run(execute(tool_functions))

def execute(tool_functions: list):
  return asyncio.gather(*tool_functions)

def max_encoding_tokens(encoding_name: str = "gpt-3.5-turbo") -> int:
  """Returns the max of tokens for a encoding."""
  encoding = tiktoken.encoding_for_model(encoding_name)
  return encoding.max_token_value

def num_tokens_from_string(string: str, encoding_name: str = "gpt-3.5-turbo") -> int:
  """Returns the number of tokens in a text string."""
  encoding = tiktoken.encoding_for_model(encoding_name)
  num_tokens = len(encoding.encode(string))
  return num_tokens