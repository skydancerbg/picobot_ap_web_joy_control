# Serial Debug

## Open REPL

```bash
python3 -m mpremote connect /dev/ttyACM0 repl
```

Or use `screen`:

```bash
screen /dev/ttyACM0 115200
```

Ctrl+A then K to exit screen.

## Stream logs without interrupting runtime

```bash
python3 -m mpremote connect /dev/ttyACM0 repl --escape-non-printable
```

Ctrl+] to exit mpremote repl.

## Soft reset from REPL

```
>>> import machine; machine.reset()
```

Or Ctrl+D in REPL for soft reset.

## Check heap

```python
>>> import gc; gc.collect(); print(gc.mem_free())
```

## Run a single test on device

```bash
python3 -m mpremote connect /dev/ttyACM0 run tests/test_wheel_map.py
```

## Monitor serial output to file

```bash
python3 -m mpremote connect /dev/ttyACM0 repl 2>&1 | tee serial.log
```

(`serial.log` is gitignored.)
