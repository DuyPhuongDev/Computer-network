from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel
from typing import Optional
from database import get_db
from models import Channels, ChannelMembers, Users, ChannelType, Messages
from service.auth import get_current_user, get_current_user_optional
from routers.auth import UserResponse
import uuid

router = APIRouter(prefix="/channels", tags=["channels"])

# Pydantic model

class ChannelCreate(BaseModel):
    name: str
    channel_type: ChannelType

class ChannelMember(BaseModel):
    id: int
    user: UserResponse
    role: str

    class Config:
        from_attributes = True

class ChannelResponse(BaseModel):
    id: int
    name: str
    channel_type: ChannelType
    members: list[ChannelMember]  # Thông tin thành viên

    class Config:
        from_attributes = True

class JoinChannelRequest(BaseModel):
    peer_id: str  # UUID từ ReactJS 

class MessageResponse(BaseModel):
    id: int
    content: str
    created_at: str
    sender: UserResponse

    class Config:
        from_attributes = True
class DataChannelResponse(BaseModel):
    id: int
    name: str
    channel_type: ChannelType
    messages: list[MessageResponse]
    class Config:
        from_attributes = True

# Create channel (chỉ authenticated-user)
@router.post("/create", response_model=ChannelResponse)
async def create_channel(
    channel: ChannelCreate,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Tạo channel mới
    db_channel = Channels(name=channel.name, channel_type=channel.channel_type)
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


@router.get("/{channel_id}/messages", response_model=DataChannelResponse, status_code=status.HTTP_200_OK)
async def get_messages(
    channel_id: int,
    db: Session = Depends(get_db)
):
    # eager load messages
    db_channel = db.query(Channels).options(joinedload(Channels.messages).joinedload(Messages.sender)).filter(Channels.id == channel_id).first()
    if not db_channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    return db_channel