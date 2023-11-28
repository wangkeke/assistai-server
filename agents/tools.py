import os
import urllib.request
import uuid
from agents.core import client
import ssl

ssl._create_default_https_context = ssl._create_unverified_context
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# 图像生成
def generate_image(args: dict):
    """Generate an image based on the prompt"""
    prompt: str = args.get("prompt")
    print(f"generate_image tool args is : {args}")
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )
    nginx_prefix = os.environ.get("NGINX_API_LOCATION","")
    domain_name = os.getenv("DOMAIN_NAME", "http://localhost:8000")
    image_url = response.data[0].url
    revised_prompt = prompt
    if response.data[0].revised_prompt:
        revised_prompt = prompt
    data_path = os.getenv("DATA_PATH")
    os.makedirs(f"{data_path}/images", exist_ok=True)
    image_path = f"/images/{str(uuid.uuid4())}.webp"
    with urllib.request.urlopen(image_url, context=ctx) as response:
        with open(data_path + image_path, 'wb') as f: 
            f.write(response.read())
    return f'![{revised_prompt}]({domain_name + nginx_prefix}/static{image_path} "{prompt}")'


def understanding_image(args: dict):
    """Understand images based on user description"""
    description: str = args.get("description")
    print(f"understanding_image tool args is : {args}")
    image_urls: list[str] = args.get("image_urls")
    contents = []
    if description:
        contents.append({"type": "text", "text": description})
    for image_url in image_urls:
        contents.append({"type": "image_url", "image_url": image_url})
    response = client.chat.completions.create(
        model="gpt-4-vision-preview",       
        messages=[
            {
                "role": "system",
                "content": "Please translate the returned content into Chinese",
            },
            {
                "role": "user",
                "content": contents,
            }
        ],
    )
    print(f"Understand images response = {response}")
    return response.choices[0].message.content

tool_functions = {
    generate_image.__name__ : generate_image,
    understanding_image.__name__ : understanding_image
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
                        "description": "a detailed prompt to generate an image",
                    },
                },
                "required": ["prompt"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": understanding_image.__name__,
            "description": understanding_image.__doc__,
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {"type": "string", "description": "user description"},
                    "image_urls": {"type": "array", "items": {"type": "string"}, "description": "List of urls for images"}
                },
                "required": ["description", "image_urls"],
            },
        }
    },
]
