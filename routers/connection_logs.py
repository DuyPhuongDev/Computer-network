from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from database import get_db
from models import Users, ChannelMembers
from service.auth import get_current_user
from service.connection_logger import get_connection_logger
from service.logger import get_logger
import os

# Tạo logger cho module connection_logs
logger = get_logger("connection_logs")
# Tạo connection logger để theo dõi kết nối host
connection_logger = get_connection_logger()

router = APIRouter(prefix="/connection-logs", tags=["connection-logs"])

class ConnectionLogResponse(BaseModel):
    timestamp: str
    host_type: str
    host_id: Any
    user_id: Any
    channel_id: Optional[Any] = None
    event_type: str
    metadata: Dict[str, Any]

@router.get("", response_model=List[ConnectionLogResponse], status_code=status.HTTP_200_OK)
async def get_connection_logs(
    limit: int = 100, 
    offset: int = 0,
    host_type: Optional[str] = None,
    event_type: Optional[str] = None,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lấy danh sách connection logs với phân trang
    
    Parameters:
    - limit: Số lượng bản ghi tối đa
    - offset: Vị trí bắt đầu
    - host_type: Lọc theo loại host (centralized_host, channel_hosting, text_channel, message, signaling)
    - event_type: Lọc theo loại sự kiện (connect, disconnect, create, send_message, offer, answer, ice_candidate)
    """
    try:
        # Kiểm tra xem người dùng có quyền admin trong bất kỳ channel nào hay không
        is_admin = db.query(ChannelMembers).filter(
            ChannelMembers.user_id == current_user.id,
            ChannelMembers.role == "host"
        ).first() is not None
            
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view connection logs"
            )
            
        logs = connection_logger.get_connection_logs(limit=limit, offset=offset)
        
        # Lọc theo host_type nếu có
        if host_type:
            logs = [log for log in logs if log.get("host_type") == host_type]
            
        # Lọc theo event_type nếu có
        if event_type:
            logs = [log for log in logs if log.get("event_type") == event_type]
            
        return logs
    except Exception as e:
        logger.error(f"Error getting connection logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/count", response_model=int, status_code=status.HTTP_200_OK)
async def get_connection_logs_count(
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lấy tổng số bản ghi connection logs
    """
    try:
        # Kiểm tra xem người dùng có quyền admin trong bất kỳ channel nào hay không
        is_admin = db.query(ChannelMembers).filter(
            ChannelMembers.user_id == current_user.id,
            ChannelMembers.role == "host"
        ).first() is not None
            
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view connection logs"
            )
            
        # Kiểm tra file logs tồn tại
        if not os.path.exists(connection_logger.log_file):
            return 0
            
        # Đếm số dòng trong file
        with open(connection_logger.log_file, 'r', encoding='utf-8') as f:
            count = sum(1 for _ in f)
            
        return count
    except Exception as e:
        logger.error(f"Error counting connection logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def clear_connection_logs(
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Xóa toàn bộ connection logs
    """
    try:
        # Kiểm tra xem người dùng có quyền admin trong bất kỳ channel nào hay không
        is_admin = db.query(ChannelMembers).filter(
            ChannelMembers.user_id == current_user.id,
            ChannelMembers.role == "host"
        ).first() is not None
            
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to clear connection logs"
            )
            
        # Xóa file logs nếu tồn tại
        if os.path.exists(connection_logger.log_file):
            os.remove(connection_logger.log_file)
            
        # Reset counter
        connection_logger.record_count = 0
        
        return None
    except Exception as e:
        logger.error(f"Error clearing connection logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

class StatsResponse(BaseModel):
    total_records: int
    host_types: Dict[str, int]
    event_types: Dict[str, int]

@router.get("/stats", response_model=StatsResponse, status_code=status.HTTP_200_OK)
async def get_connection_logs_stats(
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lấy thống kê về các loại sự kiện và host trong connection logs
    """
    try:
        # Kiểm tra xem người dùng có quyền admin trong bất kỳ channel nào hay không
        is_admin = db.query(ChannelMembers).filter(
            ChannelMembers.user_id == current_user.id,
            ChannelMembers.role == "host"
        ).first() is not None
            
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view connection logs statistics"
            )
            
        stats = connection_logger.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting connection logs statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 