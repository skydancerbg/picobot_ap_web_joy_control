# CLAUDE_UI_TASKS.md

Task list for Claude Code / UI-focused work. Tasks here concern the browser-side controller
(`pico/PicoBot/www/index.html`) and the WebSocket protocol contract between browser and firmware.

See `PROTOCOL_V1.md` for the full message specification.

---

## Status key

- `OPEN` — not started
- `IN_PROGRESS` — being worked on
- `DONE` — implemented and reviewed
- `BLOCKED` — waiting on firmware or hardware milestone

---

## Task List

### UI-01 — Connection state machine audit  `OPEN`
**File:** `pico/PicoBot/www/index.html`  
Trace all WebSocket state transitions (CONNECTING → OPEN → CLOSING → CLOSED) and verify:
- Reconnect timer fires exactly once on unexpected close.
- Status bar shows accurate connection state at every transition.
- `armed` flag is always reset to `false` on disconnect (never left true across reconnects).

---

### UI-02 — Joystick dead-zone and frame-rate tuning  `OPEN`
**File:** `pico/PicoBot/www/index.html`  
Currently the joystick emits D frames at 20 Hz while the stick is held. Verify:
- Dead-zone radius (currently hardcoded) matches `config.MOTOR_DEADBAND` in firmware.
- A single D(0,0,0) frame is always sent on joystick release before STOP.
- The 20 Hz interval is not faster than the firmware's 50 Hz motor loop (safe) but not slower
  than `DEADMAN_MS / 2` = 125 ms (required to keep deadman alive).

---

### UI-03 — Arm slider -1 sentinel correctness  `OPEN`
**File:** `pico/PicoBot/www/index.html`  
The claw slider should send `-1` until the user first touches it. Confirm this is implemented
and that subsequent moves from the default position (90°) don't silently send -1.
Also verify the base and arm sliders never send -1 once initialized.

---

### UI-04 — Page visibility / background tab handler  `OPEN`
**File:** `pico/PicoBot/www/index.html`  
Confirm that `document.addEventListener('visibilitychange', ...)` sends `STOP` then `ARM,seq,0`
when the tab is hidden. Confirm it does NOT re-arm automatically when the tab becomes visible
again (user must press ARM button).

---

### UI-05 — Emergency STOP button UX  `OPEN`
**File:** `pico/PicoBot/www/index.html`  
STOP button must be visible and tappable from all four tabs without scrolling on a 375×667
viewport (iPhone SE). Verify in browser devtools device emulation.

---

### UI-06 — Show-off move button feedback  `OPEN`
**File:** `pico/PicoBot/www/index.html`  
Each of the 10 move buttons should show a visual "active" state while the move runs and revert
to normal when the move ends or is interrupted by STOP. The firmware sends `ACK` on move start
and `ERR` on unknown move — wire these to the button state.

---

### UI-07 — Telemetry display layout  `OPEN`
**File:** `pico/PicoBot/www/index.html`  
The `S` frame fields (dist_cm, armed, uptime, mem, rssi) should each have a labeled cell in the
Info tab. Verify all five are parsed from the S frame and displayed with the correct unit label.

---

### UI-08 — PROTOCOL_V1.md sync check  `OPEN`
Compare the message types sent/received in `index.html` against `PROTOCOL_V1.md`.  
Flag any message the UI sends that is not in the protocol doc, or any protocol message the UI
does not handle (including error paths).
