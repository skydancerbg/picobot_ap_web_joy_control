# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PicoBot web control — a Raspberry Pi Pico W running MicroPython serves a browser-based robot controller over its own Wi-Fi AP (`192.168.4.1`). The robot has four mecanum wheels and a 3-servo arm via PCA9685.

**Division of labor:**
- **Claude Code** owns the full codebase: firmware (`pico/main.py`, `pico/PicoBot/*.py`) and UI (`pico/PicoBot/www/index.html`).

Do not redesign the page layout/visual design unless explicitly asked.

## Repo Layout

```
repo/
├── pico/
│   ├── main.py                  # boot safety + entry point
│   └── PicoBot/
│       ├── app.py               # supervisor, WDT, asyncio orchestration
│       ├── config.py
│       ├── hardware_map.py
│       ├── http_server.py
│       ├── protocol_ws.py       # WebSocket frame parsing
│       ├── safety.py
│       ├── drive.py             # mecanum mixer + motor driver
│       ├── arm.py               # PCA9685 + non-blocking servo planner
│       ├── show_moves.py        # interruptible state machines
│       ├── telemetry.py
│       └── www/
│           └── index.html       # ← Claude owns this file
├── build/mpy/                   # compiled output, gitignored
├── tools/                       # developer guides (never uploaded to Pico)
├── tests/                       # desktop test scripts
└── Documents/                   # reference only, never uploaded to Pico
```

`Documents/` must never appear in `PICO_UPLOAD_MANIFEST.md` and must never be uploaded to the Pico.

## Compile and Upload

Compile Python modules to `.mpy` before upload (especially important on RP2040):

```bash
mkdir -p build/mpy/PicoBot
mpy-cross pico/PicoBot/app.py          -o build/mpy/PicoBot/app.mpy
mpy-cross pico/PicoBot/config.py       -o build/mpy/PicoBot/config.mpy
# ... repeat for each module in pico/PicoBot/
```

Upload to Pico using `mpremote` or Thonny. Only upload files listed in `PICO_UPLOAD_MANIFEST.md`:
- `/main.py`
- `/PicoBot/*.mpy` (or `.py` during debugging for readable stack traces)
- `/PicoBot/www/index.html`

Never upload: `Documents/`, `.git/`, `tools/`, `tests/`, `*.md`.

Serial debugging:

```bash
mpremote connect /dev/ttyACM0 repl
```

## WebSocket Protocol (PROTOCOL_V1.md)

The UI communicates with the robot exclusively via `ws://192.168.4.1/ws`. All frames are comma-delimited text, max 64 bytes.

**Browser → Robot:**
```
HELLO,1,picobot-ui-v2
PING,seq,timestamp_ms
ARM,seq,0|1
D,seq,f,s,r          # drive: forward(-100..100), strafe(-100..100), rotate(-100..100)
A,seq,base,arm,claw  # arm angles; -1 = no-change sentinel
M,seq,move_id,speed  # show-off move
STOP,seq
CFG,seq,key,value
```

**Robot → Browser:**
```
HELLO,1,picobot-fw-v2
PONG,seq,timestamp_ms
ACK,seq
ERR,seq,code,message
S,seq,mode,armed,f,s,r,base,arm,claw,dist_cm,uptime_ms   # 5 Hz telemetry
K,seq,event,value
SD,seq,fl,bl,fr,br,last_drive_age_ms,heap_free            # debug only
```

Key protocol rules:
- `seq` is 16-bit unsigned, for staleness rejection only (no retransmission).
- `STOP` and `ARM,0` are **always** honored regardless of seq.
- `D` frames reset the firmware motor deadman timer.
- `A`, `M`, `S`, `K`, `SD` do NOT reset the deadman.

## UI Rules

When modifying `index.html`, these rules are non-negotiable:

**Connection state:**
- Use `socket.readyState === 1` (not `onopen` flag) to check if connected.
- Show ARMED/DISARMED state visibly in the UI.
- Default DISARMED on page load and on every reconnect.

**Drive frames:**
- While a joystick is active, send `D,seq,f,s,r` at **20 Hz**.
- While the stick is touched but centered, send `D,seq,0,0,0` at minimum **5 Hz** (heartbeat to reset deadman).
- Joystick arbitration: first-touched joystick owns drive; the other is ignored until released; release sends `STOP`.

**Right joystick** sends `D,seq,f,0,r` (differential drive, no strafe).
**Left joystick** sends `D,seq,f,s,r` (full mecanum: forward, strafe, rotate).

**Safety:**
- On `document.visibilitychange` → hidden: send `STOP` then `ARM,0`.
- On WebSocket close/error: UI must show DISARMED.
- Do NOT add UI-side motor acceleration limiting — firmware owns that.

**Arm control:**
- Send `-1` as no-change for any servo axis the user hasn't touched yet.
- Do NOT send `claw=0` before the user touches the gripper control.

**Show-off moves:**
- Triggered by `M,seq,move_id,speed`.
- UI must provide a STOP button that sends `STOP,seq`.

**HTTP is only used for:**
- `GET /` — load the web page
- `GET /health` — alive check
- `GET /status` — fallback status
- `GET /api/stop` — emergency stop fallback

Old repeated `fetch()` movement commands must not exist in the final UI.

## Safety Architecture (read before any firmware work)

Motors stop and disarm on: deadman timeout (250 ms no `D` frame), WebSocket disconnect, `STOP`, `ARM,0`, joystick release, page hidden, show-off move stopped, parse failure, exception, WDT reset.

`main.py` must set all motor input pins and MOTOR_ENABLE low **before** importing any PicoBot module.

`machine.Timer` deadman runs independently of `uasyncio`. Safety must not depend solely on asyncio scheduling.

`machine.WDT` is fed only by the top-level supervisor, not worker tasks.

All before-floor safety checklist items (in `HARDWARE_MAP.md` and `TEST_LOG.md`) must pass with wheels lifted before any floor test.

## Milestones (current development order)

0. Repo and docs  
1. Hardware baseline (wheel/servo/safety pin mapping confirmed)  
2. Serve page from Pico  
3. WebSocket connection (HELLO/PING/PONG, honest connection state)  
4. **Safety gate** — ARM/DISARM, Timer deadman, WDT, parse-failure safety ← must pass before floor tests  
5. Right joystick only (lifted test first)  
6. Left mecanum joystick (lifted test first)  
7. Joystick arbitration  
8–10. Servos (base, arm, gripper)  
11. Telemetry  
12. Show-off moves (one at a time, interruptible state machines)  

Do not implement a later milestone before the safety gate (Milestone 4) is confirmed working.
