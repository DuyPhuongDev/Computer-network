from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from database import engine
from models import Base
from routers import auth, channel, signaling, tracker, server
from fastapi.responses import FileResponse


app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this in production to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

@app.get("/healthy")
def health_check():
    return {'status': 'Healthy'}

app.include_router(auth.router)
app.include_router(channel.router)
app.include_router(signaling.router)
app.include_router(tracker.router)
app.include_router(server.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",  # Cho phép truy cập từ LAN
        port=8000,
        ssl_keyfile="./ssl/192.168.1.11+1-key.pem",
        ssl_certfile="./ssl/192.168.1.11+1.pem"
    )