# PICO_UPLOAD_MANIFEST.md

Only the files listed here may be uploaded to the Pico.

## Production Upload (compiled)

```
/main.py
/PicoBot/__init__.mpy
/PicoBot/config.mpy
/PicoBot/hardware_map.mpy
/PicoBot/safety.mpy
/PicoBot/drive.mpy
/PicoBot/arm.mpy
/PicoBot/http_server.mpy
/PicoBot/protocol_ws.mpy
/PicoBot/show_moves.mpy
/PicoBot/telemetry.mpy
/PicoBot/app.mpy
/PicoBot/www/index.html
```

## Debug Upload (readable stack traces)

Replace each `.mpy` above with the corresponding `.py` file.  
Return to `.mpy` before extended RP2040 tests.

## Explicitly Excluded — Never Upload

- `Documents/` (reference only)
- `.git/`, `.github/`
- `tools/`
- `tests/`
- `build/`
- `*.md` (unless intentionally served by the robot)
- `secrets.py`, `wifi_secrets.py`, `*.env`
