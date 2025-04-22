import logging
import os
import json
from datetime import datetime
import time

class ConnectionLogger:
    """
    Logger để theo dõi các kết nối host (centralized hoặc channel hosting)
    Tự động xoay vòng tệp log khi số lượng bản ghi vượt quá giới hạn.
    """
    def __init__(self, log_file="logs/connections.log", max_records=10000):
        # Tạo thư mục logs nếu chưa tồn tại
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        self.log_file = log_file
        self.max_records = max_records
        self.record_count = 0
        
        # Đếm số lượng bản ghi hiện tại nếu tệp đã tồn tại
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                self.record_count = sum(1 for _ in f)
                
    def log_connection(self, host_type, host_id, user_id, channel_id=None, event_type="connect", metadata=None):
        """
        Ghi lại thông tin kết nối
        
        Args:
            host_type: Loại host (centralized_host/channel_hosting/text_channel/message/signaling)
            host_id: ID của host
            user_id: ID của người dùng kết nối
            channel_id: ID của channel (nếu có)
            event_type: Loại sự kiện (connect/disconnect/create/send_message/offer/answer/ice_candidate)
            metadata: Thông tin bổ sung (nếu có)
        """
        if self.record_count >= self.max_records:
            self._rotate_log()
            
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "host_type": host_type, 
            "host_id": host_id,
            "user_id": user_id,
            "channel_id": channel_id,
            "event_type": event_type,
            "metadata": metadata or {}
        }
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        self.record_count += 1
            
    def _rotate_log(self):
        """Xoay vòng tệp log khi số lượng bản ghi vượt quá giới hạn"""
        # Tạo tên tệp log backup với timestamp
        backup_timestamp = int(time.time())
        backup_file = f"{self.log_file}.{backup_timestamp}"
        
        # Đổi tên tệp log hiện tại thành tệp backup
        if os.path.exists(self.log_file):
            os.rename(self.log_file, backup_file)
            
        # Reset số lượng bản ghi
        self.record_count = 0
        
    def get_connection_logs(self, limit=100, offset=0, filters=None):
        """
        Lấy danh sách bản ghi log theo giới hạn và vị trí
        
        Args:
            limit: Số lượng bản ghi tối đa
            offset: Vị trí bắt đầu
            filters: Các điều kiện lọc (dictionary)
            
        Returns:
            Danh sách bản ghi log
        """
        logs = []
        
        if not os.path.exists(self.log_file):
            return logs
            
        with open(self.log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Áp dụng bộ lọc nếu có
        filtered_lines = []
        if filters:
            for line in lines:
                try:
                    entry = json.loads(line)
                    match = True
                    for key, value in filters.items():
                        if key in entry and entry[key] != value:
                            match = False
                            break
                    if match:
                        filtered_lines.append(line)
                except json.JSONDecodeError:
                    continue
        else:
            filtered_lines = lines
            
        # Phân trang
        paginated_lines = filtered_lines[offset:offset + limit]
                
        # Chuyển đổi từ JSON sang dictionary
        for line in paginated_lines:
            try:
                logs.append(json.loads(line))
            except json.JSONDecodeError:
                continue
                
        return logs
    
    def get_stats(self):
        """
        Lấy thống kê về các loại sự kiện và host
        
        Returns:
            Dictionary chứa thông tin thống kê
        """
        if not os.path.exists(self.log_file):
            return {
                "total_records": 0,
                "host_types": {},
                "event_types": {}
            }
            
        host_types = {}
        event_types = {}
        total_records = 0
        
        with open(self.log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    total_records += 1
                    
                    # Đếm theo host_type
                    host_type = entry.get("host_type")
                    if host_type:
                        host_types[host_type] = host_types.get(host_type, 0) + 1
                        
                    # Đếm theo event_type
                    event_type = entry.get("event_type")
                    if event_type:
                        event_types[event_type] = event_types.get(event_type, 0) + 1
                        
                except json.JSONDecodeError:
                    continue
                    
        return {
            "total_records": total_records,
            "host_types": host_types,
            "event_types": event_types
        }

# Tạo instance mặc định của ConnectionLogger
connection_logger = ConnectionLogger()

def get_connection_logger():
    """
    Lấy instance mặc định của ConnectionLogger
    
    Returns:
        ConnectionLogger instance
    """
    return connection_logger 