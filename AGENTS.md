# AGENTS.md

## Device Connection

- Pico is connected via usbip and appears at `/dev/ttyACM0`.
- All mpremote commands use the full invocation: `python3 -m mpremote connect /dev/ttyACM0 ...`
- Check `/dev/ttyACM0` exists before running any mpremote command; if absent, the usbip connection may need to be re-established by the user.
- Never run interactive REPL commands (`repl`) without the user's explicit request — it blocks the terminal.

## Coding Rules for all coding agents working in this repo:

- Do not upload `Documents/` to the Pico. Ever.
- Only files listed in `PICO_UPLOAD_MANIFEST.md` may be uploaded.
- Prefer `.mpy` runtime upload for Pico W / RP2040 once modules stabilize.
- Preserve the existing UI design unless explicitly asked to redesign.
- Motor safety has absolute priority over UI features or new functionality.
- Emergency STOP, ARM/DISARM, hardware motor-enable, Timer deadman, and WDT must all work before any floor test.
- Do not use blocking servo movements inside HTTP or WebSocket handlers.
- Show-off moves must be interruptible state machines and must never write motor PWM directly — only set `(f, s, r)` targets.
- UI code must not implement motor acceleration limiting; firmware owns that.
- Do not implement a later milestone before the Milestone 4 safety gate is confirmed working.
- `HARDWARE_MAP.md` must be complete and verified before any motor or servo code is tested on hardware.
- Safety must not depend only on `uasyncio`. Use `machine.Timer` for the deadman.
