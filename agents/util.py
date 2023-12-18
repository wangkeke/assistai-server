import os
import base64
import asyncio

# Function to encode the image
def encode_image(image_url: str):
  UPLOAD_PATH = os.getenv("UPLOAD_PATH", "/home/lighthouse/workspace/data/upload/")
  path = image_url[image_url.index("/upload/") + 8:]
  with open(UPLOAD_PATH + path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

async def execute(tool_functions: list):
    return await asyncio.gather(*tool_functions)