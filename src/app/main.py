from fastapi import FastAPI
from src.app.routes import chat, status
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(status.router, prefix="/api", tags=["status"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
