from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from database import engine
from models import Base
from routers import auth, channel, signaling, server
from fastapi.responses import FileResponse
import os
from service.logger import get_logger

# Tạo thư mục logs nếu chưa tồn tại
os.makedirs("logs", exist_ok=True)

# Tạo logger cho ứng dụng chính
logger = get_logger("main")
logger.info("Starting application")

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this in production to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("Setting up CORS middleware")

Base.metadata.create_all(bind=engine)
logger.info("Database tables created")

@app.get("/healthy")
def health_check():
    logger.debug("Health check endpoint called")
    return {'status': 'Healthy'}

logger.info("Registering routers")
app.include_router(auth.router)
app.include_router(channel.router)
app.include_router(signaling.router)
app.include_router(server.router)

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting uvicorn server")
    uvicorn.run(
        app,
        host="0.0.0.0",  # Cho phép truy cập từ LAN
        port=8000
    )