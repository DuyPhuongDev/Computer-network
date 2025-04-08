from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from database import engine
from models import Base
from routers import auth, channel, signaling, tracker
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# using public file html,js,css
app = FastAPI()
# Mount thư mục static
app.mount("/static", StaticFiles(directory="static"), name="static")

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

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

app.include_router(auth.router)
app.include_router(channel.router)
app.include_router(signaling.router)
app.include_router(tracker.router)
