import os
import urllib.request
from typing import Tuple, Any
import uuid
from agents.core import client, aclient
from agents.retrievers.file_retrieval_tool import summary_of_files, retrieval_of_files
import ssl
from agents.util import encode_image, abatch_tasks
from orm.crud import create_user_image


ssl._create_default_https_context = ssl._create_unverified_context
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# 图像生成
async def generate_image(user_id: int, user_partition: str, content: str, tool_args: dict) -> str:
    """Generate an image based on the prompt"""
    prompt: str = tool_args.get("prompt")
    size: str = "1024x1024"
    quality: str = tool_args.get("quality")
    if not quality:
        quality = "standard"
    n: int = tool_args.get("n")
    if not n or n<1:
        n = 1
    elif n>4:
        n = 4
    style: str = tool_args.get("style")
    if not style:
        style = "vivid"
    # return f"Here is the result from the dall-e-3 tool: https://cdn.openai.com/API/images/guides/image_generation_simple.png"
    # return json.dumps({"prompt": prompt, "image_url": f'https://cdn.openai.com/API/images/guides/image_generation_simple.webp'})
    responses = abatch_tasks([
        aclient.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            quality=quality,
            n=1,
            style=style,
        ) 
        for _ in range(n)
    ])
    nginx_prefix = os.environ.get("NGINX_API_LOCATION","")
    domain_name = os.getenv("DOMAIN_NAME", "http://localhost:8000")
    os.makedirs(f"{user_partition}/images", exist_ok=True)
    image_list = []
    for i, response in enumerate(responses):
        image_url = response.data[0].url
        revised_prompt = response.data[0].revised_prompt
        image_path = f"{user_partition}/images/{str(uuid.uuid4())}.png"
        with urllib.request.urlopen(image_url, context=ctx) as response:
            with open(image_path, 'wb') as f: 
                f.write(response.read())
        user_image_path = image_path.replace(os.getenv("DATA_PATH"),"")
        image_url = f'{domain_name + nginx_prefix}/static/{user_image_path}'
        create_user_image(user_id=user_id, user_image={
                "prompt": prompt,
                "quality": quality,
                "size": size,
                "style": style,
                "revised_prompt": revised_prompt,
                "image_url": image_url
            })
        image_list.append(image_url)
    return "Here is the results from the generate_image tool:\n\n" + ('\n'.join(image_list))


def understanding_image(user_id: int, user_partition: str, content: str, tool_args: dict) -> str:
    """Understand images based on user description"""
    image_urls: list[str] = tool_args.get("image_urls")
    contents = []
    if content:
        contents.append({"type": "text", "text": content})
    for image_url in image_urls:
        final_path_pos = image_url.rfind("/")
        file_name = image_url[final_path_pos+1:]
        content_type = "image/jpeg"
        if image_url.endswith(".png"):
            content_type = "image/png"
        elif image_url.endswith(".gif"):
            content_type = "image/gif"
        image_encode = encode_image(image_path=user_partition + "/upload/" + file_name)
        contents.append({"type": "image_url", "image_url": {"url": f"data:{content_type};base64,{image_encode}"}})
    response = client.chat.completions.create(
        model="gpt-4-vision-preview",       
        messages=[
            {
                "role": "user",
                "content": contents,
            }
        ],
    )
    return f"Here is the result from the understanding_image tool: {response.choices[0].message.content}"

tool_functions = {
    generate_image.__name__ : generate_image,
    understanding_image.__name__ : understanding_image,
    summary_of_files.__name__ : summary_of_files,
    retrieval_of_files.__name__ : retrieval_of_files,
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
                    "quality": {
                        "type": "string",
                        "enum": ["standard", "hd"],
                        "description": "The quality of the generated image",
                    },
                    "n": {
                        "type": "number",
                        "description": "The number of images to generate for a prompt"
                    },
                    "style": {
                        "tyle": "string",
                        "enum": ["vivid", "natural"],
                        "description": "The style of the generated images. Must be one of vivid or natural. Vivid causes the model to lean towards generating hyper-real and dramatic images. Natural causes the model to produce more natural, less hyper-real looking images."
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
                    "image_urls": {"type": "array", "items": {"type": "string"}, "description": "List of urls for images"},
                },
                "required": ["image_urls"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": summary_of_files.__name__,
            "description": summary_of_files.__doc__,
            "parameters": {
                "type": "object",
                "properties": {
                    "file_urls": {"type": "array", "items": {"type": "string"}, "description": "List of uploaded files, excluding image files"},
                },
                "required": ["file_urls"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": retrieval_of_files.__name__,
            "description": retrieval_of_files.__doc__,
            "parameters": {
                "type": "object",
                "properties": {
                    "file_urls": {"type": "array", "items": {"type": "string"}, "description": "List of uploaded files, excluding image files"},
                    "query": {"type": "string", "description": "String to find relevant documents for"},
                    "page": {"type": "number", "description": "Page number to find relevant documents for"},
                },
                "required": ["file_urls", "query"],
            },
        }
    },
]
