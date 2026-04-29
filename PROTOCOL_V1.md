# PROTOCOL_V1.md

WebSocket endpoint: `ws://192.168.4.1/ws`  
All frames are comma-delimited UTF-8 text. Max frame length: 64 bytes.

## Browser → Robot

| Frame | Description |
|-------|-------------|
| `HELLO,1,picobot-ui-v2` | Handshake on connect |
| `PING,seq,timestamp_ms` | Keep-alive ping |
| `ARM,seq,0` | Disarm motors (always honored) |
| `ARM,seq,1` | Arm motors (rejected if safety checks fail) |
| `D,seq,f,s,r` | Drive: forward(−100..100), strafe(−100..100), rotate(−100..100) |
| `A,seq,base,arm,claw` | Arm target angles; −1 = no-change; out-of-range values are clamped by firmware without returning a protocol error (with debug logging enabled, firmware prints requested and clamped values to serial) |
| `M,seq,move_id,speed` | Start show-off move |
| `STOP,seq` | Emergency stop (always honored) |
| `CFG,seq,key,value` | Runtime config (e.g. `CFG,1,debug,1`) |

## Robot → Browser

| Frame | Description |
|-------|-------------|
| `HELLO,1,picobot-fw-v2` | Handshake response |
| `PONG,seq,timestamp_ms` | Ping response |
| `ACK,seq` | Command acknowledged |
| `ERR,seq,code,message` | Error response |
| `S,seq,mode,armed,f,s,r,base,arm,claw,dist_cm,uptime_ms` | Telemetry at 5 Hz |
| `K,seq,event,value` | Async event notification |
| `SD,seq,fl,bl,fr,br,last_drive_age_ms,heap_free` | Debug wheel telemetry (CFG debug=1 only) |

## Sequence Numbers

- `seq` is a 16-bit unsigned counter (0–65535, wraps to 0).
- Purpose: staleness rejection only. No retransmission.
- `D` and `A` frames with `seq` ≤ last accepted `seq` are silently dropped (with wraparound handling).
- `STOP` and `ARM,0` are **always** honored regardless of `seq`.
- `ARM,1` may be rejected if safety checks fail.

## Safety Semantics

- `D` frames reset the motor deadman timer (250 ms window).
- `A`, `M`, `S`, `K`, `SD` frames do **not** reset the deadman.
- While a joystick is active, browser sends `D` at 20 Hz.
- While stick is touched but centered, browser sends `D,seq,0,0,0` at minimum 5 Hz.
- Parse failure → firmware sends `ERR` if possible, then triggers the same safety path as deadman expiry.

## Show-Off Move IDs

`spin`, `moonwalk`, `crab_dash`, `wiggle`, `orbit`, `rear_pivot`, `planet`, `twirl`, `figure8`, `tank_drift`

## Debug Config Keys

| Key | Values | Effect |
|-----|--------|--------|
| `debug` | `0`, `1` | Enable / disable SD wheel telemetry |
