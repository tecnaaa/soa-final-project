from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Payment Service")

class PaymentRequest(BaseModel):
    user_id: int
    amount: float

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/pay")
async def pay(req: PaymentRequest):
    # Dummy processing
    return {"status": "processed", "user_id": req.user_id, "amount": req.amount}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8004, reload=True)
