import os
import uuid
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import FileResponse
from app.core.config import UPLOAD_DIR
from app.services.user_service import check_username_available

router = APIRouter()

@router.get("/check-username/{username}")
async def check_username(username: str):
    return {"available": check_username_available(username)}

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    ext = file.filename.split(".")[-1].lower()
    if ext not in ["jpg", "jpeg", "png", "gif", "webp"]:
        return {"error": "Invalid file type."}
    filename = f"{uuid.uuid4()}.{ext}"
    path = os.path.join(UPLOAD_DIR, filename)
    with open(path, "wb") as f:
        content = await file.read()
        f.write(content)
    return {"url": f"/uploads/{filename}"}

@router.get("/uploads/{filename}")
async def get_upload(filename: str):
    path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(path):
        return {"error": "Not found"}
    return FileResponse(path)

@router.get("/logo.png")
async def get_logo():
    # Assuming logo.png is in the root directory
    if os.path.exists("Logo.png"):
        return FileResponse("Logo.png")
    return {"error": "Logo not found"}
