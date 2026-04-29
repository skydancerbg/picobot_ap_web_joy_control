import hashlib
import ubinascii

_MAGIC = b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

# WebSocket opcodes
OP_TEXT   = 0x1
OP_BINARY = 0x2
OP_CLOSE  = 0x8
OP_PING   = 0x9
OP_PONG   = 0xA

# ── handshake ─────────────────────────────────────────────────────────────────

async def handshake(reader, writer):
    """
    Read an HTTP upgrade request and send the 101 response.
    Returns the request path, or raises OSError on failure.
    """
    # Request line
    line = await reader.readline()
    parts = line.split()
    path = parts[1].decode() if len(parts) >= 2 else '/'

    # Headers
    ws_key = b''
    while True:
        line = await reader.readline()
        if line in (b'\r\n', b'\n', b''):
            break
        if b':' in line:
            name, _, val = line.partition(b':')
            if name.strip().lower() == b'sec-websocket-key':
                ws_key = val.strip()

    if not ws_key:
        raise OSError("missing Sec-WebSocket-Key")

    accept = ubinascii.b2a_base64(
        hashlib.sha1(ws_key + _MAGIC).digest()
    ).strip()

    writer.write(
        b"HTTP/1.1 101 Switching Protocols\r\n"
        b"Upgrade: websocket\r\n"
        b"Connection: Upgrade\r\n"
        b"Sec-WebSocket-Accept: " + accept + b"\r\n"
        b"\r\n"
    )
    await writer.drain()
    return path


# ── frame receive ─────────────────────────────────────────────────────────────

async def recv_frame(reader):
    """
    Read one WebSocket frame. Returns (opcode, text_or_bytes).
    Raises OSError on connection close or error.
    """
    h = await reader.readexactly(2)
    opcode = h[0] & 0x0F
    masked = (h[1] >> 7) & 1
    length = h[1] & 0x7F

    if length == 126:
        ext = await reader.readexactly(2)
        length = (ext[0] << 8) | ext[1]
    elif length == 127:
        ext = await reader.readexactly(8)
        length = int.from_bytes(ext, 'big')

    if length > 256:
        raise OSError("frame too large")

    mask_key = await reader.readexactly(4) if masked else None
    payload = bytearray(await reader.readexactly(length))

    if mask_key:
        for i in range(length):
            payload[i] ^= mask_key[i & 3]

    if opcode == OP_TEXT:
        return opcode, payload.decode()
    return opcode, bytes(payload)


# ── frame send ────────────────────────────────────────────────────────────────

def make_frame(text):
    """Build an unmasked text WebSocket frame."""
    if isinstance(text, str):
        text = text.encode()
    n = len(text)
    if n < 126:
        header = bytes([0x81, n])
    elif n < 65536:
        header = bytes([0x81, 126, n >> 8, n & 0xFF])
    else:
        raise ValueError("frame too large")
    return header + text


async def send(writer, text):
    """Send a text frame. writer must still be open."""
    writer.write(make_frame(text))
    await writer.drain()
