import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.core.config import UPLOAD_DIR

router = APIRouter()


@router.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        file_id = f"{uuid.uuid4().hex[:12]}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, file_id)
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        return {"file_path": file_path, "filename": file.filename, "size": len(content)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
