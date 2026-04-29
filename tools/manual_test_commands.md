# Manual Test Commands

Use `tests/test_protocol_desktop.html` in a browser for interactive WebSocket testing,
or send raw frames with a WebSocket CLI tool:

```bash
# Install wscat if needed
npm install -g wscat

# Connect
wscat -c ws://192.168.4.1/ws
```

## Protocol Test Sequence

```
# 1. Handshake
> HELLO,1,picobot-ui-v2
< HELLO,1,picobot-fw-v2

# 2. Ping
> PING,1,0
< PONG,1,0

# 3. Arm (requires safety gate)
> ARM,2,1
< ACK,2

# 4. Drive forward at 30%
> D,3,30,0,0
< (no ACK for D frames; check telemetry)

# 5. Stop
> STOP,4
< ACK,4

# 6. Disarm
> ARM,5,0
< ACK,5

# 7. Request debug telemetry
> CFG,6,debug,1
< ACK,6
```

## HTTP Endpoints

```bash
curl http://192.168.4.1/health
curl http://192.168.4.1/status
curl http://192.168.4.1/api/stop   # emergency stop fallback
```

## Servo Channel Test

Open REPL on device and run:

```bash
mpremote connect /dev/ttyACM0 run tests/test_servo_channels.py
```

## Wheel Map Test (desktop, no hardware)

```bash
python3 tests/test_wheel_map.py
```
