from fastapi import Depends
from sqlalchemy.orm import Session
from database import ChannelData, get_db

def sync_channel_data(channel_id: str, content_type: str, content: str, db: Session = Depends(get_db)):
    new_data = ChannelData(channel_id=channel_id, content_type=content_type, content=content)
    db.add(new_data)
    db.commit()
    return {"status": "synced"}

def get_channel_data(channel_id: str, db: Session = Depends(get_db)):
    data = db.query(ChannelData).filter(ChannelData.channel_id == channel_id).all()
    return [{"content_type": d.content_type, "content": d.content} for d in data]