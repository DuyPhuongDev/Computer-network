# Video Chat App Backend

## Tổng quan / Overview

Đây là backend cho ứng dụng video chat xây dựng với FastAPI. Hệ thống hỗ trợ chat văn bản, cuộc gọi video/audio thông qua WebRTC, quản lý người dùng và kênh truyền thông.

This is the backend for a video chat application built with FastAPI. The system supports text chat, video/audio calls via WebRTC, user management, and communication channels.

## Tính năng / Features

- **Xác thực người dùng** / **User Authentication**: Đăng ký, đăng nhập và quản lý người dùng. / Registration, login, and user management.
- **Quản lý máy chủ và kênh** / **Servers and Channels Management**: Tạo và quản lý máy chủ và kênh chat. / Create and manage servers and chat channels.
- **Chat văn bản** / **Text Chat**: Chat thời gian thực giữa người dùng. / Real-time text chat between users.
- **Gọi Video/Audio** / **Video/Audio Calls**: Tích hợp WebRTC cho cuộc gọi video và audio. / WebRTC integration for video and audio calls.
- **Hệ thống ghi nhật ký** / **Logging System**: Ghi lại tất cả kết nối, tin nhắn và sự kiện signaling. / Records all connections, messages, and signaling events.
- **API REST** / **REST API**: Giao diện API đầy đủ cho các tác vụ quản lý. / Full API interface for management tasks.
- **WebSockets**: Kết nối thời gian thực cho chat và signaling. / Real-time connections for chat and signaling.

## Cài đặt / Installation

### Yêu cầu / Requirements

- Python 3.8+
- PostgreSQL (hoặc SQLite cho phát triển) / (or SQLite for development)

### Cài đặt / Setup

1. **Sao chép mã nguồn / Clone the repository**:

   ```bash
   git clone https://github.com/yourusername/video-chat-app.git
   cd video-chat-app/backend
   ```

2. **Cài đặt các gói phụ thuộc / Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Thiết lập biến môi trường / Set up environment variables**:

   ```bash
   cp .env.example .env
   # Chỉnh sửa .env để cấu hình / Edit .env to configure
   ```

4. **Chạy ứng dụng / Run the application**:
   ```bash
   python main.py
   ```

Ứng dụng sẽ khởi chạy trên http://localhost:8000.

The application will be running on http://localhost:8000.

## API Documentation

### Xác thực / Authentication

- `POST /auth/register` - Đăng ký người dùng mới / Register a new user
- `POST /auth/login` - Đăng nhập / Login
- `GET /auth/me` - Lấy thông tin người dùng hiện tại / Get current user info

### Máy chủ / Servers

- `POST /servers/create` - Tạo máy chủ mới / Create a new server
- `GET /servers` - Lấy danh sách máy chủ / Get all servers
- `GET /servers/{server_id}` - Lấy thông tin máy chủ theo ID / Get server by ID

### Kênh / Channels

- `POST /channels/create` - Tạo kênh mới / Create a new channel
- `GET /channels/{channel_id}` - Lấy thông tin kênh theo ID / Get channel by ID
- `GET /channels/{channel_id}/members` - Lấy danh sách thành viên kênh / Get channel members

### WebSockets

- `WebSocket /ws/{channel_id}` - Kết nối đến kênh chat văn bản / Connect to text chat channel
- `WebSocket /ws/{channel_id}/signaling` - Kết nối đến kênh signaling cho WebRTC / Connect to signaling channel for WebRTC

## Hệ thống ghi nhật ký / Logging System

Backend tích hợp hệ thống ghi nhật ký toàn diện để theo dõi:

The backend integrates a comprehensive logging system to track:

- **Kết nối host / Host Connections**: Ghi lại khi người dùng kết nối đến máy chủ trung tâm hoặc kênh. / Records when users connect to centralized hosts or channels.
- **Tin nhắn / Messages**: Ghi lại mọi tin nhắn được gửi qua kênh chat. / Records all messages sent through chat channels.
- **Sự kiện Signaling / Signaling Events**: Ghi lại các sự kiện WebRTC như offer, answer và ice_candidate. / Records WebRTC events such as offer, answer, and ice_candidate.

Nhật ký được lưu dưới dạng JSON và tự động xoay vòng khi vượt quá 10.000 bản ghi.

Logs are stored in JSON format and automatically rotated when exceeding 10,000 records.

## Docker

Dự án bao gồm Dockerfile để dễ dàng triển khai.

The project includes a Dockerfile for easy deployment.

```bash
# Xây dựng image / Build the image
docker build -t video-chat-backend .

# Chạy container / Run the container
docker run -p 8000:8000 video-chat-backend
```

## Liên hệ / Contact

Vui lòng tạo issue trên GitHub nếu bạn gặp bất kỳ vấn đề nào.

Please create an issue on GitHub if you encounter any problems.
