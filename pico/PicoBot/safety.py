import time
from machine import Timer, Pin
from PicoBot import config

# ── shared state ──────────────────────────────────────────────────────────────
armed = False
_last_drive_ms = 0

# ── hardware refs set during init ─────────────────────────────────────────────
_enable_pin    = None    # motor-enable GPIO (Pin object or None)
_deadman_timer = None

# NOTE: motors are PCA9685-driven (I2C), so they CANNOT be zeroed inside a
# hardware Timer ISR (I2C requires the async event loop).
# The ISR handles hardware safety (enable pin) and sets armed=False.
# The async motor_loop in app.py calls zero_all() immediately when armed=False.
# If MOTOR_ENABLE_PIN is None the ISR still clears armed so motor_loop stops
# within one 20 ms tick.

# ── initialise ────────────────────────────────────────────────────────────────

def init(enable_pin_no):
    """
    Call once from app.py after drive.init().
    enable_pin_no: GPIO number or None.
    No pwm_objects needed — motors are I2C/PCA9685, not GPIO PWM.
    """
    global _enable_pin, _deadman_timer, _last_drive_ms
    _last_drive_ms = time.ticks_ms()

    if enable_pin_no is not None:
        _enable_pin = Pin(enable_pin_no, Pin.OUT, value=0)

    _deadman_timer = Timer()
    _deadman_timer.init(
        period=config.DEADMAN_TICK_MS,
        mode=Timer.PERIODIC,
        callback=_safety_tick,
    )

# ── ISR callback ──────────────────────────────────────────────────────────────

def _safety_tick(timer):
    # Hardware Timer ISR — no I2C allowed, no allocation.
    global armed
    if not armed:
        return
    age = time.ticks_diff(time.ticks_ms(), _last_drive_ms)
    if age > config.DEADMAN_MS:
        armed = False
        if _enable_pin is not None:
            _enable_pin.value(0)
        # PCA9685 motor zeroing happens in motor_loop next tick (~20 ms later).

# ── public API ────────────────────────────────────────────────────────────────

def hard_disable():
    """Full stop from async context. Sets flag and zeros motors via drive."""
    global armed
    armed = False
    if _enable_pin is not None:
        _enable_pin.value(0)
    # Caller (app.py) must call drive.zero_all() after this.
    from PicoBot import drive
    drive.zero_all()


def do_arm():
    """Arm motors and reset deadman clock."""
    global armed, _last_drive_ms
    if _enable_pin is not None:
        _enable_pin.value(1)
    _last_drive_ms = time.ticks_ms()
    armed = True


def feed_deadman():
    """Reset deadman timer. Call on every accepted D frame."""
    global _last_drive_ms
    _last_drive_ms = time.ticks_ms()


def is_armed():
    return armed
