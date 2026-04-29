import time
import gc
import network
import uasyncio as asyncio
from machine import WDT

from PicoBot import config, hardware_map as hw
from PicoBot import safety, drive, arm, telemetry
from PicoBot import protocol_ws as ws
from PicoBot import http_server as http
from PicoBot import show_moves

# ── drive target (written by WS handler and show-off moves) ──────────────────
_drive_f = 0
_drive_s = 0
_drive_r = 0

def _set_drive(f, s, r):
    global _drive_f, _drive_s, _drive_r
    _drive_f, _drive_s, _drive_r = f, s, r

# ── seq tracking for staleness rejection ─────────────────────────────────────
_last_drive_seq = -1
_last_arm_seq   = -1

def _seq_newer(incoming, last):
    """16-bit wraparound-aware comparison."""
    diff = (incoming - last) & 0xFFFF
    return 0 < diff < 32768

# ── response seq counter ─────────────────────────────────────────────────────
_resp_seq = 0

def _rseq():
    global _resp_seq
    _resp_seq = (_resp_seq + 1) & 0xFFFF
    return _resp_seq

# ── Wi-Fi AP ──────────────────────────────────────────────────────────────────

def _start_wifi():
    ap = network.WLAN(network.AP_IF)
    ap.active(False)
    ap.config(
        ssid=config.WIFI_SSID,
        password=config.WIFI_PASSWORD,
        channel=config.WIFI_CHANNEL,
    )
    ap.active(True)
    t = time.ticks_ms()
    while not ap.active():
        if time.ticks_diff(time.ticks_ms(), t) > 10000:
            raise RuntimeError("Wi-Fi AP failed to start")
        time.sleep_ms(100)
    print("wifi: AP active", ap.ifconfig())

# ── WebSocket handler ─────────────────────────────────────────────────────────

async def _ws_handler(reader, writer):
    global _last_drive_seq, _last_arm_seq, _drive_f, _drive_s, _drive_r

    telemetry.set_writer(writer)
    _last_drive_seq = _last_arm_seq = -1

    try:
        # Handshake greeting
        await ws.send(writer, f"HELLO,1,picobot-fw-v2")

        while True:
            try:
                opcode, data = await ws.recv_frame(reader)
            except OSError:
                break

            if opcode == ws.OP_CLOSE:
                break
            if opcode == ws.OP_PING:
                writer.write(ws.make_frame(b'\x8a\x00'))  # pong
                await writer.drain()
                continue
            if opcode != ws.OP_TEXT:
                continue

            # Parse and route
            try:
                await _dispatch(writer, data)
            except Exception as e:
                # Parse failure → same path as deadman
                safety.hard_disable()
                _set_drive(0, 0, 0)
                try:
                    await ws.send(writer, f"ERR,{_rseq()},parse,{e}")
                except Exception:
                    pass

    finally:
        safety.hard_disable()
        _set_drive(0, 0, 0)
        show_moves.stop()
        telemetry.clear_writer()
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass


async def _dispatch(writer, text):
    global _last_drive_seq, _last_arm_seq

    parts = text.split(',')
    cmd = parts[0]

    if cmd == 'HELLO':
        await ws.send(writer, f"HELLO,1,picobot-fw-v2")

    elif cmd == 'PING':
        seq = int(parts[1])
        ts  = parts[2] if len(parts) > 2 else '0'
        await ws.send(writer, f"PONG,{_rseq()},{ts}")

    elif cmd == 'ARM':
        seq = int(parts[1])
        val = int(parts[2])
        if val == 0:
            safety.hard_disable()
            _set_drive(0, 0, 0)
        else:
            safety.do_arm()
        await ws.send(writer, f"ACK,{_rseq()}")

    elif cmd == 'STOP':
        safety.hard_disable()
        _set_drive(0, 0, 0)
        show_moves.stop()
        await ws.send(writer, f"ACK,{_rseq()}")

    elif cmd == 'D':
        seq = int(parts[1])
        if not _seq_newer(seq, _last_drive_seq) and _last_drive_seq != -1:
            return
        _last_drive_seq = seq
        f = int(parts[2])
        s = int(parts[3])
        r = int(parts[4])
        safety.feed_deadman()
        _set_drive(f, s, r)

    elif cmd == 'A':
        seq = int(parts[1])
        if not _seq_newer(seq, _last_arm_seq) and _last_arm_seq != -1:
            return
        _last_arm_seq = seq
        base  = int(parts[2])
        arm_a = int(parts[3])
        claw  = int(parts[4])
        arm.set_targets(base, arm_a, claw)

    elif cmd == 'M':
        seq = int(parts[1])
        move_id = parts[2]
        speed   = int(parts[3])
        ok = await show_moves.start(move_id, speed, _set_drive)
        if ok:
            await ws.send(writer, f"ACK,{_rseq()}")
        else:
            await ws.send(writer, f"ERR,{_rseq()},unknown_move,{move_id}")

    elif cmd == 'CFG':
        seq = int(parts[1])
        key = parts[2]
        val = parts[3]
        if key == 'debug':
            telemetry.set_debug(val == '1')
            await ws.send(writer, f"ACK,{_rseq()}")
        else:
            await ws.send(writer, f"ERR,{_rseq()},unknown_cfg,{key}")

    else:
        raise ValueError(f"unknown cmd: {cmd}")

# ── background tasks ──────────────────────────────────────────────────────────

async def _motor_loop():
    """Apply drive target to motors at ~50 Hz."""
    while True:
        drive.apply(_drive_f, _drive_s, _drive_r, safety.is_armed())
        await asyncio.sleep_ms(20)


async def _servo_loop():
    while True:
        arm.tick()
        await asyncio.sleep_ms(config.SERVO_TICK_MS)


async def _distance_loop():
    """HC-SR04 measurement at DIST_INTERVAL_MS."""
    from machine import Pin
    import time as _time

    trig = Pin(hw.TRIG_PIN, Pin.OUT)
    echo = Pin(hw.ECHO_PIN, Pin.IN)

    while True:
        await asyncio.sleep_ms(config.DIST_INTERVAL_MS)
        try:
            trig.value(0)
            await asyncio.sleep_ms(2)
            trig.value(1)
            _time.sleep_us(10)
            trig.value(0)

            t0 = _time.ticks_ms()
            while echo.value() == 0:
                if _time.ticks_diff(_time.ticks_ms(), t0) > 50:
                    telemetry.dist_cm = -1
                    break
            else:
                t1 = _time.ticks_us()
                while echo.value() == 1:
                    if _time.ticks_diff(_time.ticks_us(), t1) > 30000:
                        telemetry.dist_cm = -1
                        break
                else:
                    t2 = _time.ticks_us()
                    telemetry.dist_cm = _time.ticks_diff(t2, t1) * 0.01715
        except Exception:
            telemetry.dist_cm = -1


async def _connection_handler(reader, writer):
    await http.handle(reader, writer, _ws_handler)


# ── main entry ───────────────────────────────────────────────────────────────

async def _app_run():
    drive.init()
    arm.init()

    safety.init(hw.MOTOR_ENABLE_PIN)

    asyncio.create_task(_motor_loop())
    asyncio.create_task(_servo_loop())
    asyncio.create_task(telemetry.send_loop())
    asyncio.create_task(_distance_loop())

    server = await asyncio.start_server(_connection_handler, "0.0.0.0", 80, backlog=4)
    print("app: server listening on :80")

    while True:
        gc.collect()
        await asyncio.sleep_ms(1000)


def main():
    _start_wifi()

    wdt = WDT(timeout=config.WDT_TIMEOUT_MS) if config.ENABLE_WDT else None

    async def _wdt_feed():
        while True:
            if wdt is not None:
                wdt.feed()
            await asyncio.sleep_ms(500)

    async def supervisor():
        asyncio.create_task(_wdt_feed())
        while True:
            try:
                await _app_run()
            except Exception as exc:
                safety.hard_disable()
                print("FATAL:", exc)
                await asyncio.sleep_ms(1000)

    asyncio.run(supervisor())
