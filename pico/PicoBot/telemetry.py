import time
import uasyncio as asyncio
from PicoBot import config, safety, drive, arm, protocol_ws as ws

_seq = 0
_ws_writer = None      # set by app.py on WS connect
_debug = False
_uptime_start = time.ticks_ms()

# latest distance reading (cm), updated by distance task in app.py
dist_cm = -1

def set_writer(writer):
    global _ws_writer
    _ws_writer = writer

def clear_writer():
    global _ws_writer
    _ws_writer = None

def set_debug(enabled):
    global _debug
    _debug = enabled

def _next_seq():
    global _seq
    _seq = (_seq + 1) & 0xFFFF
    return _seq

async def send_loop():
    """5 Hz telemetry loop. Runs as an asyncio task."""
    while True:
        await asyncio.sleep_ms(config.TELEMETRY_INTERVAL_MS)
        w = _ws_writer
        if w is None:
            continue
        try:
            await _send_state(w)
            if _debug:
                await _send_debug(w)
        except Exception:
            pass   # writer will be cleared by WS handler on close


async def _send_state(writer):
    fl, bl, fr, br = drive.get_wheel_outputs()
    base, arm_ang, claw = arm.get_positions()
    uptime = time.ticks_diff(time.ticks_ms(), _uptime_start)
    seq = _next_seq()
    frame = (
        f"S,{seq},normal,{1 if safety.is_armed() else 0},"
        f"{int(fl)},{int(bl)},{int(fr)},"
        f"{int(base)},{int(arm_ang)},{int(claw)},"
        f"{int(dist_cm)},{uptime}"
    )
    await ws.send(writer, frame)


async def _send_debug(writer):
    fl, bl, fr, br = drive.get_wheel_outputs()
    import gc
    seq = _next_seq()
    frame = f"SD,{seq},{int(fl)},{int(bl)},{int(fr)},{int(br)},0,{gc.mem_free()}"
    await ws.send(writer, frame)
