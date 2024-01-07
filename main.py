import models
from typing import Annotated
from fastapi import Depends, FastAPI, status, HTTPException, UploadFile, File
from database import engine, SessionLocal
from secrets import token_hex
from sqlalchemy.orm import Session
import auth
from auth import get_current_user
import zipfile
import os
from glob import glob

app = FastAPI()
app.include_router(auth.router)

models.Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

@app.get("/", status_code=status.HTTP_200_OK)
async def user(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    return {"User": user}

@app.post("/create-challenge")
async def create_challenge(file:UploadFile = File(...)):
    file_ext = file.filename.split(".").pop()
    if file_ext != "zip":
        raise HTTPException(status_code=401, detail='Bad extension')
    challenges_dir = "./challenges"
    file_name = token_hex(10)
    file_path = f"{file_name}.{file_ext}"
    with open(f"temp/{file_path}", "wb") as f:
        content = await file.read()
        f.write(content)
    with zipfile.ZipFile(f"temp/{file_path}", 'r') as zip_ref:
        current_challenges = [x.replace(f"{challenges_dir}\\", '') for x in glob(f"{challenges_dir}/*")]
        if zip_ref.filelist[0].filename[:-1] in current_challenges:
            raise HTTPException(status_code=401, detail='Challenge has been already created!')
        zip_ref.extractall(challenges_dir)
    os.remove(f"temp/{file_path}")
    # TODO: Sprawdzanie struktury challenge'a, tylko admin może tworzyć challenge, refactor
    return {"success": True, "file_path": file_path, "message": "File uloaded successfully"}