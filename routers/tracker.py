from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from routers.signaling import active_connections  # Import từ signaling

router = APIRouter(prefix="/tracker", tags=["tracker"])

class PeerResponse(BaseModel):
    peer_id: str
    channel_id: int

@router.get("/get_list", response_model=List[PeerResponse])
async def get_list(channel_id: Optional[int] = None):
    if channel_id:
        if channel_id not in active_connections:
            raise HTTPException(status_code=404, detail="Channel not found")
        return [{"peer_id": pid, "channel_id": channel_id} for pid in active_connections[channel_id].keys()]
    return [{"peer_id": pid, "channel_id": cid} for cid in active_connections for pid in active_connections[cid].keys()]