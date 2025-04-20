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
    server_id: int
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
        
class JoinChannelRequest(BaseModel):
    channel_id: int

# Create channel (chỉ authenticated-user)
@router.post("/create", response_model=ChannelResponse)
async def create_channel(
    channel: ChannelCreate,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Tạo channel mới
    db_channel = Channels(name=channel.name, channel_type=channel.channel_type, server_id=channel.server_id)
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

@router.post("/join", response_model=ChannelResponse)
async def join_channel(
    channel: JoinChannelRequest,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Kiểm tra xem người dùng đã là thành viên của channel chưa
    existing_member = db.query(ChannelMembers).filter(
        ChannelMembers.channel_id == channel.channel_id,
        ChannelMembers.user_id == current_user.id
    ).first()

    if existing_member:
        raise HTTPException(status_code=400, detail="User already a member of the channel")

    # Thêm người dùng vào channel
    db_member = ChannelMembers(channel_id=channel.channel_id, user_id=current_user.id, role='member')
    db.add(db_member)
    db.commit()
    db.refresh(db_member)

    # Tải lại members với thông tin từ Users
    db_channel = db.query(Channels).filter(Channels.id == channel.channel_id).first()
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


# get all members of channel except current user
@router.get("/{channel_id}/members", response_model=list[ChannelMember])
async def get_channel_members(
    channel_id: int,
    current_user: Users = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    # Kiểm tra xem người dùng có quyền truy cập vào channel không
    db_channel = db.query(Channels).filter(Channels.id == channel_id).first()
    if not db_channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    # Lấy danh sách thành viên của channel 
    if current_user is None:
        # Nếu không có người dùng hiện tại, chỉ lấy thành viên
        members = (
            db.query(ChannelMembers)
            .filter(ChannelMembers.channel_id == channel_id)
            .all()
        )
    else:
        # Nếu có người dùng hiện tại, lấy thành viên không bao gồm người dùng hiện tại  
        members = (
            db.query(ChannelMembers)
            .filter((ChannelMembers.channel_id == channel_id) & (ChannelMembers.user_id != current_user.id))
            .all()
        )

    # Thêm thông tin người dùng vào danh sách thành viên
    for member in members:
        member.user = db.query(Users).filter(Users.id == member.user_id).first()

    return members