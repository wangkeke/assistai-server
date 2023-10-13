import urllib.request
import uuid
import os

response = urllib.request.urlopen("https://cdn.openai.com/API/images/guides/image_generation_simple.webp")
data = response.read()
os.makedirs("/home/data/images")
image_path = f"/images/{str(uuid.uuid4())}.webp"
with open("/home/data" + image_path, 'wb') as f: 
    f.write(data)
print("写入完成")