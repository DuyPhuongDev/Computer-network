from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session
from database import get_db
from models import Channels, Users, Messages
from datetime import datetime
from typing import Optional, Dict
import json
from service.auth import get_current_user, get_current_user_optional, getUsernameByToken
from service.logger import get_logger
import uuid

# Tạo logger cho module signaling
logger = get_logger("signaling")

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
    logger.info(f"channel_id: {channel_id}, peer_id: {peer_id}, token: {token}")
    channel = db.query(Channels).filter(Channels.id == channel_id).first()
    if not channel:
        await websocket.close(code=4001, reason="Channel not found")
        logger.warning(f"Channel {channel_id} not found, connection closed")
        return

    # Xác thực token
    current_user = None
    if token:
        try:
            current_user = await get_current_user_optional(token, db)
        except:
            await websocket.close(code=4003, reason="Invalid token")
            logger.warning(f"Invalid token for text channel {channel_id}, connection closed")
            return
    # current user is None => guest
    if not current_user: 
        # await websocket.close(code=4003, reason="Authentication required")
        # logger.warning(f"Authentication required for text channel {channel_id}, connection closed")
        # return
        random_uuid = str(uuid.uuid4())
        logger.info(f"Generated random UUID: {random_uuid}")
        current_user = Users(
            id=random_uuid,
            username=f"guest_{getUsernameByToken(token)}",
            full_name=getUsernameByToken(token),
            status="online"
        )
        logger.info(f"Guest user created: {current_user.username}")

    # Đăng ký peer vào active_connections
    await websocket.accept()
    if channel_id not in active_connections:
        active_connections[channel_id] = {}
    active_connections[channel_id][peer_id] = websocket
    
    # Thông báo peer mới join tới các peer khác
    join_message = {
        "action": "new_peer",
        "peer_id": peer_id,
        "channel_id": channel_id,
        "username": current_user.username,
        "fullname": current_user.full_name
    }
    
    for ws in active_connections[channel_id].values():
        if ws != websocket:  # Không gửi lại cho peer vừa join
            await ws.send_text(json.dumps(join_message))
    logger.info(f"User {peer_id} joined voice channel {channel_id}")

    try:
        while True:
            data = await websocket.receive_text()
            logger.debug(f"Received from {peer_id}: {data}")
            message = json.loads(data)
            action = message.get("action")
            # Xử lý signaling cho WebRTC
            if action in ["offer", "answer", "ice_candidate"]:
                # send all member in channel => khoong can target id
                target_id = message.get("target_id")
                if target_id and channel_id in active_connections and target_id in active_connections[channel_id]:
                    target_ws = active_connections[channel_id][target_id]
                    message["peer_id"] = peer_id
                    await target_ws.send_text(json.dumps(message))
                else:
                    logger.warning(f"Target {target_id} not found in channel {channel_id}")
            else:
                # Gửi tới tất cả peer khác (nếu cần broadcast thông tin khác)
                for ws in active_connections[channel_id].values():
                    if ws != websocket:
                        await ws.send_text(data)

    except WebSocketDisconnect:
        # Xóa peer khỏi active_connections
        if channel_id in active_connections and peer_id in active_connections[channel_id]:
            del active_connections[channel_id][peer_id]
        
        # Nếu channel rỗng, xóa channel
        if channel_id in active_connections and not active_connections[channel_id]:
            del active_connections[channel_id]

        # Chỉ gửi thông báo "peer_left" nếu channel vẫn còn trong active_connections
        if channel_id in active_connections:
            leave_message = {
                "action": "peer_left",
                "peer_id": peer_id,
                "channel_id": channel_id
            }
            for ws in active_connections[channel_id].values():
                await ws.send_text(json.dumps(leave_message))
        logger.info(f"User {peer_id} disconnected from channel {channel_id}")
     
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
        logger.warning(f"Text channel {channel_id} not found, connection closed")
        return

    current_user = None
    if token:
        try:
            current_user = await get_current_user_optional(token, db)
        except:
            await websocket.close(code=4003, reason="Invalid token")
            logger.warning(f"Invalid token for text channel {channel_id}, connection closed")
            return
    # current user is None => guest
    if not current_user: 
        # await websocket.close(code=4003, reason="Authentication required")
        # logger.warning(f"Authentication required for text channel {channel_id}, connection closed")
        # return
        random_uuid = str(uuid.uuid4())
        logger.info(f"Generated random UUID: {random_uuid}")
        current_user = Users(
            id=random_uuid,
            username=f"guest_{getUsernameByToken(token)}",
            full_name=getUsernameByToken(token),
            status="online"
        )
        logger.info(f"Guest user created: {current_user.username}")
        

    # handshake dc fastapi xu ly khi dung app.websocket
    await websocket.accept()
    if channel_id not in text_connections:
        text_connections[channel_id] = {}
    text_connections[channel_id][current_user.id] = websocket
    logger.info(f"User {current_user.username} connected to text channel {channel_id}")

    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            logger.debug(f"Received from {current_user.id}: {message_data}")
            new_message = Messages(
                content=message_data["content"],
                channel_id=channel_id,
                sender_id=current_user.id,
                created_at=message_data["created_at"]
            )
            db.add(new_message)
            db.commit()
            db.refresh(new_message)
            logger.debug(f"New message: {new_message.id}")
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
            # Gửi tin nhắn tới tất cả client trong channel
            for ws in text_connections[channel_id].values():
                await ws.send_json(response)
    except WebSocketDisconnect:
        if channel_id in text_connections and current_user.id in text_connections.get(channel_id, {}):
            del text_connections[channel_id][current_user.id]
            logger.info(f"User {current_user.username} disconnected from text channel {channel_id}")
        if channel_id in text_connections and not text_connections[channel_id]:
            del text_connections[channel_id]