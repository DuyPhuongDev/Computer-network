<a id="readme-top"></a>

<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="">
    <img src="hcmut.png" alt="HCMUT Logo" width="160" height="160">
  </a>

  <h3 align="center">Discord-like Chat Application</h3>

  <p align="center">
    Đây là backend cho ứng dụng video chat xây dựng với FastAPI. Hệ thống hỗ trợ chat văn bản, cuộc gọi video/audio thông qua WebRTC, quản lý người dùng và kênh truyền thông.
  </p>
</div>


## Tính năng / Features

- **Xác thực người dùng**: Đăng ký, đăng nhập và quản lý người dùng.
- **Quản lý máy chủ và kênh**: Tạo và quản lý máy chủ và kênh chat.
- **Chat văn bản**: Chat thời gian thực giữa người dùng.
- **Gọi Video/Audio**: Tích hợp WebRTC cho cuộc gọi video và audio.
- **Hệ thống ghi nhật ký**: Ghi lại tất cả kết nối, tin nhắn và sự kiện signaling.
- **REST API**: Giao diện API đầy đủ cho các tác vụ quản lý.
- **WebSockets**: Kết nối thời gian thực cho chat và signaling.

## Cài đặt / Installation

### Yêu cầu / Requirements

- Python 3.8+
- SQLite

### Cài đặt / Setup

1. **Sao chép mã nguồn**:

   ```bash
   git clone https://github.com/DuyPhuongDev/Computer-network.git
   cd Computer-network/backend
   ```

2. **Cài đặt các gói phụ thuộc**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Thiết lập biến môi trường**:

   ```bash
   cp .env.example .env
   # Chỉnh sửa .env để cấu hình
   ```

4. **Chạy ứng dụng**:
   ```bash
   python3 main.py
   ```

Ứng dụng sẽ khởi chạy trên http://localhost:8000.

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

## Docker

Dự án bao gồm Dockerfile để dễ dàng triển khai.

```bash
# Xây dựng image / Build the image
docker build -t video-chat-backend .

# Chạy container / Run the container
docker run -p 8000:8000 video-chat-backend
```
