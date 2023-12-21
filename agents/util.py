import os
import base64
import asyncio
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