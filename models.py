from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()


class ChannelType(enum.Enum):
    text = "text"
    voice = "voice"

class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    full_name = Column(String)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    status = Column(String, default='online')
    messages = relationship('Messages', back_populates='sender')
    members = relationship('ChannelMembers', back_populates='user')
    servers = relationship('Servers', back_populates='host_user')

# 1 user can have many servers
# 1 server can have many channels

class Servers(Base):
    __tablename__ = 'servers'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    host_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    color = Column(String)
    host_user = relationship('Users', back_populates='servers')
    channels = relationship('Channels', back_populates='server')
    is_active = Column(Boolean, default=True)
    is_private = Column(Boolean, default=False)

class Channels(Base):
    __tablename__ = 'channels'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    channel_type = Column(Enum(ChannelType), nullable=False)
    members = relationship('ChannelMembers', back_populates='channel')
    messages = relationship('Messages', back_populates='channel')
    server_id = Column(Integer, ForeignKey('servers.id'), nullable=False)
    server = relationship('Servers', back_populates='channels')
    
class ChannelMembers(Base):
    __tablename__ = 'channel_members'

    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey('channels.id'))
    channel = relationship('Channels', back_populates='members')
    user_id = Column(Integer, ForeignKey('users.id'))
    role = Column(String, default='user')
    user = relationship('Users', back_populates='members')
    __table_args__ = (UniqueConstraint('channel_id', 'user_id', name='uix_channel_user'),)

class Messages(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String)
    channel_id = Column(Integer, ForeignKey('channels.id'))
    channel = relationship('Channels', back_populates='messages')
    sender_id = Column(Integer, ForeignKey('users.id'))
    sender = relationship('Users', back_populates='messages')
    created_at = Column(String)
