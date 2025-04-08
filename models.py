from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    full_name = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    status = Column(String, default='online')
    # 1:N relationship with channels
    channels = relationship('Channels', back_populates='host_user')
    messages = relationship('Messages', back_populates='sender')
    members = relationship('ChannelMembers', back_populates='user')

class Peers(Base):
    __tablename__ = "peers"
    id = Column(Integer, primary_key=True, index=True)
    peer_id = Column(String, unique=True, index=True)  # UUID thay vì "ip:port"
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    channel_id = Column(Integer, ForeignKey('channels.id'), nullable=True)
    channel = relationship('Channels', back_populates='peers')

class Channels(Base):
    __tablename__ = 'channels'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    host_user_id = Column(Integer, ForeignKey('users.id'))
    host_user = relationship('Users', back_populates='channels')
    members = relationship('ChannelMembers', back_populates='channel')
    messages = relationship('Messages', back_populates='channel')
    peers = relationship('Peers', back_populates='channel')
    is_active = Column(Boolean, default=True)  # Channel đang hoạt động không
    
class ChannelMembers(Base):
    __tablename__ = 'channel_members'

    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey('channels.id'))
    channel = relationship('Channels', back_populates='members')
    user_id = Column(Integer, ForeignKey('users.id'))
    role = Column(String, default='user')
    user = relationship('Users', back_populates='members')

class Messages(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String)
    channel_id = Column(Integer, ForeignKey('channels.id'))
    channel = relationship('Channels', back_populates='messages')
    sender_id = Column(Integer, ForeignKey('users.id'))
    sender = relationship('Users', back_populates='messages')
    created_at = Column(DateTime, default=datetime.now)
