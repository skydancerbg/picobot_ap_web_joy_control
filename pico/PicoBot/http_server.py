import os
import json
import uasyncio as asyncio
from PicoBot import protocol_ws as ws

_INDEX_PATH = '/PicoBot/www/index.html'


async def handle(reader, writer, ws_handler_fn):
    """
    Route one incoming TCP connection.
    ws_handler_fn(reader, writer) is called for WebSocket upgrade requests.
    """
    try:
        line = await asyncio.wait_for(reader.readline(), timeout=5)
        parts = line.split()
        if len(parts) < 2:
            writer.close()
            return
        method = parts[0].decode()
        path = parts[1].decode().split('?')[0]

        # Peek at headers to detect WebSocket upgrade
        headers = {}
        while True:
            h = await reader.readline()
            if h in (b'\r\n', b'\n', b''):
                break
            if b':' in h:
                k, _, v = h.partition(b':')
                headers[k.strip().lower()] = v.strip()

        upgrade = headers.get(b'upgrade', b'').lower()

        if upgrade == b'websocket' and path == '/ws':
            # Re-construct a minimal header stream for the handshake function.
            # We already consumed the headers, so we replay directly.
            ws_key = headers.get(b'sec-websocket-key', b'')
            await _ws_reply(writer, ws_key)
            await ws_handler_fn(reader, writer)
            return

        if method == 'GET':
            if path == '/':
                await _serve_file(writer, _INDEX_PATH, 'text/html; charset=utf-8')
            elif path == '/health':
                await _send_text(writer, 200, 'OK')
            elif path == '/status':
                from PicoBot import safety, drive, arm
                b, a, c = arm.get_positions()
                data = {
                    'armed': safety.is_armed(),
                    'drive_ok': drive.is_ok(),
                    'drive_err': drive._drive_init_error,
                    'wheels': drive.get_wheel_outputs(),
                    'arm': {'base': b, 'arm': a, 'claw': c},
                }
                await _send_json(writer, data)
            elif path == '/test_motor':
                # Direct PCA9685 test — bypasses ARM/joystick/deadman.
                # Commands FL motor (ch 0,1,2) at 30% forward for 1 second.
                # Wheels must be LIFTED before calling this endpoint.
                from PicoBot import drive, hardware_map as hw
                result = {}
                try:
                    if not drive.is_ok():
                        result = {'error': 'drive not initialized', 'detail': drive._drive_init_error}
                    else:
                        duty = int(0.30 * 4095)  # 30%
                        fl = hw.MOTOR_FL_CHS      # (0, 1, 2)
                        drive._pca.ch(fl[0], 0, duty)   # PWM 30%
                        drive._pca.ch(fl[1], 0, 0)      # IN1 LOW  → forward
                        drive._pca.ch(fl[2], 0, 4095)   # IN2 HIGH → forward
                        await asyncio.sleep_ms(1000)
                        drive.zero_all()
                        result = {'status': 'FL motor 30% forward 1s — done', 'duty': duty}
                except Exception as e:
                    result = {'error': str(e)}
                await _send_json(writer, result)
            elif path == '/i2c':
                from machine import I2C, Pin
                from PicoBot import hardware_map as hw
                try:
                    i2c0 = I2C(hw.MOTOR_I2C_BUS,
                               sda=Pin(hw.MOTOR_I2C_SDA),
                               scl=Pin(hw.MOTOR_I2C_SCL),
                               freq=hw.MOTOR_I2C_FREQ)
                    motor_addrs = ['0x{:02x}'.format(a) for a in i2c0.scan()]
                except Exception as e:
                    motor_addrs = ['error: ' + str(e)]
                try:
                    i2c1 = I2C(hw.ARM_I2C_BUS,
                               sda=Pin(hw.ARM_I2C_SDA),
                               scl=Pin(hw.ARM_I2C_SCL),
                               freq=hw.ARM_I2C_FREQ)
                    arm_addrs = ['0x{:02x}'.format(a) for a in i2c1.scan()]
                except Exception as e:
                    arm_addrs = ['error: ' + str(e)]
                data = {
                    'motor_bus': hw.MOTOR_I2C_BUS,
                    'motor_sda': hw.MOTOR_I2C_SDA,
                    'motor_scl': hw.MOTOR_I2C_SCL,
                    'motor_addrs': motor_addrs,
                    'arm_bus': hw.ARM_I2C_BUS,
                    'arm_sda': hw.ARM_I2C_SDA,
                    'arm_scl': hw.ARM_I2C_SCL,
                    'arm_addrs': arm_addrs,
                }
                await _send_json(writer, data)
            elif path == '/api/stop':
                from PicoBot import safety, drive
                safety.hard_disable()
                await _send_text(writer, 200, 'stopped')
            else:
                await _send_text(writer, 404, 'Not Found')
        else:
            await _send_text(writer, 405, 'Method Not Allowed')

    except Exception as e:
        print('http: error:', e)
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass


async def _ws_reply(writer, ws_key):
    """Send 101 directly using the already-read ws_key."""
    import hashlib, ubinascii
    _MAGIC = b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    accept = ubinascii.b2a_base64(
        hashlib.sha1(ws_key + _MAGIC).digest()
    ).strip()
    writer.write(
        b"HTTP/1.1 101 Switching Protocols\r\n"
        b"Upgrade: websocket\r\n"
        b"Connection: Upgrade\r\n"
        b"Sec-WebSocket-Accept: " + accept + b"\r\n\r\n"
    )
    await writer.drain()


async def _serve_file(writer, path, content_type):
    try:
        size = os.stat(path)[6]
    except OSError:
        await _send_text(writer, 404, 'Not Found')
        return
    writer.write(
        f"HTTP/1.1 200 OK\r\n"
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {size}\r\n"
        f"Connection: close\r\n\r\n".encode()
    )
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(512)
            if not chunk:
                break
            writer.write(chunk)
            await writer.drain()


async def _send_text(writer, code, body):
    b = body.encode() if isinstance(body, str) else body
    writer.write(
        f"HTTP/1.1 {code} \r\n"
        f"Content-Type: text/plain\r\n"
        f"Content-Length: {len(b)}\r\n"
        f"Connection: close\r\n\r\n".encode() + b
    )
    await writer.drain()


async def _send_json(writer, obj):
    body = json.dumps(obj).encode()
    writer.write(
        b"HTTP/1.1 200 OK\r\n"
        b"Content-Type: application/json\r\n"
        b"Content-Length: " + str(len(body)).encode() + b"\r\n"
        b"Connection: close\r\n\r\n" + body
    )
    await writer.drain()
