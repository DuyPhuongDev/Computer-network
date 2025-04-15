import logging
import os

def setup_logger(logger_name, log_file, level=logging.INFO):
    """
    Thiết lập logger với tên và tệp log cụ thể
    
    Args:
        logger_name: Tên của logger
        log_file: Đường dẫn tới tệp log
        level: Mức độ log (mặc định là INFO)
        
    Returns:
        Logger object
    """
    # Tạo thư mục logs nếu chưa tồn tại
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # Tạo logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    
    # Tạo file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    
    # Tạo console handler với mức INFO
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # Tạo formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Nếu logger đã có handlers, xóa handlers cũ
    if logger.handlers:
        logger.handlers.clear()
    
    # Thêm handlers vào logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def get_logger(module_name):
    """
    Lấy logger cho module cụ thể
    
    Args:
        module_name: Tên của module
        
    Returns:
        Logger object
    """
    log_file = f"logs/{module_name}.log"
    return setup_logger(module_name, log_file) 