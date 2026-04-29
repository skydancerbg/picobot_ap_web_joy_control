# TEST_LOG.md

One entry per test session. Both firmware and UI sides must be recorded when relevant.

---

## Template

```
Date:
Milestone:
Firmware commit / file hash:
Web page commit / file hash:
Pico target: Pico W / Pico 2 W
Battery voltage:
Phone / browser:
Tested feature:
Expected result:
Actual result:
Pass / fail:
Browser console excerpt (with timestamp):
Pico serial excerpt (with timestamp):
Notes:
Next action:
```

---

## Milestone 1 — Architecture Regression Confirmation

**Purpose:** The pin and channel mapping is already known from the tested working repo.  
Milestone 1 does not discover pin numbers. It confirms that the new firmware architecture  
(PCA9685-based drive.py, async app.py, WebSocket protocol) produces the same physical  
robot behavior as `picobot_motors.py` and `picobot_arm.py` on the real robot.

All steps run with **wheels lifted** unless noted. Use USB power for steps M1-1 through M1-3;  
battery is required for M1-4 onward.

Use `mpremote connect /dev/ttyACM0 repl` or upload via `tools/upload_to_pico.md`.

---

### M1-1 — Confirm both I2C buses are live

**What we already know:** motor PCA9685 at I2C0/GP20/GP21, arm PCA9685 at I2C1/GP2/GP3.  
**What this confirms:** the new firmware can reach both boards after refactoring.

```python
from machine import I2C, Pin

i2c0 = I2C(0, sda=Pin(20), scl=Pin(21), freq=100_000)
i2c1 = I2C(1, sda=Pin(2),  scl=Pin(3),  freq=400_000)

print("Motor PCA9685 (I2C0):", i2c0.scan())   # expected: [64]
print("Arm PCA9685   (I2C1):", i2c1.scan())   # expected: [64]
```

| Check | Expected | Actual | Pass? |
|-------|----------|--------|-------|
| I2C0 returns [64] | [64] | | |
| I2C1 returns [64] | [64] | | |

---

### M1-2 — Confirm motor channel mapping matches working repo

**What we already know:** LeftFront=(0,1,2), LeftBack=(3,4,5), RightFront=(6,7,8), RightBack=(9,10,11).  
**What this confirms:** each physical wheel spins in the direction the working repo predicts.

Run the new firmware's `drive.init()` and command forward at 30% on one wheel at a time.  
Compare against `picobot_motors.py` `TurnMotor('LeftFront','forward',30)` behavior.

```python
from PicoBot import hardware_map as hw
from PicoBot import drive

drive.init()

# Forward at 30% on front-left only
from machine import I2C, Pin
i2c = I2C(hw.MOTOR_I2C_BUS, sda=Pin(hw.MOTOR_I2C_SDA), scl=Pin(hw.MOTOR_I2C_SCL), freq=hw.MOTOR_I2C_FREQ)

def pca_ch(i2c, ch, on, off, addr=0x40):
    base = 0x06 + 4*ch
    i2c.writeto_mem(addr, base, bytes([on&0xFF, on>>8, off&0xFF, off>>8]))

# Front-Left forward: PWM ch0=30%, IN1 ch1=LOW, IN2 ch2=HIGH
pca_ch(i2c, 0, 0, 1229)   # 30% of 4095
pca_ch(i2c, 1, 0, 0)       # IN1 LOW
pca_ch(i2c, 2, 0, 4095)    # IN2 HIGH

import time; time.sleep(1)

# Stop
pca_ch(i2c, 0, 0, 0); pca_ch(i2c, 1, 0, 0); pca_ch(i2c, 2, 0, 0)
```

Repeat for BL (3,4,5), FR (6,7,8), BR (9,10,11).

| Motor | Working repo direction | New firmware direction | Match? |
|-------|----------------------|----------------------|--------|
| FL (ch 0,1,2) | Forward = wheel spins forward | | |
| BL (ch 3,4,5) | Forward = wheel spins forward | | |
| FR (ch 6,7,8) | Forward = wheel spins forward | | |
| BR (ch 9,10,11) | Forward = wheel spins forward | | |

---

### M1-3 — Confirm arm I2C and servo channel mapping matches working repo

**What we already know:** arm at I2C1/GP2/GP3, ch0=base, ch1=arm, ch2=claw, 500–2500 µs.  
**What this confirms:** each servo moves to the same physical position as `picobot_arm.py`.

```python
from PicoBot import arm

arm.init()                        # should print: arm: PCA9685 OK (I2C bus 1 ...)
arm.set_targets(90, 90, 90)      # all servos to 90°

import time
time.sleep(1)

arm.set_targets(45, -1, -1)      # base only to 45°
time.sleep(1)
arm.set_targets(90, -1, -1)      # back to 90°
```

| Check | Expected | Actual | Pass? |
|-------|----------|--------|-------|
| `arm.init()` prints OK | ✓ | | |
| ch0 (base) moves to 45° | base servo moves | | |
| ch1 (arm) stays at 90° | arm servo still | | |
| ch2 (claw) stays at 90° | claw servo still | | |

---

### M1-4 — Confirm mecanum strafe direction (wheels lifted, battery)

**What we already know:** working repo `starf_right()` = FL fwd, BL back, FR back, BR fwd → STRAFE_SIGN=+1.  
**What this confirms:** `drive.apply(f=0, s=50, r=0)` produces the same wheel pattern as the working repo.

```python
from PicoBot import drive, safety, hardware_map as hw

drive.init()
safety.init(hw.MOTOR_ENABLE_PIN)

safety.do_arm()
drive.apply(0, 50, 0, armed=True)   # strafe right command

import time; time.sleep(1)
drive.zero_all()
safety.hard_disable()
```

| Wheel | Expected (matches working repo) | Actual | Pass? |
|-------|--------------------------------|--------|-------|
| FL | Forward | | |
| BL | Backward | | |
| FR | Backward | | |
| BR | Forward | | |

If all four match: STRAFE_SIGN=+1 confirmed for new firmware.  
If FL/BR and BL/FR are swapped: set `STRAFE_SIGN = -1` in `hardware_map.py`.

---

### M1-5 — Calibrate servo safe ranges (new requirement for advanced UI)

**Why this is new:** `picobot_arm.py` used uncalibrated 0°–180°. The new advanced UI sends  
precise slider targets; buzzing or binding will damage servos.

Per dev plan §15.1: from 90°, step ±5° until buzzing/binding, then back 5–10°.

| Servo | Buzzes at low (°) | SAFE_MIN | Buzzes at high (°) | SAFE_MAX |
|-------|:-----------------:|:--------:|:------------------:|:--------:|
| Base  | | | | |
| Arm   | | | | |
| Claw  | | | | |

Update `SERVO_*_MIN / SERVO_*_MAX` in `hardware_map.py` when done.

---

### M1-6 — Inspect motor driver for MOTOR_ENABLE_PIN

Inspect the motor driver PCB silkscreen and datasheet:

- If a STBY / nSLEEP / EN pad is routed to a Pico GPIO: set `MOTOR_ENABLE_PIN = <pin>` in `hardware_map.py`.
- If the enable input is tied permanently HIGH on the PCB: leave `MOTOR_ENABLE_PIN = None` and document it here.

| Field | Value |
|-------|-------|
| Motor driver chip | TODO |
| Enable pin present? | TODO |
| MOTOR_ENABLE_PIN | TODO |

---

## Milestone 1 Pass Criteria

All of the following must be true before moving to Milestone 2:

- [ ] M1-1: Both I2C buses respond at address 0x40.
- [ ] M1-2: All four wheels spin in the direction the working repo predicts.
- [ ] M1-3: Each servo channel moves the correct physical servo.
- [ ] M1-4: Strafe command produces same wheel pattern as working repo; `STRAFE_SIGN` confirmed.
- [ ] M1-5: Servo safe ranges calibrated; `hardware_map.py` updated.
- [ ] M1-6: `MOTOR_ENABLE_PIN` resolved (GPIO number or confirmed None).

---

## Before-Floor Safety Checklist (complete before any Milestone 5+ floor test)

- [ ] Milestone 1 fully passed (all six steps above).
- [ ] `MOTOR_ENABLE_PIN` set or confirmed None; safety implication documented.
- [ ] `main.py` forces `MOTOR_ENABLE_PIN` low at boot — confirmed.
- [ ] `machine.Timer` deadman fires and clears `armed` — confirmed.
- [ ] `machine.WDT` enabled, fed only by top-level supervisor — confirmed.
- [ ] UI sends `STOP` then `ARM,0` on page hidden — confirmed in browser dev tools.
- [ ] `ARM,seq,0/1` works; robot boots disarmed; reconnect resets to disarmed.
- [ ] WebSocket disconnect triggers stop + disarm — confirmed.
- [ ] Parse failure triggers safety path — confirmed.
- [ ] Show-off moves write only `(f, s, r)` targets — confirmed in code review.
- [ ] Wheels lifted, low-speed full-forward test passed.

---

<!-- Add test entries below this line -->

---

## UI-RESTORE-01 — Advanced UI Regression Restoration (PENDING hardware verification)

```
Date: 2026-04-30
Milestone: UI regression fix (not a new hardware milestone)
Firmware commit: b99aacf
Web page commit: (see git log after this entry)
Pico target: Pico W / Pico 2 W
Battery voltage: N/A (UI-only change)
Phone / browser: pending
Tested feature: Advanced cyber/neon UI restored with working WebSocket controls
Expected result: Page visually matches advanced mockup; all WebSocket control logic preserved
Actual result: (pending browser + robot test)
Pass / fail: pending
Browser console excerpt (with timestamp): pending
Pico serial excerpt (with timestamp): pending
Notes: Documents/picobot_web_page-v1.html was absent (gitignored). Advanced UI
  reconstructed from task description: splash screen, cyber/neon palette, 2-tab layout
  (CONTROL / SHOW OFF), STRAFE / ARM JOY mode switch, sector joystick marks, neon glows.
  All working WebSocket logic preserved from prior index.html.
Next action: Open pico/PicoBot/www/index.html in browser and verify layout matches
  advanced mockup. Then upload to Pico and verify robot control.
```

### Browser Verification Checklist (PENDING)

| # | Check | Expected | Actual | Pass? |
|---|-------|----------|--------|-------|
| 1 | Page visually matches advanced mockup | Cyber/neon design, not plain debug page | | |
| 2 | Splash screen appears on load | PICOBOT neon logo + TAP TO ENTER | | |
| 3 | Splash dismisses on tap or after 3.5s | App becomes visible | | |
| 4 | Topbar shows PICOBOT + dot + DISARMED + STOP | All elements present | | |
| 5 | CONTROL / SHOW OFF tabs present | Two tabs, CONTROL active by default | | |
| 6 | STRAFE / ARM JOY mode switch present | Toggle buttons in left zone | | |
| 7 | Left joystick visible in STRAFE mode | Mecanum joystick with sector marks | | |
| 8 | Arm sliders visible in ARM JOY mode | BASE / ARM RAISE / CLAW sliders | | |
| 9 | Right drive joystick present | DRIVE joystick with sector marks | | |
| 10 | SHOW OFF tab: 10 move buttons + speed | Grid of move buttons visible | | |
| 11 | WebSocket connects to ws://192.168.4.1/ws | Dot turns green, label ONLINE | | |
| 12 | Right joystick sends D frames at 20 Hz | Confirmed in browser console | | |
| 13 | Left joystick sends D frames (strafe) | Confirmed in browser console | | |
| 14 | ARM JOY sliders clamp: base 0–180 | Slider min=0, max=180 | | |
| 15 | ARM JOY sliders clamp: arm 40–140 | Slider min=40, max=140 | | |
| 16 | ARM JOY sliders clamp: claw 40–140 | Slider min=40, max=140 | | |
| 17 | CENTRE ARM sends A,seq,90,90,90 | All sliders snap to 90 | | |
| 18 | Page hidden sends STOP then ARM,0 | Confirmed via visibility API | | |
| 19 | No old HTTP GET movement endpoints active | grep fetch returns no movement URLs | | |

---

## Milestones 8–10 — Servo Travel-Limit Verification (PENDING)

**Status:** Servo travel-limit implementation complete; physical verification pending.

Servo limits extracted from the tested working repo and enforced in firmware (`arm.py` `set_targets()`) and UI (slider attributes + JS clamp). This entry captures the required hardware verification steps. Fill in Actual / Pass columns during the next robot session.

```
Date:
Milestone: 8–10 (servo limit physical verification)
Firmware commit:
Web page commit:
Pico target: Pico W / Pico 2 W
Battery voltage:
Phone / browser:
Tested feature: Servo travel limits — base 0–180°, arm 40–140°, claw 40–140°
Expected result: No servo exceeds its limits; no buzzing or binding at endpoints; Centre Arm sends 90,90,90
Actual result:
Pass / fail:
Browser console excerpt (with timestamp):
Pico serial excerpt (with timestamp):
Notes:
Next action:
```

### Verification Checklist

| # | Check | Expected | Actual | Pass? |
|---|-------|----------|--------|-------|
| 1 | Tap "Centre Arm (90°)" button | Serial: `A,seq,90,90,90` sent; all sliders snap to 90 | | |
| 2 | Drag base slider to 0 and 180 | Servo reaches both ends; no buzzing | | |
| 3 | Base never commanded below 0° | Slider min=0, JS clamp confirmed in browser console | | |
| 4 | Base never commanded above 180° | Slider max=180, JS clamp confirmed | | |
| 5 | Drag arm slider to 40 and 140 | Servo reaches both ends; no buzzing or binding | | |
| 6 | Arm never commanded below 40° | Slider min=40, JS clamp + firmware clamp | | |
| 7 | Arm never commanded above 140° | Slider max=140, JS clamp + firmware clamp | | |
| 8 | Drag claw slider to 40 and 140 | Servo reaches both ends; no buzzing or binding | | |
| 9 | Claw never commanded below 40° | Slider min=40, JS clamp + firmware clamp | | |
| 10 | Claw never commanded above 140° | Slider max=140, JS clamp + firmware clamp | | |
| 11 | Send invalid frame `A,seq,999,-20,300` via browser console | Serial prints: `arm: clamp base 999.0 → 180`, `arm: clamp arm -20.0 → 40`, `arm: clamp claw 300.0 → 140` | | |
| 12 | Motor STOP still works while a servo is moving | `sendStop()` halts drive immediately | | |
| 13 | No buzzing or binding at any servo endpoint | All three servos quiet at limits | | |
