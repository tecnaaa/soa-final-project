"""
File upload service for handling image uploads
"""
import os
import glob
from pathlib import Path
from typing import Optional
from fastapi import UploadFile, HTTPException, status
from fastapi.responses import FileResponse
import uuid

# --- CẤU HÌNH ĐƯỜNG DẪN (SỬA LẠI) ---
# Trong Docker: /app/services/file_upload.py -> parent.parent = /app
BASE_DIR = Path(__file__).resolve().parent.parent 

# Đường dẫn tuyệt đối tới thư mục uploads trong container
# Phải khớp với volume mount trong docker-compose: /app/backend/uploads
UPLOAD_DIR = BASE_DIR / "backend" / "uploads"

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Tạo thư mục nếu chưa có (quan trọng: parents=True để tạo cả folder cha 'backend' nếu thiếu)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
# ------------------------------------

def validate_file(file: UploadFile) -> bool:
    """Validate uploaded file extension"""
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        return False
    return True

async def save_upload_file(file: UploadFile, user_id: int) -> Optional[str]:
    """Save uploaded file as {user_id}.{ext}"""
    try:
        # 1. Validate extension
        if not validate_file(file):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Định dạng file không hợp lệ. Chỉ chấp nhận: jpg, jpeg, png, gif, webp"
            )
        
        # 2. Kiểm tra kích thước
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File quá lớn. Tối đa: {MAX_FILE_SIZE / (1024*1024)}MB"
            )

        # 3. Xóa avatar cũ (nếu có)
        search_pattern = str(UPLOAD_DIR / f"{user_id}.*")
        existing_files = glob.glob(search_pattern)
        
        for old_file in existing_files:
            try:
                os.remove(old_file)
            except Exception as e:
                print(f"[AVATAR] Error deleting old file {old_file}: {e}")

        # 4. Lưu file mới
        file_ext = Path(file.filename).suffix.lower()
        new_filename = f"{user_id}{file_ext}"
        file_path = UPLOAD_DIR / new_filename
        
        with open(file_path, "wb") as f:
            f.write(contents)
        
        print(f"[AVATAR] Saved new avatar: {file_path}")
        
        # Trả về đường dẫn tương đối để lưu vào DB: "uploads/1.png"
        # Gateway sẽ ghép thành /files/uploads/1.png -> trỏ tới /app/backend/uploads/1.png
        return f"uploads/{new_filename}"
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi lưu file: {str(e)}"
        )

async def delete_file(file_path: str) -> bool:
    """Delete uploaded file"""
    try:
        # file_path input: "uploads/1.png" -> full: /app/backend/uploads/1.png
        full_path = BASE_DIR / "backend" / file_path
        if full_path.exists() and full_path.is_file():
            full_path.unlink()
            return True
        return False
    except Exception as e:
        print(f"Error deleting file: {e}")
        return False

def get_file_url(file_path: str) -> str:
    clean_path = file_path.replace("\\", "/")
    return f"/files/{clean_path}"

async def get_file(file_path_str: str) -> FileResponse:
    """
    Lấy file ảnh. Đường dẫn đầu vào từ Gateway dạng: "uploads/1.png"
    """
    # Ghép thành đường dẫn tuyệt đối: /app/backend/uploads/1.png
    full_path = BASE_DIR / "backend" / file_path_str
    
    if not full_path.exists():
        # Fallback về default.webp
        default_path = UPLOAD_DIR / "default.webp"
        
        if default_path.exists():
            return FileResponse(default_path)
        
        # Nếu không có cả default -> Lỗi 404 (để tránh loop 500)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Default avatar not found"
        )
        
    return FileResponse(full_path)