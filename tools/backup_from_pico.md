# Backup from Pico

## Pull all files

```bash
python3 -m mpremote connect /dev/ttyACM0 cp -r : backup_$(date +%Y%m%d)/
```

## Pull specific file

```bash
python3 -m mpremote connect /dev/ttyACM0 cp :PicoBot/config.py pico/PicoBot/config.py
```

## List Pico filesystem

```bash
python3 -m mpremote connect /dev/ttyACM0 ls :
python3 -m mpremote connect /dev/ttyACM0 ls :PicoBot
```

`backup_*/` directories are gitignored.
