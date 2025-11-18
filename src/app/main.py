from fastapi import FastAPI
from src.app.routes import chat, status

app = FastAPI()
app.include_router(status.router, prefix="/api", tags=["status"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
