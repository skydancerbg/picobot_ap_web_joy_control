"""
Run on-device via: mpremote connect /dev/ttyACM0 run tests/test_servo_channels.py

Sweeps each PCA9685 servo channel one at a time so you can confirm wiring.
Robot must be powered with servo rail active. Keep hands clear.
"""
from machine import I2C, Pin
import time

SDA = 2
SCL = 3
PCA_ADDR = 0x40
CHANNELS = {0: 'base', 1: 'arm', 2: 'claw'}

PULSE_MIN_US = 500
PULSE_MAX_US = 2500
PERIOD_US = 20000


def pca_write(i2c, reg, val):
    i2c.writeto_mem(PCA_ADDR, reg, bytes([val]))


def pca_set_us(i2c, ch, pulse_us):
    ticks = round(pulse_us * 4096 / PERIOD_US)
    ticks = max(0, min(4095, ticks))
    base = 0x06 + 4 * ch
    i2c.writeto_mem(PCA_ADDR, base, bytes([0, 0, ticks & 0xFF, ticks >> 8]))


def init_pca(i2c):
    pca_write(i2c, 0x00, 0x10)        # sleep
    prescale = round(25_000_000 / (4096 * 50)) - 1
    pca_write(i2c, 0xFE, prescale)
    pca_write(i2c, 0x00, 0x00)
    time.sleep_ms(5)
    pca_write(i2c, 0x00, 0xA0)        # auto-increment


i2c = I2C(1, sda=Pin(SDA), scl=Pin(SCL), freq=400_000)
init_pca(i2c)

for ch, name in CHANNELS.items():
    print(f"\nChannel {ch} ({name}) — moving to 45°, 90°, 135°")
    for angle in (45, 90, 135, 90):
        t = angle / 180
        us = PULSE_MIN_US + t * (PULSE_MAX_US - PULSE_MIN_US)
        pca_set_us(i2c, ch, us)
        print(f"  {angle}°")
        time.sleep_ms(800)

print("\nDone. All servos returned to 90°.")
