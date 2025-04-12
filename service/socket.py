import json
import struct
import base64
import hashlib

# Hàm tính Sec-WebSocket-Accept (không cần dùng vì FastAPI tự xử lý handshake)
def compute_accept_key(key):
    GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    sha1 = hashlib.sha1((key + GUID).encode()).digest()
    return base64.b64encode(sha1).decode()

# Mã hóa frame (server không mask)
def encode_frame(message, opcode=0x1):
    payload = json.dumps(message).encode()
    length = len(payload)
    frame = bytearray()
    frame.append(0x80 | opcode)  # FIN=1, opcode=0x1 (text)
    if length <= 125:
        frame.append(length)
    elif length <= 65535:
        frame.append(126)
        frame.extend(struct.pack(">H", length))
    else:
        frame.append(127)
        frame.extend(struct.pack(">Q", length))
    frame.extend(payload)
    return bytes(frame)

# Giải mã frame (client có mask)
def decode_frame(data):
    if len(data) < 2:
        return 0, 0, b""  # Frame không hợp lệ

    fin = (data[0] & 0x80) >> 7
    opcode = data[0] & 0x0F
    mask = (data[1] & 0x80) >> 7
    payload_len = data[1] & 0x7F

    offset = 2
    if payload_len == 126:
        if len(data) < 4:
            return 0, 0, b""
        payload_len = struct.unpack(">H", data[2:4])[0]
        offset = 4
    elif payload_len == 127:
        if len(data) < 10:
            return 0, 0, b""
        payload_len = struct.unpack(">Q", data[2:10])[0]
        offset = 10

    if mask:
        if len(data) < offset + 4:
            return 0, 0, b""
        masking_key = data[offset:offset + 4]
        offset += 4
        if len(data) < offset + payload_len:
            return 0, 0, b""  # Frame chưa đủ dữ liệu
        masked_data = data[offset:offset + payload_len]
        unmasked_data = bytes(b ^ masking_key[i % 4] for i, b in enumerate(masked_data))
    else:
        unmasked_data = data[offset:offset + payload_len]

    return fin, opcode, unmasked_data