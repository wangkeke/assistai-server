import os
import hashlib
import uuid
from datetime import datetime
import logging
from typing import Annotated
from fastapi import UploadFile, Depends, HTTPException, APIRouter
from orm import schemas
from PIL import Image
from dependencies import get_current_user


router = APIRouter(
    prefix="/upload", 
    tags=["upload"], 
    responses={404 : {"description": "Not Found"}}
)

UPLOAD_PATH = os.getenv("UPLOAD_PATH", "/home/lighthouse/workspace/data/upload/")
if not os.path.exists(UPLOAD_PATH):
    os.makedirs(UPLOAD_PATH, exist_ok=True)

log = logging.getLogger(__name__)

supported_file_suffixes = (
    ".jpg",".jpeg",".png",".webp",".gif",
    # ".doc",".docx",".xls",".xlsx",".ppt",".pptx",".csv",".pdf",
    # ".txt",".sql",".json",".java",".py",".mq4",".mq5",".mqh",".js",".jsx",".ts",".tsx",".log",".html",".htm",".md",".vue",
    # ".rtf",".ipynb",".css",".cs",".php",".c",".cpp",".swift",".go",".scala",".dart",".lua",".sh",".bash",".ini",".config",
    # ".yaml",".yml",".bat",
    )

@router.post("/files")
async def upload_file(files: list[UploadFile], current_user: Annotated[schemas.User, Depends(get_current_user)]):
    result = []
    nginx_prefix = os.environ.get("NGINX_API_LOCATION","")
    domain_name = os.getenv("DOMAIN_NAME", "http://localhost:8000")
    for file in files:
        file_size = file.size
        if file_size > 10*1024*1024:
            raise HTTPException(status_code=400, detail="Each file size max 10MB.")
        file_name: str = file.filename
        if not file_name.endswith(supported_file_suffixes):
            raise HTTPException(status_code=400, detail="Unsupported file types.")
        ext_pos = file_name.rfind('.')
        file_format = file_name[ext_pos+1:]
        user_dir = hashlib.md5(current_user.username.encode()).hexdigest()
        if not os.path.exists(UPLOAD_PATH + user_dir):
            os.makedirs(UPLOAD_PATH + user_dir, exist_ok=True)
        file_etag = str(uuid.uuid4())
        new_file_name = file_etag + "." + file_format
        with open(UPLOAD_PATH + user_dir + "/" + new_file_name, mode="xb") as f:
            f.write(await file.read())
        if file.content_type.startswith("image/"):    
            with Image.open(UPLOAD_PATH + user_dir + "/" + new_file_name) as img:
                new_width = img.width
                new_height = img.height
                if new_width > 512:
                    new_height = new_height*512/new_width
                    new_width = 512
                if new_height > 512:
                    new_width = new_width*512/new_height
                    new_height = 512
                img.resize(size=(int(new_width),int(new_height))).save(UPLOAD_PATH + user_dir + "/" + new_file_name) 
        file_url = f'{nginx_prefix}/static/upload/{user_dir}/{new_file_name}'
        result.append({
            "file_etag": file_etag, 
            "file_name": file_name, 
            "content_type": file.content_type, 
            "file_format": file_format, 
            "file_size": file.size, "file_url": domain_name + file_url
        })
    return result


