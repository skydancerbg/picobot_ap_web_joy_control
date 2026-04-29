# Upload to Pico

## Using mpremote

```bash
# One-shot upload of the full runtime tree (after compiling .mpy)
python3 -m mpremote connect /dev/ttyACM0 \
  cp pico/main.py :main.py \
  mkdir :PicoBot \
  mkdir :PicoBot/www \
  cp build/mpy/PicoBot/__init__.mpy  :PicoBot/__init__.mpy \
  cp build/mpy/PicoBot/config.mpy    :PicoBot/config.mpy \
  cp build/mpy/PicoBot/hardware_map.mpy :PicoBot/hardware_map.mpy \
  cp build/mpy/PicoBot/safety.mpy    :PicoBot/safety.mpy \
  cp build/mpy/PicoBot/drive.mpy     :PicoBot/drive.mpy \
  cp build/mpy/PicoBot/arm.mpy       :PicoBot/arm.mpy \
  cp build/mpy/PicoBot/http_server.mpy :PicoBot/http_server.mpy \
  cp build/mpy/PicoBot/protocol_ws.mpy :PicoBot/protocol_ws.mpy \
  cp build/mpy/PicoBot/show_moves.mpy :PicoBot/show_moves.mpy \
  cp build/mpy/PicoBot/telemetry.mpy :PicoBot/telemetry.mpy \
  cp build/mpy/PicoBot/app.mpy       :PicoBot/app.mpy \
  cp pico/PicoBot/www/index.html     :PicoBot/www/index.html

# Soft reset after upload
python3 -m mpremote connect /dev/ttyACM0 reset
```

## Upload single file

```bash
python3 -m mpremote connect /dev/ttyACM0 cp pico/PicoBot/www/index.html :PicoBot/www/index.html
```

## Verify filesystem after upload

```bash
python3 -m mpremote connect /dev/ttyACM0 ls :
python3 -m mpremote connect /dev/ttyACM0 ls :PicoBot
python3 -m mpremote connect /dev/ttyACM0 ls :PicoBot/www
```

## Using Thonny

File → Open → This computer → navigate to file.  
File → Save copy → MicroPython device → set path to `:PicoBot/filename.py`.
