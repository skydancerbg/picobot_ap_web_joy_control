# CODEX_TASKS.md

Task list for Codex / automated coding agents. Each task is self-contained and does not require
robot hardware access. All tasks operate on local files only.

---

## Status key

- `OPEN` — not started
- `IN_PROGRESS` — being worked on
- `DONE` — merged or confirmed working
- `BLOCKED` — waiting for physical hardware confirmation

---

## Task List

### COD-01 — Desktop unit tests for mecanum mixer  `DONE`
**File:** `tests/test_wheel_map.py`  
All 8 directional cases verified. Run with: `python3 tests/test_wheel_map.py`

---

### COD-02 — Validate WebSocket frame parser against RFC 6455 vectors  `OPEN`
**File:** `pico/PicoBot/protocol_ws.py`  
Write a desktop test (`tests/test_protocol_ws.py`) that feeds raw bytes from RFC 6455 §5.7
example frames into `recv_frame()` and checks opcode + payload. No hardware needed — stub
the `asyncio.StreamReader` with a `BytesIO`-backed shim.

---

### COD-03 — Validate arm servo planner step function  `OPEN`
**File:** `pico/PicoBot/arm.py` — `_step()` inner function in `tick()`  
Extract `_step` logic into a pure function. Write `tests/test_arm_planner.py` that:
- Verifies convergence within the expected number of ticks at configured speed.
- Verifies SAFE_MIN / SAFE_MAX clamping.
- Verifies the `-1` sentinel leaves position unchanged.

---

### COD-04 — Show-off move smoke test  `OPEN`
**File:** `pico/PicoBot/show_moves.py`  
Write `tests/test_show_moves.py` that stubs `asyncio.sleep_ms` and `_set_drive_fn`, runs each
move for a fixed number of ticks, and asserts all `(f, s, r)` values stay in `[-100, 100]`.
No negative motor values that exceed the hardware range are allowed.

---

### COD-05 — Static type / syntax check for all firmware modules  `OPEN`
Run `python3 -m py_compile` on every `.py` file under `pico/` to catch syntax errors before
upload. Add a `tools/syntax_check.sh` script that does this and exits non-zero on any failure.

---

### COD-06 — Distance sensor timeout guard review  `OPEN`
**File:** `pico/PicoBot/app.py` — `_distance_loop()`  
Verify that both the echo-wait-HIGH and echo-wait-LOW timeouts can actually interrupt in the
async loop. Document (in a code comment) the maximum blocking time and confirm it is well below
the WDT timeout.

---

### COD-07 — Sequence number rollover test  `OPEN`
**File:** `pico/PicoBot/app.py` — `_seq_newer()`  
Write `tests/test_seq_newer.py` verifying: normal increment, wraparound at 0xFFFF→0,
duplicate rejection, and the 32767-window boundary.
