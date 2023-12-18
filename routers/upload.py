import os
import hashlib
import io
import uuid
from datetime import datetime
import logging
from typing import Annotated
from fastapi import UploadFile, Depends, HTTPException, APIRouter
from orm import schemas, crud
from PIL import Image
from sqlalchemy.orm import Session
from dependencies import get_db, get_current_user


router = APIRouter(
    prefix="/upload", 
    tags=["upload"], 
    responses={404 : {"description": "Not Found"}}
)

DATA_PATH = os.getenv("DATA_PATH", "/home/lighthouse/workspace/data/")
if not os.path.exists(DATA_PATH):
    os.makedirs(DATA_PATH, exist_ok=True)

log = logging.getLogger(__name__)

supported_file_suffixes = (
    ".jpg",".jpeg",".png",".webp",".gif",
    ".doc",".docx",".xls",".xlsx",".ppt",".pptx",".csv",".pdf",
    ".txt",".sql",".json",".log",".md",".html",".htm",".ipynb",
    ".java",".py",".mq4",".mq5",".mqh",".js",".jsx",".ts",".tsx",".vue",".rtf",".bat",
    ".css",".cs",".php",".c",".cpp",".swift",".go",".scala",".dart",".lua",".sh",".bash",
    ".ini",".config",".yaml",".yml",
    )

@router.post("/files", response_model=list[schemas.UserFile])
async def upload_file(files: list[UploadFile], 
                      current_user: Annotated[schemas.User, Depends(get_current_user)], 
                      db: Session = Depends(get_db)):
    result = []
    nginx_prefix = os.environ.get("NGINX_API_LOCATION","")
    domain_name = os.getenv("DOMAIN_NAME", "http://localhost:8000")
    user_dir = hashlib.md5(current_user.username.encode()).hexdigest()
    if not os.path.exists(DATA_PATH + user_dir + "/upload"):
        os.makedirs(DATA_PATH + user_dir + "/upload", exist_ok=True)
    for file in files:
        file_size = file.size
        if file_size > 5*1024*1024:
            raise HTTPException(status_code=400, detail="Each file size max 5MB.")
        file_name: str = file.filename
        if not file_name.endswith(supported_file_suffixes):
            raise HTTPException(status_code=400, detail="Unsupported file types.")
        ext_pos = file_name.rfind('.')
        file_format = file_name[ext_pos+1:]
        content_type = file.content_type
        hash_obj = hashlib.sha256()
        bytes = await file.read()
        await file.close()
        hash_obj.update(bytes)
        file_etag = hash_obj.hexdigest()
        new_file_name = file_etag + "." + file_format
        user_file = crud.get_user_file(db=db, user_id=current_user.id, file_etag=file_etag)
        if user_file:
            result.append(user_file)
            continue
        if content_type.startswith("image/"):
            with Image.open(io.BytesIO(bytes)) as img:
                new_width = img.width
                new_height = img.height
                if new_width > 512:
                    new_height = new_height*512/new_width
                    new_width = 512
                if new_height > 512:
                    new_width = new_width*512/new_height
                    new_height = 512
                img.resize(size=(int(new_width),int(new_height))).save(DATA_PATH + user_dir + "/upload/" + new_file_name) 
        else:
            with open(DATA_PATH + user_dir  + "/upload/" + new_file_name, mode="xb") as f:
                f.write(bytes)
        file_url = f'{nginx_prefix}/static/{user_dir}/upload/{new_file_name}'
        user_file = crud.create_user_file(
            db=db, 
            user_id=current_user.id, 
            create_user_file=schemas.CreateUserFile(file_etag=file_etag, 
                                                    file_name=file_name, 
                                                    content_type=content_type, 
                                                    file_format=file_format, 
                                                    file_size=file_size, 
                                                    file_url=domain_name + file_url)
        )
        result.append(user_file)
    return result

