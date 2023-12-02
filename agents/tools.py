import os
import urllib.request
import uuid
from agents.core import client, logger
import ssl
import json

ssl._create_default_https_context = ssl._create_unverified_context
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# 图像生成
def generate_image(args: dict):
    """Generate an image based on the prompt"""
    prompt: str = args.get("prompt")
    # return json.dumps({"prompt": prompt, "image_url": f'https://cdn.openai.com/API/images/guides/image_generation_simple.webp'})
    response = client.images.generate(
        model="dall-e-2",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )
    nginx_prefix = os.environ.get("NGINX_API_LOCATION","")
    domain_name = os.getenv("DOMAIN_NAME", "http://localhost:8000")
    image_url = response.data[0].url
    data_path = os.getenv("DATA_PATH")
    os.makedirs(f"{data_path}/images", exist_ok=True)
    image_path = f"/images/{str(uuid.uuid4())}.png"
    with urllib.request.urlopen(image_url, context=ctx) as response:
        with open(data_path + image_path, 'wb') as f: 
            f.write(response.read())
    # return json.dumps({"image_url": f'{domain_name + nginx_prefix}/static{image_path}'})
    # return f'{domain_name + nginx_prefix}/static{image_path}'
    return f'An image has been generated:\n ![{prompt}]({domain_name + nginx_prefix}/static{image_path} "{prompt}")'


def understanding_image(args: dict):
    """Understand images based on user description"""
    text: str = args.get("text")
    image_urls: list[str] = args.get("image_urls")
    contents = []
    if text:
        contents.append({"type": "text", "text": text})
    for image_url in image_urls:
        contents.append({"type": "image_url", "image_url": {"url": image_url}})
    response = client.chat.completions.create(
        model="gpt-4-vision-preview",       
        messages=[
            {
                "role": "user",
                "content": contents,
            }
        ],
    )
    return json.dumps({"content": response.choices[0].message.content})

tool_functions = {
    generate_image.__name__ : generate_image,
    # understanding_image.__name__ : understanding_image
}

tools = [
    {
        "type": "function",
        "function": {
            "name": generate_image.__name__,
            "description": generate_image.__doc__,
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "A detailed prompt to generate an image",
                    },
                },
                "required": ["prompt"],
            },
        }
    },
    # {
    #     "type": "function",
    #     "function": {
    #         "name": understanding_image.__name__,
    #         "description": understanding_image.__doc__,
    #         "parameters": {
    #             "type": "object",
    #             "properties": {
    #                 "image_urls": {"type": "array", "items": {"type": "string"}, "description": "List of urls for images"},
    #                 "text": {"type": "string", "description": "Other text content"},
    #             },
    #             "required": ["text", "image_urls"],
    #         },
    #     }
    # },
]
