from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload, joinedload
from pydantic import BaseModel
from typing import Optional
from database import get_db
from models import Servers, Users, Channels, ChannelType, ChannelMembers
from service.auth import get_current_user
from routers.channel import ChannelResponse
import uuid

router = APIRouter(prefix="/servers", tags=["servers"])

class ServerRequest(BaseModel):
    name: str
    color: str
    is_private: bool

class ServerResponse(BaseModel):
    id: int
    name: str
    host_user_id: int
    color: str
    is_private: bool
    channels: list[ChannelResponse]

    class Config:
        from_attributes = True

# create server
@router.post("/create", response_model=ServerResponse, status_code=status.HTTP_201_CREATED)
async def create_server(
    server: ServerRequest,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:    
        new_server = Servers(
            name=server.name,
            color=server.color,
            host_user_id=current_user.id,
            is_private=server.is_private
        )
        db.add(new_server)
        db.commit()
        db.refresh(new_server)
        
        # create default channel
        default_text_channel = Channels(
            name="general",
            server_id=new_server.id,
            channel_type=ChannelType.text
        )
        db.add(default_text_channel)
        db.commit()
        db.refresh(default_text_channel)
        
        # create default voice channel
        default_voice_channel = Channels(
            name="general",
            server_id=new_server.id,
            channel_type=ChannelType.voice
        )
        db.add(default_voice_channel)
        db.commit()
        db.refresh(default_voice_channel)
        
        # create default text channel member
        default_text_channel_member = ChannelMembers(
            channel_id=default_text_channel.id,
            user_id=current_user.id,
            role="host"
        )
        db.add(default_text_channel_member)
        db.commit()
        db.refresh(default_text_channel_member)
        
        # create default voice channel member
        default_voice_channel_member = ChannelMembers(
            channel_id=default_voice_channel.id,
            user_id=current_user.id,
            role="host"
        )
        db.add(default_voice_channel_member)
        db.commit()
        db.refresh(default_voice_channel_member)
        
        # Eager load channels và members, bao gồm user
        new_server = (
            db.query(Servers)
            .options(joinedload(Servers.channels).joinedload(Channels.members).joinedload(ChannelMembers.user))
            .get(new_server.id)
        )
        return new_server
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
# get all servers
@router.get("", response_model=list[ServerResponse], status_code=status.HTTP_200_OK)
async def get_all_servers(
    db: Session = Depends(get_db)
):
    try:
        # Eager load channels và members, bao gồm user
        servers = (
            db.query(Servers)
            .options(joinedload(Servers.channels).joinedload(Channels.members).joinedload(ChannelMembers.user))
            .all()
        )
        return servers
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# get server by id
@router.get("/{server_id}", response_model=ServerResponse, status_code=status.HTTP_200_OK)
async def get_server_by_id(server_id: int, db: Session = Depends(get_db)):
    try:
        # Eager load channels và members, bao gồm user
        server = (
            db.query(Servers)
            .options(joinedload(Servers.channels).joinedload(Channels.members).joinedload(ChannelMembers.user))
            .get(server_id)
        )
        if not server:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")
        return server
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
