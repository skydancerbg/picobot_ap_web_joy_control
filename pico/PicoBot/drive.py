# Motor control via PCA9685.
# All four motors are driven through I2C → PCA9685 channels.
# There are NO direct GPIO motor PWM/direction pins on this hardware.
#
# Architecture (confirmed from picobot_motors.py on GitHub):
#   Each motor = 3 PCA9685 channels: (pwm_ch, in1_ch, in2_ch)
#   Forward : pwm=speed, in1=LOW(0),     in2=HIGH(4095)
#   Backward: pwm=speed, in1=HIGH(4095), in2=LOW(0)
#   Stop    : pwm=0,     in1=0,          in2=0

from machine import I2C, Pin
from PicoBot import config
from PicoBot import hardware_map as hw

# ── PCA9685 driver (minimal, motor-specific) ──────────────────────────────────
# This is a separate instance from arm.py's PCA9685; they are different boards.

class _PCA:
    _LED0_ON_L = 0x06
    _MODE1     = 0x00
    _PRESCALE  = 0xFE

    def __init__(self, i2c, addr):
        self._i2c = i2c
        self._addr = addr
        self._w(self._MODE1, 0x00)  # clear SLEEP; arm.py PCA9685 does the same in _reset()

    def _w(self, reg, val):
        self._i2c.writeto_mem(self._addr, reg, bytes([val]))

    def _r(self, reg):
        return self._i2c.readfrom_mem(self._addr, reg, 1)[0]

    def set_freq(self, freq):
        prescale = int(25_000_000.0 / 4096.0 / freq + 0.5)
        old = self._r(self._MODE1)
        self._w(self._MODE1, (old & 0x7F) | 0x10)
        self._w(self._PRESCALE, prescale)
        self._w(self._MODE1, old)
        import time; time.sleep_ms(5)
        self._w(self._MODE1, old | 0xA0)   # RESTART + AI (auto-increment for bulk writes)

    def ch(self, channel, on, off):
        base = self._LED0_ON_L + 4 * channel
        self._i2c.writeto_mem(self._addr, base,
                              bytes([on & 0xFF, on >> 8, off & 0xFF, off >> 8]))


# ── PCA motor object ──────────────────────────────────────────────────────────

class _Motor:
    __slots__ = ('_pca', '_pwm', '_in1', '_in2', '_sim')

    def __init__(self, pca, pwm_ch, in1_ch, in2_ch):
        self._pca = pca
        self._pwm = pwm_ch
        self._in1 = in1_ch
        self._in2 = in2_ch
        self._sim = (pca is None)

    def set(self, pct):
        """pct: −100..100. Values within DEADBAND are treated as 0."""
        if self._sim:
            return
        duty = _pct_to_duty(pct)
        if pct > 0:
            self._pca.ch(self._pwm, 0, duty)
            self._pca.ch(self._in1, 0, 0)       # IN1 LOW
            self._pca.ch(self._in2, 0, 4095)    # IN2 HIGH  → forward
        elif pct < 0:
            self._pca.ch(self._pwm, 0, duty)
            self._pca.ch(self._in1, 0, 4095)    # IN1 HIGH
            self._pca.ch(self._in2, 0, 0)       # IN2 LOW   → backward
        else:
            self.zero()

    def zero(self):
        if not self._sim:
            self._pca.ch(self._pwm, 0, 0)
            self._pca.ch(self._in1, 0, 0)
            self._pca.ch(self._in2, 0, 0)


def _pct_to_duty(pct):
    mag = abs(pct)
    if mag < config.MOTOR_DEADBAND:
        return 0
    scaled = (mag - config.MOTOR_DEADBAND) / (100 - config.MOTOR_DEADBAND)
    out = config.MOTOR_MIN_START + scaled * (100 - config.MOTOR_MIN_START)
    return int(out * 40.95)   # 100% → 4095


# ── initialise ────────────────────────────────────────────────────────────────

_pca = None
_fl = _bl = _fr = _br = None
_out_fl = _out_bl = _out_fr = _out_br = 0
_drive_ok = False
_drive_init_error = ''


def is_ok():
    return _drive_ok


def init():
    global _pca, _fl, _bl, _fr, _br, _drive_ok, _drive_init_error

    _drive_ok = False
    _drive_init_error = ''

    if hw.MOTOR_I2C_BUS is None:
        _drive_init_error = 'MOTOR_I2C_BUS is None'
        print("drive: sim mode —", _drive_init_error)
        _pca = None
    else:
        try:
            i2c = I2C(hw.MOTOR_I2C_BUS,
                      sda=Pin(hw.MOTOR_I2C_SDA),
                      scl=Pin(hw.MOTOR_I2C_SCL),
                      freq=hw.MOTOR_I2C_FREQ)
            _pca = _PCA(i2c, hw.MOTOR_PCA_ADDR)
            _pca.set_freq(hw.MOTOR_PCA_FREQ)
            _drive_ok = True
            print("drive: motor PCA9685 OK")
        except Exception as e:
            _drive_init_error = str(e)
            print("drive: motor PCA9685 init failed:", e)
            _pca = None

    _fl = _Motor(_pca, *hw.MOTOR_FL_CHS)
    _bl = _Motor(_pca, *hw.MOTOR_BL_CHS)
    _fr = _Motor(_pca, *hw.MOTOR_FR_CHS)
    _br = _Motor(_pca, *hw.MOTOR_BR_CHS)


def get_wheel_outputs():
    return (_out_fl, _out_bl, _out_fr, _out_br)


# ── mecanum mixer ─────────────────────────────────────────────────────────────

def _mix(f, s, r):
    """X-pattern mecanum. Returns (fl, bl, fr, br) in −100..100."""
    s = s * hw.STRAFE_SIGN
    fl = f + s + r
    bl = f - s + r
    fr = f - s - r
    br = f + s - r
    mx = max(abs(fl), abs(bl), abs(fr), abs(br), 100)
    return fl * 100 / mx, bl * 100 / mx, fr * 100 / mx, br * 100 / mx


# ── public API ────────────────────────────────────────────────────────────────

def apply(f, s, r, armed):
    global _out_fl, _out_bl, _out_fr, _out_br
    if not armed:
        zero_all()
        return
    f = max(-100, min(100, f))
    s = max(-100, min(100, s))
    r = max(-100, min(100, r))
    fl, bl, fr, br = _mix(f, s, r)
    _out_fl, _out_bl, _out_fr, _out_br = fl, bl, fr, br
    _fl.set(fl)
    _bl.set(bl)
    _fr.set(fr)
    _br.set(br)


def zero_all():
    """Stop all motors. Called from async context (PCA9685 needs I2C, not ISR-safe)."""
    global _out_fl, _out_bl, _out_fr, _out_br
    _out_fl = _out_bl = _out_fr = _out_br = 0
    if _fl: _fl.zero()
    if _bl: _bl.zero()
    if _fr: _fr.zero()
    if _br: _br.zero()
