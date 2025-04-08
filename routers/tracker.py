from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from database import get_db
from models import Peers, Channels, Users
from service.auth import get_current_user_optional

router = APIRouter(prefix="/tracker", tags=["tracker"])

# Pydantic models
class PeerInfo(BaseModel):
    peer_id: str  # UUID từ ReactJS
    channel_id: Optional[int] = None  # Channel mà peer tham gia (nếu có)

class PeerResponse(BaseModel):
    peer_id: str
    user_id: Optional[int]
    channel_id: Optional[int]

    class Config:
        from_attributes = True

# Submit Info (đăng ký/cập nhật peer)
@router.post("/submit_info", response_model=PeerResponse)
async def submit_info(
    peer_info: PeerInfo,
    current_user: Optional[Users] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    # Kiểm tra channel_id (nếu có)
    if peer_info.channel_id:
        channel = db.query(Channels).filter(Channels.id == peer_info.channel_id).first()
        if not channel:
            raise HTTPException(status_code=404, detail="Channel not found")

    # Tìm hoặc tạo peer
    db_peer = db.query(Peers).filter(Peers.peer_id == peer_info.peer_id).first()
    if not db_peer:
        db_peer = Peers(
            peer_id=peer_info.peer_id,
            user_id=current_user.id if current_user else None,
            channel_id=peer_info.channel_id
        )
        db.add(db_peer)
    else:
        # Cập nhật thông tin peer
        db_peer.user_id = current_user.id if current_user else None
        db_peer.channel_id = peer_info.channel_id
    db.commit()
    db.refresh(db_peer)
    return db_peer

# Get List (lấy danh sách peer)
@router.get("/get_list", response_model=List[PeerResponse])
async def get_list(
    channel_id: Optional[int] = None,  # Lọc theo channel nếu có
    current_user: Optional[Users] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    query = db.query(Peers)
    if channel_id:
        # Kiểm tra channel tồn tại
        channel = db.query(Channels).filter(Channels.id == channel_id).first()
        if not channel:
            raise HTTPException(status_code=404, detail="Channel not found")
        query = query.filter(Peers.channel_id == channel_id)
    peers = query.all()
    return peers

# (Tùy chọn) Remove Peer
@router.delete("/remove/{peer_id}", response_model=dict)
async def remove_peer(
    peer_id: str,
    current_user: Optional[Users] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    db_peer = db.query(Peers).filter(Peers.peer_id == peer_id).first()
    if not db_peer:
        raise HTTPException(status_code=404, detail="Peer not found")
    
    # Chỉ cho phép user liên quan hoặc không cần auth
    if current_user and db_peer.user_id and db_peer.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to remove this peer")
    
    db.delete(db_peer)
    db.commit()
    return {"status": "peer removed"}