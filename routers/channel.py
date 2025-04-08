from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db
from models import Channels, ChannelMembers, Peers, Users
from service.auth import get_current_user, get_current_user_optional
import uuid

router = APIRouter(prefix="/channels", tags=["channels"])

# Pydantic models
class ChannelCreate(BaseModel):
    name: str
class ChannelMember(BaseModel):
    id: int
    username: str
    full_name: str
    role: str

    class Config:
        from_attributes = True

class ChannelResponse(BaseModel):
    id: int
    name: str
    host_user_id: int
    members: list[ChannelMember]  # Thông tin thành viên

    class Config:
        from_attributes = True

class JoinChannelRequest(BaseModel):
    peer_id: str  # UUID từ ReactJS 

# Create channel (chỉ authenticated-user)
@router.post("/create", response_model=ChannelResponse)
async def create_channel(
    channel: ChannelCreate,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Tạo channel mới
    db_channel = Channels(name=channel.name, host_user_id=current_user.id)
    db.add(db_channel)
    db.commit()
    db.refresh(db_channel)

    # Thêm host làm thành viên
    db_member = ChannelMembers(channel_id=db_channel.id, user_id=current_user.id, role='host')
    db.add(db_member)
    db.commit()
    db.refresh(db_channel)

    # Tải lại members với thông tin từ Users
    db_channel.members = (
        db.query(ChannelMembers)
        .filter(ChannelMembers.channel_id == db_channel.id)
        .all()
    )
    for member in db_channel.members:
        member.username = member.user.username
        member.full_name = member.user.full_name
        member.status = member.user.status

    return db_channel

# Join channel (cả visitor và authenticated-user)
@router.post("/{channel_id}/join", response_model=ChannelResponse)
async def join_channel(
    channel_id: int,
    join_request: JoinChannelRequest,
    current_user: Optional[Users] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    # Kiểm tra channel tồn tại
    db_channel = db.query(Channels).filter(Channels.id == channel_id).first()
    if not db_channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    # Kiểm tra peer_id
    db_peer = db.query(Peers).filter(Peers.peer_id == join_request.peer_id).first()
    if not db_peer:
        # Tạo peer mới nếu chưa tồn tại
        db_peer = Peers(peer_id=join_request.peer_id, user_id=current_user.id if current_user else None, channel_id=channel_id)
        db.add(db_peer)
    else:
        # Cập nhật channel_id nếu peer đã tồn tại
        db_peer.channel_id = channel_id
    db.commit()

    # Thêm thành viên (nếu authenticated-user)
    if current_user:
        existing_member = db.query(ChannelMembers).filter(
            ChannelMembers.channel_id == channel_id,
            ChannelMembers.user_id == current_user.id
        ).first()
        if not existing_member:
            db_member = ChannelMembers(
                channel_id=channel_id,
                user_id=current_user.id,
                role='member' if current_user.id != db_channel.host_user_id else 'host'
            )
            db.add(db_member)
            db.commit()

    db.refresh(db_channel)
    return db_channel

# Get channel info
@router.get("/{channel_id}", response_model=ChannelResponse)
async def get_channel_info(
    channel_id: int,
    current_user: Optional[Users] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    db_channel = db.query(Channels).filter(Channels.id == channel_id).first()
    if not db_channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    return db_channel