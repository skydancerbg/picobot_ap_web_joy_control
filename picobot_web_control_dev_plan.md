# PicoBot Web Control Development Plan

**File:** `picobot_web_control_dev_plan.md`  
**Version:** v2 — revised after protocol/safety critique  
**Purpose:** Repo-oriented development and bug-fixing handoff for PicoBot web control  
**Reference target:** Raspberry Pi Pico W / RP2040 running MicroPython  
**Secondary target:** Raspberry Pi Pico 2 W / RP2350, best-effort with more headroom  
**Development agents:** Codex CLI for firmware/backend, Claude Code CLI for UI  
**Important rule:** `Documents/` is a reference-only folder and must **not** be uploaded to the Pico.

---

## 0. v2 Critical Changes

This version makes the critique binding. Before any **on-the-floor** test, these are required:

1. **Drive frames are heartbeats.** While a joystick is active, the browser sends `D,seq,f,s,r` at 20 Hz. If the stick is touched but centered, it sends `D,seq,0,0,0` at minimum 5 Hz.
2. **Motors are explicitly armed.** Add `ARM,seq,0/1`. The robot boots disarmed. Every browser reconnect starts disarmed.
3. **Safety is hardware-backed.** Use a motor-enable / STBY / nSLEEP GPIO if available. Safety must not depend only on `uasyncio`.
4. **Deadman is Timer-based.** Use `machine.Timer` to disable motors if drive heartbeat is lost.
5. **WDT is required.** Enable `machine.WDT`, fed only by the top-level supervisor.
6. **Hardware map is mandatory.** Document motor-driver chip, motor-enable pin, pull-downs, servo rail power, and bulk capacitance.
7. **9 g servos need real safe ranges.** Calibrate `SAFE_MIN` and `SAFE_MAX` 5–10° inside buzz/binding zones.
8. **Runtime modules should be precompiled to `.mpy`.** Especially on RP2040, use `mpy-cross` before longer tests.
9. **Show-off moves never write PWM directly.** They only write `(f, s, r)` targets through the same safety path as joystick commands.
10. **Old HTTP GET drive commands must be removed from final control.** WebSocket replaces repeated `fetch()` movement commands.

---

## 1. Project Goal

Build a robust robot-served web control system:

- The Pico serves the advanced HTML/CSS/JavaScript controller.
- The browser connects to `ws://192.168.4.1/ws`.
- Right joystick drives like a normal differential-drive robot.
- Left joystick performs mecanum strafe, diagonal movement, and spin.
- Arm tab controls 3 hobby servos through PCA9685.
- Show-off moves are interruptible firmware state machines.
- Safety gates are verified with wheels lifted before floor tests.

The current advanced page is the **UI prototype**. The current simple firmware is a **starting point**, not the final architecture.

---

## 2. Local Folder Layout

Use one project folder:

```text
picobot-web-control-project/
├── Documents/                         # reference only, never uploaded to Pico
│   ├── picobot_web_page-v1-hand_off.md
│   ├── picobot_web_page-v1.html
│   ├── PicoBot_Electronics_Assembly_Manual_w_line_v5.docx
│   ├── picobot_plan_critique.md
│   └── future_notes/
│
└── repo/                              # Git repo starts here
    ├── .git/
    ├── .gitignore
    ├── README.md
    ├── picobot_web_control_dev_plan.md
    ├── AGENTS.md
    ├── CODEX_TASKS.md
    ├── CLAUDE_UI_TASKS.md
    ├── TEST_LOG.md
    ├── HARDWARE_MAP.md
    ├── PROTOCOL_V1.md
    ├── PICO_UPLOAD_MANIFEST.md
    ├── pico/
    │   ├── main.py
    │   └── PicoBot/
    │       ├── app.py
    │       ├── config.py
    │       ├── hardware_map.py
    │       ├── http_server.py
    │       ├── protocol_ws.py
    │       ├── safety.py
    │       ├── drive.py              # motor driver + mecanum mixer
    │       ├── arm.py                # PCA9685 + servo planner
    │       ├── show_moves.py
    │       ├── telemetry.py
    │       └── www/
    │           └── index.html
    ├── build/
    │   └── mpy/
    ├── tools/
    │   ├── compile_mpy.md
    │   ├── upload_to_pico.md
    │   ├── backup_from_pico.md
    │   ├── serial_debug.md
    │   └── manual_test_commands.md
    └── tests/
        ├── test_wheel_map.py
        ├── test_servo_channels.py
        └── test_protocol_desktop.html
```

The runtime tree is intentionally smaller than the v1 11-module tree. On RP2040, every `.py` import costs RAM, so `drive.py` combines motor output and mixer logic, and `arm.py` combines PCA9685 and servo planner logic. If more modules are kept for clarity, they must be precompiled to `.mpy` for upload.

---

## 3. `Documents/` Folder Rule

`Documents/` is only for reference files, critique files, screenshots, and notes.

It must not be uploaded to Pico. It should normally be ignored by Git:

```gitignore
Documents/
```

Even if committed later, `Documents/` must never appear in `PICO_UPLOAD_MANIFEST.md`.

---

## 4. Git Repo Setup

Preferred:

```bash
cd picobot-web-control-project
git clone https://github.com/robosteamdev/picobot-web-control.git repo
cd repo
```

Or, if the folder already exists:

```bash
cd picobot-web-control-project/repo
git init
git remote add origin https://github.com/robosteamdev/picobot-web-control.git
```

---

## 5. Pico Upload Rule

Only upload runtime files listed in `PICO_UPLOAD_MANIFEST.md`.

Preferred upload after `.mpy` compilation:

```text
/main.py
/PicoBot/app.mpy
/PicoBot/config.mpy
/PicoBot/hardware_map.mpy
/PicoBot/http_server.mpy
/PicoBot/protocol_ws.mpy
/PicoBot/safety.mpy
/PicoBot/drive.mpy
/PicoBot/arm.mpy
/PicoBot/show_moves.mpy
/PicoBot/telemetry.mpy
/PicoBot/www/index.html
```

Debugging exception: upload `.py` instead of `.mpy` only when readable stack traces are needed. Return to `.mpy` before longer RP2040 tests.

Never upload:

```text
Documents/
.git/
.github/
tools/
tests/
*.md unless intentionally served by robot
```

---

## 6. Required Repo Handoff Files

### 6.1 `AGENTS.md`

Must state:

```markdown
# AGENTS.md

- Do not upload `Documents/` to Pico.
- Only files listed in `PICO_UPLOAD_MANIFEST.md` may be uploaded.
- Prefer `.mpy` runtime upload for Pico W / RP2040 once modules stabilize.
- Preserve the existing UI design unless explicitly asked to redesign.
- Motor safety has priority over UI features.
- Emergency STOP, ARM/DISARM, hardware motor-enable, Timer deadman, and WDT must work before floor tests.
- Do not use blocking servo movements inside HTTP or WebSocket handlers.
- Show-off moves must be interruptible and must never write motor PWM directly.
- UI code must not implement motor acceleration limiting; firmware owns motor limiting.
```

### 6.2 `CODEX_TASKS.md`

Codex owns:

- MicroPython runtime.
- HTTP server.
- WebSocket server.
- `machine.Timer` deadman.
- `machine.WDT` supervisor.
- Boot-time safe motor pins.
- Hardware motor-enable GPIO.
- Mecanum mixer and motor driver.
- Servo calibration tools and servo planner.
- `.mpy` compile workflow.
- Real robot test scripts.
- Serial-log bug fixing.

Codex must not implement a safety path that relies only on `uasyncio`.

### 6.3 `CLAUDE_UI_TASKS.md`

Claude owns UI only:

- Preserve layout and visual design.
- Replace old HTTP drive endpoints with WebSocket frames.
- Use `socket.readyState === 1` for actual connection state.
- Add ARMED/DISARMED UI state.
- Default disarmed after load and reconnect.
- Send `STOP` then `ARM,0` on `document.visibilitychange` when hidden.
- Send `D,seq,f,s,r` at 20 Hz while joystick is active.
- Send `D,seq,0,0,0` at minimum 5 Hz while stick is touched but centered.
- Use `A,seq,base,arm,claw` for arm control, with `-1` as no-change sentinel.
- Do not send `claw=0` before the user touches the gripper.
- Do not add UI-side motor acceleration limiting.

### 6.4 `TEST_LOG.md`

Every test entry must include both sides when relevant:

```markdown
Date:
Firmware commit:
Web page commit:
Pico target: Pico W / Pico 2 W
Battery voltage:
Phone/browser:
Tested feature:
Expected result:
Actual result:
Pass/fail:
Browser console excerpt with timestamp:
Pico serial excerpt with timestamp:
Notes:
Next action:
```

### 6.5 `HARDWARE_MAP.md`

Must include:

```text
Pico target: Pico W or Pico 2 W
Battery and WAGO mapping
Pololu D30V30F5 wiring
Motor-driver chip name
Motor-enable / STBY / nSLEEP pin, or confirmed unavailable
Motor input pull-down strategy
A1/A2 -> front-left motor
B1/B2 -> back-left motor
C1/C2 -> front-right motor
D1/D2 -> back-right motor
GP2 -> PCA9685 SDA
GP3 -> PCA9685 SCL
PCA9685 slot 0 -> base servo
PCA9685 slot 1 -> arm servo
PCA9685 slot 2 -> gripper servo
Servo rail voltage
Servo rail bulk capacitance at PCA9685 V+
Confirmation servos are not powered from Pico 3V3 or VBUS
GP27 -> HC-SR04 Trig
GP26 -> HC-SR04 Echo
Wheel polarity test results
Mecanum roller orientation result: STRAFE_SIGN = +1 or -1
Servo SAFE_MIN / SAFE_MAX values
```

### 6.6 `PROTOCOL_V1.md`

Browser to robot:

```text
HELLO,1,picobot-ui-v2
PING,seq,timestamp_ms
ARM,seq,0
ARM,seq,1
D,seq,f,s,r
A,seq,base,arm,claw
M,seq,move_id,speed
STOP,seq
CFG,seq,key,value
```

Robot to browser:

```text
HELLO,1,picobot-fw-v2
PONG,seq,timestamp_ms
ACK,seq
ERR,seq,code,message
S,seq,mode,armed,f,s,r,base,arm,claw,dist_cm,uptime_ms
K,seq,event,value
SD,seq,fl,bl,fr,br,last_drive_age_ms,heap_free   # only when debug enabled
```

Protocol semantics:

```text
seq is a 16-bit unsigned counter.
seq is for staleness rejection only, not reliability or retransmission.
D and A frames older than or equal to last accepted seq are ignored with wraparound handling.
STOP is always honored, regardless of seq.
ARM,0 is always honored, regardless of seq.
ARM,1 may be rejected if safety checks fail.
Max frame length is 64 bytes.
Parse failure sends ERR if possible and triggers the same safety path as deadman expiry.
D frames reset the motor deadman.
A, M, S, K, and SD do not reset the motor deadman.
Drive frames are heartbeats while joystick is active.
Touched but centered stick sends D,seq,0,0,0 at minimum 5 Hz.
Normal telemetry S is 5 Hz.
Debug wheel telemetry SD is disabled unless CFG,seq,debug,1 is active.
Servo telemetry is estimated, not measured.
Binary D frames may be added later, but parsing must remain separate from frame handling.
```

### 6.7 `PICO_UPLOAD_MANIFEST.md`

Must list only runtime files. It must explicitly exclude `Documents/`, `.git/`, `tools/`, `tests/`, and docs.

---

## 7. `.gitignore`

```gitignore
Documents/
build/mpy/
*.mpy
__pycache__/
*.pyc
.mypy_cache/
.pytest_cache/
.DS_Store
Thumbs.db
.vscode/
.idea/
*.bak
*.tmp
*.old
backup_*/
_backups/
secrets.py
wifi_secrets.py
*.env
mpremote.log
serial.log
```

If `.vscode/` contains useful safe tasks, commit only those specific files.

---

## 8. `.mpy` Compile Workflow

Add `tools/compile_mpy.md`:

```markdown
# Compile MicroPython Runtime Modules to .mpy

Use an `mpy-cross` version compatible with the MicroPython firmware installed on the Pico.

From repo root:

mkdir -p build/mpy/PicoBot
mpy-cross pico/PicoBot/app.py          -o build/mpy/PicoBot/app.mpy
mpy-cross pico/PicoBot/config.py       -o build/mpy/PicoBot/config.mpy
mpy-cross pico/PicoBot/hardware_map.py -o build/mpy/PicoBot/hardware_map.mpy
mpy-cross pico/PicoBot/http_server.py  -o build/mpy/PicoBot/http_server.mpy
mpy-cross pico/PicoBot/protocol_ws.py  -o build/mpy/PicoBot/protocol_ws.mpy
mpy-cross pico/PicoBot/safety.py       -o build/mpy/PicoBot/safety.mpy
mpy-cross pico/PicoBot/drive.py        -o build/mpy/PicoBot/drive.mpy
mpy-cross pico/PicoBot/arm.py          -o build/mpy/PicoBot/arm.mpy
mpy-cross pico/PicoBot/show_moves.py   -o build/mpy/PicoBot/show_moves.mpy
mpy-cross pico/PicoBot/telemetry.py    -o build/mpy/PicoBot/telemetry.mpy

Upload `/main.py`, `/PicoBot/*.mpy`, and `/PicoBot/www/index.html` only.

During debugging, `.py` files may temporarily be uploaded for readable stack traces.
```

---

## 9. Runtime Architecture

```text
main.py
├── immediately sets motor input pins low
├── immediately sets MOTOR_ENABLE low if available
└── imports PicoBot.app only after safe pin state

PicoBot/app.py
├── starts hardware Timer deadman
├── starts WDT supervisor
├── starts Wi-Fi AP
├── starts HTTP server
├── starts WebSocket server
├── starts motor loop
├── starts servo planner loop
├── starts telemetry loop
└── keeps running under top-level supervisor
```

Browser:

```text
open http://192.168.4.1/
load UI
connect WebSocket
start DISARMED
user explicitly taps ARM
send joystick/arm/show-off frames
receive telemetry
send STOP + ARM,0 on hidden/disconnect/release/error
```

---

## 10. HTTP vs WebSocket

Use HTTP only for:

```text
GET /              -> web page
GET /health        -> alive check
GET /status        -> fallback status
GET /api/stop      -> emergency stop and disarm fallback
```

Use WebSocket for all real control.

Old repeated HTTP GET control is not acceptable for final movement because stale requests can arrive after stop, connection state is false, and errors are swallowed.

---

## 11. Safety Architecture

The firmware must stop motors and disarm when:

```text
No valid D frame arrives within DEADMAN_MS.
WebSocket disconnects.
Browser sends STOP.
Browser sends ARM,0.
Joystick is released.
Page becomes hidden.
Show-off move is stopped.
Any frame parse failure occurs.
Protocol error occurs.
Application exception occurs.
WDT reset occurs.
```

### 11.1 Mandatory before-floor safety checklist

Milestone 4 cannot pass until all are true:

```text
[ ] main.py sets motor pins low before importing app modules.
[ ] main.py sets MOTOR_ENABLE low before importing app modules.
[ ] Motor input pull-down strategy is documented/verified.
[ ] Motor-enable / STBY / nSLEEP is wired to Pico GPIO if available.
[ ] machine.Timer deadman disables motor-enable independently of asyncio.
[ ] machine.WDT is enabled, fed only by top-level supervisor.
[ ] Top-level try/except disables motors before logging.
[ ] UI sends STOP then ARM,0 on page hidden.
[ ] ARM,seq,0/1 exists; robot boots and reconnects disarmed.
[ ] Parse failure triggers same safety path as deadman expiry.
[ ] Show-off moves write only target (f,s,r), never PWM.
```

### 11.2 First lines of `main.py`

```python
from machine import Pin

MOTOR_INPUT_PINS = (...)      # confirmed in HARDWARE_MAP.md
MOTOR_ENABLE_PIN = ...        # confirmed GPIO, or None

for pin_no in MOTOR_INPUT_PINS:
    Pin(pin_no, Pin.OUT, value=0)

if MOTOR_ENABLE_PIN is not None:
    Pin(MOTOR_ENABLE_PIN, Pin.OUT, value=0)

from PicoBot.app import main
main()
```

Do not leave placeholder pins in production.

### 11.3 Timer deadman pattern

```python
from machine import Timer
import time

DEADMAN_MS = 250
last_drive_ms = time.ticks_ms()

def safety_tick(timer):
    age = time.ticks_diff(time.ticks_ms(), last_drive_ms)
    if age > DEADMAN_MS:
        hard_motor_disable()

watchdog_timer = Timer()
watchdog_timer.init(period=20, mode=Timer.PERIODIC, callback=safety_tick)
```

`hard_motor_disable()` must:

```text
set motor-enable low first
set all PWM/input values zero second
set armed = false
```

### 11.4 WDT supervisor pattern

```python
from machine import WDT
import uasyncio as asyncio

wdt = WDT(timeout=2000)

async def supervisor():
    while True:
        try:
            await app_run()
        except Exception as exc:
            hard_motor_disable()
            print('FATAL:', exc)
            await asyncio.sleep(2)

        wdt.feed()
        await asyncio.sleep_ms(100)
```

Do not feed WDT from low-level worker tasks.

---

## 12. Mecanum Mixer

Default X-pattern convention:

```text
FL = f + s + r
BL = f - s + r
FR = f - s - r
BR = f + s - r
```

Opposite roller orientation:

```text
FL = f - s + r
BL = f + s + r
FR = f + s - r
BR = f - s - r
```

Normalize after mixing and before deadband/min-start/gain correction:

```text
max_abs = max(abs(FL), abs(BL), abs(FR), abs(BR), 100)
FL = FL * 100 / max_abs
BL = BL * 100 / max_abs
FR = FR * 100 / max_abs
BR = BR * 100 / max_abs
```

Then apply in firmware:

```text
deadband
minimum-start PWM
per-wheel sign correction
per-wheel gain correction
acceleration limiting
armed/motor-enable check
```

Do not let the UI send values outside `-100..100` to compensate for normalization.

### 12.1 Roller orientation test

With wheels lifted, command `s=+50`.

Expected for X-pattern:

```text
FL forward
BL backward
FR backward
BR forward
```

If wheel pattern is correct but physical robot would strafe left instead of right, set:

```python
STRAFE_SIGN = -1
```

and retest.

---

## 13. Right Joystick

Right joystick behaves like a normal differential-drive robot:

```text
D,seq,f,0,r
```

Do not use old endpoints like `forward`, `back`, `right_forward`, etc.

Right joystick still goes through the same mecanum mixer. Do not create a separate differential motor path.

Recommended initial gain:

```python
TURN_GAIN_RIGHT_JOY = 0.6
TURN_GAIN_LEFT_JOY = 1.0
```

---

## 14. Left Joystick

Left joystick sends mecanum vectors:

```text
FWD       -> D,seq,+speed,0,0
BACK      -> D,seq,-speed,0,0
DIAG FR   -> D,seq,+speed,+speed,0
DIAG FL   -> D,seq,+speed,-speed,0
DIAG BR   -> D,seq,-speed,+speed,0
DIAG BL   -> D,seq,-speed,-speed,0
SPIN R    -> D,seq,0,0,+speed
SPIN L    -> D,seq,0,0,-speed
```

Joystick arbitration:

```text
first touched joystick owns drive
other joystick ignored until release
release sends STOP
centered but touched sends D,seq,0,0,0 at minimum 5 Hz
```

---

## 15. Arm and 9 g Servo Strategy

Browser sends target angles. Firmware stores targets. A non-blocking servo planner moves estimated current position toward targets.

Never do blocking servo loops inside a request/WebSocket handler.

Servo planner loop:

```text
every 20–50 ms:
  clamp target to SAFE_MIN/SAFE_MAX
  apply velocity limit
  apply acceleration limit
  update estimated angle
  write PCA9685 PWM
```

Initial speed limits:

```text
base servo:    60 deg/sec
arm servo:     35–45 deg/sec
gripper servo: 80–120 deg/sec
```

Servo telemetry is estimated, not measured.

### 15.1 Required SAFE_MIN / SAFE_MAX calibration

For every servo:

```text
1. Start at 90°.
2. Move downward in 5° increments.
3. Stop when buzzing/binding begins.
4. Move back 5–10° and save as SAFE_MIN.
5. Return to 90°.
6. Move upward in 5° increments.
7. Stop when buzzing/binding begins.
8. Move back 5–10° and save as SAFE_MAX.
```

Example:

```text
Buzz starts at 12° -> use SAFE_MIN = 20°.
Buzz starts at 171° -> use SAFE_MAX = 160° or 165°.
```

Use larger margins for mechanically loaded arm endpoints.

Do not increase PCA9685 servo PWM frequency above normal hobby-servo 50 Hz unless a specific servo datasheet requires it.

---

## 16. Milestones

### Milestone 0 — Repo and docs

Create repo structure and required files. Verify `Documents/` is not in upload manifest. Add `tools/compile_mpy.md`.

Pass: a new Codex/Claude session can continue from repo files alone.

### Milestone 1 — Hardware baseline

Confirm:

```text
Pico target
motor-driver chip
motor-enable pin
pull-down strategy
servo rail power and capacitance
wheel order and polarity
roller orientation and STRAFE_SIGN
PCA9685 channels
servo SAFE_MIN/SAFE_MAX
```

Pass: wheel, roller, safety hardware, and servo mapping are confirmed before control code.

### Milestone 2 — Serve page from Pico

Serve `/`, `/health`, `/status`, and `/api/stop`. Page loads from robot AP without internet. No movement yet.

### Milestone 3 — WebSocket connection only

Implement HELLO/PING/PONG, honest connection state, default disarmed on load/reconnect.

### Milestone 4 — Safety gate

Implement ARM/DISARM, Timer deadman, WDT supervisor, hard disable, parse-failure safety, UI hidden safety.

Pass: all before-floor safety checklist items pass with wheels lifted.

### Milestone 5 — Right joystick only

Right joystick sends `D,seq,f,0,r` at 20 Hz. Centered touched stick sends zero heartbeat. Test wheels lifted first, then low-speed floor only after Milestone 4 passes.

### Milestone 6 — Left mecanum joystick only

Left joystick sends `D,seq,f,s,r`. Test all sectors lifted. Verify physical strafe direction. Then low-speed floor.

### Milestone 7 — Joystick arbitration

First touched joystick owns drive. Other ignored until release. Release sends STOP.

### Milestone 8 — Base servo only

Enable base servo with calibrated safe limits and non-blocking planner. Motor STOP must still work while servo moves.

### Milestone 9 — Arm servo

Enable arm raise/lower with safe limits, velocity limit, acceleration limit, and no buzz.

### Milestone 10 — Gripper

Enable claw with safe open/close range and `-1` no-change sentinel until user touches slider.

### Milestone 11 — Telemetry

Send normal `S` telemetry at 5 Hz. Gate wheel PWM debug telemetry behind `CFG,seq,debug,1`.

### Milestone 12 — Show-off moves

Implement one at a time:

```text
show_spin
show_moonwalk
show_crab_dash
show_wiggle
show_orbit
show_rear_pivot
show_planet
show_twirl
show_figure8
show_tank_drift
```

Each move must be an interruptible state machine and may only write `(f, s, r)` targets.

---

## 17. First Practical Target

First real target:

```text
Robot serves page.
WebSocket connects.
Motor arming works.
Timer deadman works.
WDT supervisor works.
Right joystick only.
Stops on release, timeout, disconnect, parse failure, page hidden, STOP, and ARM,0.
No left joystick.
No arm.
No show-off.
```

Only after this is reliable should mecanum strafe and arm control be added.

---

## 18. Non-Negotiable Floor-Test Requirements

Before floor testing:

```text
[ ] Hardware map complete.
[ ] Motor-enable/STBY/nSLEEP controlled by Pico GPIO if available.
[ ] Pull-down strategy documented.
[ ] Boot-time motor pins forced low.
[ ] Wheel mapping verified.
[ ] Roller orientation verified.
[ ] STOP verified.
[ ] ARM,0 verified.
[ ] Timer deadman verified.
[ ] WebSocket disconnect stop/disarm verified.
[ ] Parse-failure stop/disarm verified.
[ ] WDT supervisor verified.
[ ] Joystick release STOP verified.
[ ] Page hidden STOP + ARM,0 verified.
[ ] Servo rail power checked.
[ ] Servo safe ranges calibrated.
[ ] Robot tested with wheels lifted first.
[ ] Initial floor speed low.
```

---

## 19. First Commit

```bash
git add .
git commit -m "Add PicoBot web control v2 safety-focused development plan"
git tag v0.2-plan-safety
```

---

## 20. Codex Prompt for Milestone 0

```text
You are working in the PicoBot web control repo.

Create the initial project structure for development.

Rules:
- Do not upload or copy Documents/ into the Pico runtime tree.
- Create or update AGENTS.md, CODEX_TASKS.md, CLAUDE_UI_TASKS.md, TEST_LOG.md, HARDWARE_MAP.md, PROTOCOL_V1.md, PICO_UPLOAD_MANIFEST.md, README.md, tools/compile_mpy.md.
- Use runtime modules: app.py, config.py, hardware_map.py, http_server.py, protocol_ws.py, safety.py, drive.py, arm.py, show_moves.py, telemetry.py.
- Do not implement robot movement yet.
- Do not redesign the web page.
- Add the before-floor safety checklist to README.md and TEST_LOG.md.
- Finish by printing the tree and exact next test step.
```

---

## 21. Claude Prompt for Initial UI Safety Work

```text
You are working only on the PicoBot web page UI.

Preserve the existing visual design.

Modify the page for WebSocket connection at ws://192.168.4.1/ws.

Required:
- Use socket.readyState === 1 for connected state.
- Add visible ARMED/DISARMED state.
- Default DISARMED after load and reconnect.
- Add ARM,seq,1 and ARM,seq,0 send functions.
- Add STOP send function.
- On document.visibilitychange hidden: send STOP then ARM,0.
- Disable old HTTP GET drive endpoint senders.
- Joystick code sends D frames at 20 Hz when active.
- Centered but touched joystick sends D,seq,0,0,0 at minimum 5 Hz.
- Do not redesign page.
- Do not add UI-side acceleration limiting.
- Finish with browser-only test steps.
```

---

## 22. Final Development Order

```text
repo + docs
hardware map
boot safety
motor-enable
Timer deadman
WDT supervisor
WebSocket protocol
right joystick lifted test
right joystick low-speed floor test
left joystick lifted test
left joystick low-speed floor test
servos
telemetry
show-off moves
```

Any task that tries to implement a later feature before the safety gate is complete should be rejected or rewritten.
