import time
from machine import I2C, Pin
from PicoBot import config
from PicoBot import hardware_map as hw

# ── PCA9685 driver ────────────────────────────────────────────────────────────

_MODE1    = 0x00
_PRESCALE = 0xFE
_LED0_ON_L = 0x06


class PCA9685:
    def __init__(self, i2c, addr=0x40):
        self._i2c = i2c
        self._addr = addr
        self._reset()

    def _write(self, reg, val):
        self._i2c.writeto_mem(self._addr, reg, bytes([val]))

    def _read(self, reg):
        return self._i2c.readfrom_mem(self._addr, reg, 1)[0]

    def _reset(self):
        self._write(_MODE1, 0x00)

    def set_freq(self, freq_hz):
        prescale = round(25_000_000 / (4096 * freq_hz)) - 1
        old = self._read(_MODE1)
        self._write(_MODE1, (old & 0x7F) | 0x10)   # sleep
        self._write(_PRESCALE, prescale)
        self._write(_MODE1, old)
        time.sleep_ms(5)
        self._write(_MODE1, old | 0xA0)             # auto-increment + restart

    def set_pwm(self, channel, on, off):
        base = _LED0_ON_L + 4 * channel
        self._i2c.writeto_mem(
            self._addr, base,
            bytes([on & 0xFF, on >> 8, off & 0xFF, off >> 8])
        )

    def set_us(self, channel, pulse_us, period_us=20000):
        """Set a servo pulse width in microseconds."""
        ticks = round(pulse_us * 4096 / period_us)
        ticks = max(0, min(4095, ticks))
        self.set_pwm(channel, 0, ticks)


# ── angle → pulse conversion ──────────────────────────────────────────────────

def _angle_to_us(angle_deg):
    t = angle_deg / 180.0
    return hw.SERVO_PULSE_MIN_US + t * (hw.SERVO_PULSE_MAX_US - hw.SERVO_PULSE_MIN_US)


# ── servo planner state ───────────────────────────────────────────────────────

_pca = None

_cur_base = float(hw.SERVO_BASE_HOME)
_cur_arm  = float(hw.SERVO_ARM_HOME)
_cur_claw = float(hw.SERVO_CLAW_HOME)

_tgt_base = float(hw.SERVO_BASE_HOME)
_tgt_arm  = float(hw.SERVO_ARM_HOME)
_tgt_claw = None   # None until first A frame with real claw value

_last_tick_ms = 0

# Per-servo config pulled entirely from hardware_map to avoid duplication.
# Populated in init() after hw constants are confirmed.
_SERVO_CFG = {}


def init():
    """Initialise I2C, arm PCA9685, and move all servos to 90° home."""
    global _pca, _last_tick_ms, _cur_base, _cur_arm, _cur_claw, _SERVO_CFG

    _SERVO_CFG = {
        'base': (hw.SERVO_BASE_CH, hw.SERVO_BASE_MIN, hw.SERVO_BASE_MAX, config.SERVO_BASE_SPEED),
        'arm':  (hw.SERVO_ARM_CH,  hw.SERVO_ARM_MIN,  hw.SERVO_ARM_MAX,  config.SERVO_ARM_SPEED),
        'claw': (hw.SERVO_CLAW_CH, hw.SERVO_CLAW_MIN, hw.SERVO_CLAW_MAX, config.SERVO_CLAW_SPEED),
    }

    try:
        i2c = I2C(hw.ARM_I2C_BUS,
                  sda=Pin(hw.ARM_I2C_SDA),
                  scl=Pin(hw.ARM_I2C_SCL),
                  freq=hw.ARM_I2C_FREQ)
        _pca = PCA9685(i2c, hw.ARM_PCA_ADDR)
        _pca.set_freq(hw.ARM_PCA_FREQ)
        homes = {
            'base': hw.SERVO_BASE_HOME,
            'arm':  hw.SERVO_ARM_HOME,
            'claw': hw.SERVO_CLAW_HOME,
        }
        for name, (ch, mn, mx, _) in _SERVO_CFG.items():
            home = max(mn, min(mx, homes[name]))
            _pca.set_us(ch, _angle_to_us(home))
        _cur_base = float(hw.SERVO_BASE_HOME)
        _cur_arm  = float(hw.SERVO_ARM_HOME)
        _cur_claw = float(hw.SERVO_CLAW_HOME)
        _last_tick_ms = time.ticks_ms()
        print("arm: PCA9685 OK (I2C bus", hw.ARM_I2C_BUS, "SDA=GP", hw.ARM_I2C_SDA, "SCL=GP", hw.ARM_I2C_SCL, ")")
    except Exception as e:
        print("arm: PCA9685 init failed:", e)
        _pca = None


def _clamp(val, mn, mx, name):
    v = float(val)
    c = max(mn, min(mx, v))
    if c != v:
        print("arm: clamp", name, v, "→", c)
    return c


def set_targets(base, arm_angle, claw):
    """Update servo targets from an A frame. -1 = no-change. Values clamped to safe limits."""
    global _tgt_base, _tgt_arm, _tgt_claw
    if base != -1:
        _tgt_base = _clamp(base, hw.SERVO_BASE_MIN, hw.SERVO_BASE_MAX, 'base')
    if arm_angle != -1:
        _tgt_arm = _clamp(arm_angle, hw.SERVO_ARM_MIN, hw.SERVO_ARM_MAX, 'arm')
    if claw != -1:
        _tgt_claw = _clamp(claw, hw.SERVO_CLAW_MIN, hw.SERVO_CLAW_MAX, 'claw')


def get_positions():
    return (_cur_base, _cur_arm, _cur_claw if _cur_claw is not None else 90.0)


def tick():
    """Non-blocking servo planner step. Call every SERVO_TICK_MS."""
    global _cur_base, _cur_arm, _cur_claw, _last_tick_ms
    if _pca is None:
        return

    now = time.ticks_ms()
    dt = time.ticks_diff(now, _last_tick_ms) / 1000.0
    _last_tick_ms = now

    def _step(cur, tgt, speed, ch, mn, mx):
        if tgt is None:
            return cur
        tgt = max(mn, min(mx, tgt))
        delta = tgt - cur
        max_step = speed * dt
        new = tgt if abs(delta) <= max_step else cur + max_step * (1 if delta > 0 else -1)
        _pca.set_us(ch, _angle_to_us(new))
        return new

    ch_b, mn_b, mx_b, sp_b = _SERVO_CFG['base']
    ch_a, mn_a, mx_a, sp_a = _SERVO_CFG['arm']
    ch_c, mn_c, mx_c, sp_c = _SERVO_CFG['claw']

    _cur_base = _step(_cur_base, _tgt_base, sp_b, ch_b, mn_b, mx_b)
    _cur_arm  = _step(_cur_arm,  _tgt_arm,  sp_a, ch_a, mn_a, mx_a)
    _cur_claw = _step(
        _cur_claw if _cur_claw is not None else 90.0,
        _tgt_claw, sp_c, ch_c, mn_c, mx_c
    )
