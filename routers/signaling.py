from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Peers, Channels
from service.auth import verify_token
from typing import Optional, Dict
import json

router = APIRouter(prefix="/ws", tags=["signaling"])

# Dictionary lưu WebSocket connections theo channel_id và peer_id
# Format: {channel_id: {peer_id: WebSocket}}
active_connections: Dict[int, Dict[str, WebSocket]] = {}


@router.websocket("/{channel_id}/signaling")
async def signaling_websocket(
    websocket: WebSocket,
    channel_id: int,
    peer_id: str,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    # Kiểm tra token
    current_user = None
    if token:
        try:
            current_user = await verify_token(token, db)
        except HTTPException:
            await websocket.close(code=4001, reason="Invalid token")
            return

    # Kiểm tra channel tồn tại
    channel = db.query(Channels).filter(Channels.id == channel_id).first()
    if not channel:
        await websocket.close(code=4001, reason="Channel not found")
        return

    # Đăng ký hoặc cập nhật peer trong DB
    db_peer = db.query(Peers).filter(Peers.peer_id == peer_id).first()
    if not db_peer:
        db_peer = Peers(
            peer_id=peer_id,
            user_id=current_user.id if current_user else None,
            channel_id=channel_id
        )
        db.add(db_peer)
    else:
        db_peer.channel_id = channel_id
    db.commit()

    # Khởi tạo dictionary cho channel nếu chưa có
    if channel_id not in active_connections:
        active_connections[channel_id] = {}

    # Thêm WebSocket connection vào active_connections
    active_connections[channel_id][peer_id] = websocket
    await websocket.accept()

    try:
        # Vòng lặp xử lý tin nhắn signaling
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            target_peer_id = message.get("target_peer_id")
            print(message)

            # Gửi tin nhắn tới target peer trong cùng channel
            if target_peer_id and target_peer_id in active_connections[channel_id]:
                target_websocket = active_connections[channel_id][target_peer_id]
                await target_websocket.send_text(data)
            else:
                # Broadcast tới tất cả peer trong channel nếu không có target_peer_id
                for ws in active_connections[channel_id].values():
                    if ws != websocket:  # Không gửi lại cho chính mình
                        await ws.send_text(data)

    except WebSocketDisconnect:
        # Xóa peer khỏi active_connections khi ngắt kết nối
        if peer_id in active_connections[channel_id]:
            del active_connections[channel_id][peer_id]
        if not active_connections[channel_id]:
            del active_connections[channel_id]
    except Exception as e:
        await websocket.close(code=1011, reason=str(e))
    finally:
        # Cập nhật trạng thái peer trong DB (tùy chọn)
        db_peer.channel_id = None  # Peer rời channel
        db.commit()