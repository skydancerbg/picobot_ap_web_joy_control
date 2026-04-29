# Compile MicroPython Modules to .mpy

Use an `mpy-cross` version that matches the MicroPython firmware on the Pico.

```bash
# From repo root
mkdir -p build/mpy/PicoBot

mpy-cross pico/PicoBot/__init__.py    -o build/mpy/PicoBot/__init__.mpy
mpy-cross pico/PicoBot/config.py      -o build/mpy/PicoBot/config.mpy
mpy-cross pico/PicoBot/hardware_map.py -o build/mpy/PicoBot/hardware_map.mpy
mpy-cross pico/PicoBot/safety.py      -o build/mpy/PicoBot/safety.mpy
mpy-cross pico/PicoBot/drive.py       -o build/mpy/PicoBot/drive.mpy
mpy-cross pico/PicoBot/arm.py         -o build/mpy/PicoBot/arm.mpy
mpy-cross pico/PicoBot/http_server.py -o build/mpy/PicoBot/http_server.mpy
mpy-cross pico/PicoBot/protocol_ws.py -o build/mpy/PicoBot/protocol_ws.mpy
mpy-cross pico/PicoBot/show_moves.py  -o build/mpy/PicoBot/show_moves.mpy
mpy-cross pico/PicoBot/telemetry.py   -o build/mpy/PicoBot/telemetry.mpy
mpy-cross pico/PicoBot/app.py         -o build/mpy/PicoBot/app.mpy
```

Then upload `build/mpy/PicoBot/*.mpy`, `pico/main.py`, and `pico/PicoBot/www/index.html`.

During debugging, skip the compile step and upload `.py` files directly for readable tracebacks.
Return to `.mpy` before any extended RP2040 test run.
