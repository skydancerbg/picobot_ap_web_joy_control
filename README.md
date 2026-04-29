# PicoBot Web Control

Raspberry Pi Pico W robot controller. The Pico serves an HTML/JS UI over its own Wi-Fi AP. The browser controls the robot exclusively via WebSocket.

## Hardware

- Pico W (RP2040) or Pico 2 W (RP2350) — connected via usbip at `/dev/ttyACM0`
- Mecanum-wheel chassis, 4 motors via PCA9685 PWM controller (I2C0: GP20=SDA, GP21=SCL)
  - Channels 0–11: four motors × 3 channels each (PWM, IN1, IN2)
- PCA9685 arm/servo controller (I2C1: GP2=SDA, GP3=SCL)
  - Ch 0: base servo, Ch 1: arm servo, Ch 2: gripper servo
- HC-SR04 distance sensor (GP27=Trig, GP26=Echo)
- See `HARDWARE_MAP.md` for the full verified pin and channel map

## Quick Start

1. Connect Pico via usbip: device appears at `/dev/ttyACM0`.
2. Verify servo travel limits on the robot (see `TEST_LOG.md` Milestones 8–10 pending entry). Default limits from working repo: base 0–180°, arm 40–140°, claw 40–140°. Update `hardware_map.py` if physical testing reveals tighter constraints.
3. Compile to `.mpy` (see `tools/compile_mpy.md`) — skip for debug uploads.
4. Upload files listed in `PICO_UPLOAD_MANIFEST.md` using `tools/upload_to_pico.md`.
5. Connect phone to `PicoBot` Wi-Fi, open `http://192.168.4.1/`.

## Development Order

See `picobot_web_control_dev_plan.md` § 22 for the full milestone sequence.  
**Do not floor-test until all items in the safety checklist below are verified with wheels lifted.**

## Before-Floor Safety Checklist

- [ ] `HARDWARE_MAP.md` is complete with actual pin numbers.
- [ ] Motor-enable / STBY / nSLEEP pin is wired and documented.
- [ ] Pull-down strategy is documented and verified.
- [ ] `main.py` forces motor pins low before importing any module — confirmed.
- [ ] `machine.Timer` deadman disables motors independently of asyncio — confirmed.
- [ ] `machine.WDT` is enabled and fed only by top-level supervisor — confirmed.
- [ ] Top-level `try/except` calls `hard_disable()` before logging — confirmed.
- [ ] ARM/DISARM works: robot boots disarmed, reconnect resets to disarmed.
- [ ] STOP command stops motors immediately — confirmed.
- [ ] `ARM,0` command stops and disarms immediately — confirmed.
- [ ] WebSocket disconnect triggers stop + disarm — confirmed.
- [ ] Parse-failure triggers same safety path as deadman — confirmed.
- [ ] Page hidden sends `STOP` then `ARM,0` — confirmed.
- [ ] Joystick release sends zero-heartbeat then STOP on lift — confirmed.
- [ ] Servo rail power confirmed (not from Pico 3V3 or VBUS).
- [ ] Servo travel limits physically verified: base 0–180°, arm 40–140°, claw 40–140° (implementation complete; physical verification pending — see `TEST_LOG.md`).
- [ ] Wheels lifted, low-speed motor test passed.

## Files Never Uploaded to Pico

`Documents/`, `.git/`, `tools/`, `tests/`, `*.md`, `build/`
