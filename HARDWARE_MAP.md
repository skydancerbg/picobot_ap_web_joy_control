# HARDWARE_MAP.md

Source of truth: https://github.com/robosteamdev/picobot-web-control (tested, working on robot)

Tag key:  
**VERIFIED** — extracted from tested repo code or assembly manual  
**NEEDS_PHYSICAL_CONF** — not in repo or docs; requires inspection before first use

---

## Motor Control PCA9685

**VERIFIED** — `picobot_motors.py`

| Field | Value |
|-------|-------|
| I2C bus | 0 |
| SDA | GP20 |
| SCL | GP21 |
| I2C frequency | 100 kHz |
| PCA9685 address | 0x40 |
| PCA9685 PWM frequency | 50 Hz |

All motor drive signals go through this PCA9685. No direct GPIO motor pins.

### Channel Map

| Wheel | Physical label | PCA ch — PWM | PCA ch — IN1 | PCA ch — IN2 |
|-------|---------------|:---:|:---:|:---:|
| Front-Left  | A1 / A2 | 0 | 1 | 2  |
| Back-Left   | B1 / B2 | 3 | 4 | 5  |
| Front-Right | C1 / C2 | 6 | 7 | 8  |
| Back-Right  | D1 / D2 | 9 | 10 | 11 |

### Direction Encoding

| Command | IN1 | IN2 | PWM |
|---------|:---:|:---:|:---:|
| Forward  | LOW (0) | HIGH (4095) | speed |
| Backward | HIGH (4095) | LOW (0) | speed |
| Stop | 0 | 0 | 0 |

---

## Arm / Servo PCA9685

**VERIFIED** — `picobot_arm.py` + assembly manual (both agree)

| Field | Value |
|-------|-------|
| I2C bus | 1 |
| SDA | GP2 |
| SCL | GP3 |
| PCA9685 address | 0x40 |
| PCA9685 PWM frequency | 50 Hz |

### Servo Channels

| Channel | Servo | Notes |
|:-------:|-------|-------|
| 0 | Base rotation | |
| 1 | Arm raise / lower | |
| 2 | Gripper (claw) | |

### Servo Pulse Range

**VERIFIED** — computed from `picobot_arm.py` constants (`min_pulse=102`, `max_pulse=512` at 4096 ticks / 20 ms)

| Angle | Pulse width |
|------:|------------|
| 0° | 500 µs |
| 90° | 1500 µs |
| 180° | 2500 µs |

---

## Mecanum Mixer Direction

**VERIFIED** — inferred from `picobot.py` `starf_right()` (FL=fwd, BL=back, FR=back, BR=fwd matches X-pattern, s=+1)

| Parameter | Value |
|-----------|-------|
| STRAFE_SIGN | +1 |

Confirm physically during Milestone 1 step M1-4 (wheels lifted, strafe command).

---

## Distance Sensor

**VERIFIED** — assembly manual

| Signal | GPIO |
|--------|:----:|
| HC-SR04 Trig | GP27 |
| HC-SR04 Echo | GP26 |

---

## Motor Enable / STBY / nSLEEP — NEEDS_PHYSICAL_CONF

`picobot_motors.py` uses no enable pin. Not mentioned in any documentation.

Inspect the motor driver PCB:
- If a STBY / nSLEEP / EN pad is routed to a Pico GPIO, set `MOTOR_ENABLE_PIN` in `hardware_map.py`.
- If the enable input is tied permanently HIGH on the PCB, leave `MOTOR_ENABLE_PIN = None`.

Safety implication if None: the hardware Timer ISR can only clear the `armed` flag; motor PCA9685 zeroing happens in the async motor loop within one 20 ms tick (no hardware-level instantaneous cut).

---

## Motor Driver Chip — NEEDS_PHYSICAL_CONF

Not identified in any repo file or documentation. Inspect PCB silkscreen.

Common candidates for this channel layout: DRV8833, TB6612FNG, L293D.

---

## External Pull-Downs on Motor Inputs — NEEDS_PHYSICAL_CONF

`picobot_motors.py` does not configure any pull-down resistors on PCA9685 output lines. Inspect PCB for 10 kΩ pull-downs between PCA9685 outputs and GND on IN1/IN2 lines. Document in the Change Log below.

---

## Servo Rail Power — NEEDS_PHYSICAL_CONF

| Field | Value |
|-------|-------|
| Servo rail voltage | TODO — measure at PCA9685 V+ |
| Servo rail bulk capacitance | TODO — inspect PCB near PCA9685 V+ |
| Power source | TODO — must NOT be Pico 3V3 or VBUS |

---

## Servo Safe Angle Limits — VERIFIED_FROM_WORKING_REPO

Extracted from `picobot_main.py` in the reference working repository.  
These limits are enforced in both firmware (`arm.py` `set_targets()`) and UI (slider `min`/`max` attributes + JS clamp).

| Servo | SAFE_MIN | SAFE_MAX | HOME |
|-------|:--------:|:--------:|:----:|
| Base  | 0°       | 180°     | 90°  |
| Arm   | 40°      | 140°     | 90°  |
| Claw  | 40°      | 140°     | 90°  |

Constants in `hardware_map.py`: `SERVO_BASE_MIN/MAX/HOME`, `SERVO_ARM_MIN/MAX/HOME`, `SERVO_CLAW_MIN/MAX/HOME`.

---

## Change Log

| Date | Change | Source |
|------|--------|--------|
| 2026-04-29 | Full mapping extracted from working repo + assembly manual | Claude Code |
