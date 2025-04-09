from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session
from database import get_db
from models import Channels, Users, Messages
from datetime import datetime
from typing import Optional, Dict
import json
from service.auth import verify_token 

router = APIRouter(prefix="/ws", tags=["signaling"])
# channel_id: {peer_id: websocket}
active_connections: Dict[int, Dict[str, WebSocket]] = {}
text_connections: Dict[int, Dict[int, WebSocket]] = {}

@router.websocket("/{channel_id}/signaling")
async def signaling_websocket(
    websocket: WebSocket,
    channel_id: int,
    peer_id: str,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    # Kiểm tra channel tồn tại
    print(f"channel_id: {channel_id}, peer_id: {peer_id}, token: {token}")
    channel = db.query(Channels).filter(Channels.id == channel_id).first()
    if not channel:
        await websocket.close(code=4001, reason="Channel not found")
        return

    # Xác thực token
    current_user = None
    if token:
        try:
            current_user = await verify_token(token, db)
        except:
            await websocket.close(code=4003, reason="Invalid token")
            return

    # Đăng ký peer vào active_connections
    await websocket.accept()
    if channel_id not in active_connections:
        active_connections[channel_id] = {}
    active_connections[channel_id][peer_id] = websocket

    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received from {peer_id}: {data}")
            message = json.loads(data)
            # send to all peers except the sender
            print(message)
            for ws in active_connections[channel_id].values():
                if ws != websocket:
                    await ws.send_text(data)
                
    except WebSocketDisconnect:
        if peer_id in active_connections[channel_id]:
            del active_connections[channel_id][peer_id]
        if not active_connections[channel_id]:
            del active_connections[channel_id]
     
@router.websocket("/{channel_id}")
async def text_websocket(
    websocket: WebSocket,
    channel_id: int,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    channel = db.query(Channels).filter(Channels.id == channel_id).first()
    if not channel:
        await websocket.close(code=4001, reason="Channel not found")
        return

    current_user = None
    if token:
        try:
            current_user = await verify_token(token, db)
        except:
            await websocket.close(code=4003, reason="Invalid token")
            return

    if not current_user:
        await websocket.close(code=4003, reason="Authentication required")
        return

    await websocket.accept()
    if channel_id not in text_connections:
        text_connections[channel_id] = {}
    text_connections[channel_id][current_user.id] = websocket

    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            print(f"Received from {current_user.id}: {message_data}")
            new_message = Messages(
                content=message_data["content"],
                channel_id=channel_id,
                sender_id=current_user.id,
                created_at=message_data["created_at"]
            )
            db.add(new_message)
            db.commit()
            db.refresh(new_message)
            print(f"New message: {new_message}")
            response = {
                "id": new_message.id,
                "content": new_message.content,
                "created_at": new_message.created_at,
                "sender": {
                    "id": current_user.id,
                    "username": current_user.username,
                    "full_name": current_user.full_name,
                    "status": current_user.status
                }
            }
            print(response);
            # Gửi tin nhắn tới tất cả client trong channel
            for ws in text_connections[channel_id].values():
                await ws.send_json(response)
    except WebSocketDisconnect:
        if current_user.id in text_connections[channel_id]:
            del text_connections[channel_id][current_user.id]
        if not text_connections[channel_id]:
            del text_connections[channel_id]