# Boot safety entry point.
#
# Motor architecture: all motors are PCA9685-driven via I2C.
# There are NO direct GPIO motor PWM/direction pins on this hardware.
# MOTOR_INPUT_PINS is intentionally empty; the GPIO loop below does nothing.
#
# Boot safety for PCA9685 architecture:
#   - PCA9685 outputs are 0 on power-on reset (motors off by default).
#   - MOTOR_ENABLE_PIN (if wired) is pulled LOW here before any I2C init.
#   - If MOTOR_ENABLE_PIN is None (no dedicated enable pin), safety relies
#     on the PCA9685 reset state and the async deadman in app.py.

from machine import Pin
from PicoBot.hardware_map import MOTOR_INPUT_PINS, MOTOR_ENABLE_PIN

# Force any direct GPIO motor pins low (empty on this hardware — kept for
# forward compatibility if GPIO motor control is ever added).
for _pin_no in MOTOR_INPUT_PINS:
    Pin(_pin_no, Pin.OUT, value=0)

# Pull motor enable / STBY / nSLEEP low before starting the application.
if MOTOR_ENABLE_PIN is not None:
    Pin(MOTOR_ENABLE_PIN, Pin.OUT, value=0)

del _pin_no  # keep namespace clean

from PicoBot.app import main
main()
