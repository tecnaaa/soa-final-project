# Backend (FastAPI microservices)

# Test dự án 
1. cd backend/services/users
2. pip install -r requirements.txt
3. tạo db trong xampp (mã sql db trong backend/db/db.md)
4. uvicorn main:app --reload --host 0.0.0.0 --port 8002
5. lên trang localhost:8002/docs để test các API