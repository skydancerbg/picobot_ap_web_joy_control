# hardware_map.py
#
# Source of truth: https://github.com/robosteamdev/picobot-web-control
# (tested, working on real hardware)
#
# Tag key:
#   VERIFIED_FROM_WORKING_REPO  — extracted directly from tested repo code
#   NEEDS_PHYSICAL_CONF         — not present in repo or assembly docs; requires
#                                  inspection before first use

# ══════════════════════════════════════════════════════════════════════════════
# MOTOR PCA9685 — VERIFIED_FROM_WORKING_REPO (picobot_motors.py)
# ══════════════════════════════════════════════════════════════════════════════
# All motor drive signals go through a PCA9685 on I2C bus 0.
# There are no direct GPIO motor PWM/direction pins.
#
# Three channels per motor: (pwm_ch, in1_ch, in2_ch)
#   pwm_ch : speed — pca.pwm(ch, 0, 0..4095)
#   in1_ch : direction bit 1 — 0 = LOW, 4095 = HIGH
#   in2_ch : direction bit 2
#
# Direction encoding (picobot_motors.py MotorDir, setLevel()):
#   forward  : IN1=LOW(0),     IN2=HIGH(4095), PWM=speed
#   backward : IN1=HIGH(4095), IN2=LOW(0),     PWM=speed
#   stop     : IN1=0, IN2=0, PWM=0
#
# Physical motor → firmware name (assembly manual A/B/C/D → picobot_motors.py names):
#   A1/A2 front-left  → LeftFront  → FL
#   B1/B2 back-left   → LeftBack   → BL
#   C1/C2 front-right → RightFront → FR
#   D1/D2 back-right  → RightBack  → BR

MOTOR_I2C_BUS  = 0        # VERIFIED_FROM_WORKING_REPO
MOTOR_I2C_SDA  = 20       # GP20 — VERIFIED_FROM_WORKING_REPO
MOTOR_I2C_SCL  = 21       # GP21 — VERIFIED_FROM_WORKING_REPO
MOTOR_I2C_FREQ = 100_000  # VERIFIED_FROM_WORKING_REPO
MOTOR_PCA_ADDR = 0x40     # VERIFIED_FROM_WORKING_REPO
MOTOR_PCA_FREQ = 50       # Hz — VERIFIED_FROM_WORKING_REPO

MOTOR_FL_CHS = (0,  1,  2)   # VERIFIED_FROM_WORKING_REPO (pwm, in1, in2)
MOTOR_BL_CHS = (3,  4,  5)   # VERIFIED_FROM_WORKING_REPO
MOTOR_FR_CHS = (6,  7,  8)   # VERIFIED_FROM_WORKING_REPO
MOTOR_BR_CHS = (9,  10, 11)  # VERIFIED_FROM_WORKING_REPO

# No direct GPIO motor pins — intentionally empty.
MOTOR_INPUT_PINS = ()

# ══════════════════════════════════════════════════════════════════════════════
# ARM / SERVO PCA9685 — VERIFIED_FROM_WORKING_REPO (picobot_arm.py)
# ══════════════════════════════════════════════════════════════════════════════
# Separate PCA9685 on I2C bus 1.
# picobot_arm.py: I2C(id=1, sda=Pin(2), scl=Pin(3))
# Assembly manual confirms GP2=SDA, GP3=SCL.

ARM_I2C_BUS  = 1        # VERIFIED_FROM_WORKING_REPO
ARM_I2C_SDA  = 2        # GP2 — VERIFIED_FROM_WORKING_REPO
ARM_I2C_SCL  = 3        # GP3 — VERIFIED_FROM_WORKING_REPO
ARM_I2C_FREQ = 400_000  # MicroPython I2C default; arm.py did not set freq
ARM_PCA_ADDR = 0x40     # VERIFIED_FROM_WORKING_REPO
ARM_PCA_FREQ = 50       # Hz — VERIFIED_FROM_WORKING_REPO

SERVO_BASE_CH = 0       # VERIFIED_FROM_WORKING_REPO
SERVO_ARM_CH  = 1       # VERIFIED_FROM_WORKING_REPO
SERVO_CLAW_CH = 2       # VERIFIED_FROM_WORKING_REPO

# Servo pulse range — VERIFIED_FROM_WORKING_REPO (picobot_arm.py)
# min_pulse=102 ticks, max_pulse=512 ticks at 4096 ticks / 20 ms period
# => 102/4096 × 20 000 µs ≈ 498 µs  (rounds to 500 µs at 0°)
# => 512/4096 × 20 000 µs = 2500 µs (at 180°)
SERVO_PULSE_MIN_US = 500   # VERIFIED_FROM_WORKING_REPO
SERVO_PULSE_MAX_US = 2500  # VERIFIED_FROM_WORKING_REPO

# ══════════════════════════════════════════════════════════════════════════════
# MECANUM MIXER — VERIFIED_FROM_WORKING_REPO (picobot.py)
# ══════════════════════════════════════════════════════════════════════════════
# picobot.py starf_right(): FL=fwd, BL=back, FR=back, BR=fwd
# Matches X-pattern mecanum with s=+1 → strafe right.
# => STRAFE_SIGN = +1 consistent with working repo.
# Physical strafe direction still requires a wheels-lifted confirmation
# (Milestone 1, step M1-4) to catch any motor/roller wiring difference.
STRAFE_SIGN = 1  # VERIFIED_FROM_WORKING_REPO (inferred); confirm physically M1-4

# ══════════════════════════════════════════════════════════════════════════════
# DISTANCE SENSOR — VERIFIED_FROM_WORKING_REPO + ASSEMBLY MANUAL
# ══════════════════════════════════════════════════════════════════════════════
TRIG_PIN = 27   # GP27 — HC-SR04 Trig
ECHO_PIN  = 26  # GP26 — HC-SR04 Echo

# ══════════════════════════════════════════════════════════════════════════════
# NEEDS_PHYSICAL_CONF — not in repo or assembly docs
# ══════════════════════════════════════════════════════════════════════════════

# Motor enable / STBY / nSLEEP GPIO.
# picobot_motors.py does not use any enable pin; not mentioned in docs.
# Inspect motor driver PCB: if a STBY/nSLEEP pad exists and is routed to Pico,
# set this to the GPIO number. Otherwise leave None.
MOTOR_ENABLE_PIN = None  # NEEDS_PHYSICAL_CONF

# Servo safe angle limits — VERIFIED_FROM_WORKING_REPO (picobot_main.py)
# Base: full 0–180° range (no mechanical obstruction).
# Arm and claw: restricted to 40–140° to avoid hardware damage.
# Home position: 90° for all three (centre of travel).
SERVO_BASE_MIN  =   0   # VERIFIED_FROM_WORKING_REPO
SERVO_BASE_MAX  = 180   # VERIFIED_FROM_WORKING_REPO
SERVO_BASE_HOME =  90   # VERIFIED_FROM_WORKING_REPO

SERVO_ARM_MIN   =  40   # VERIFIED_FROM_WORKING_REPO
SERVO_ARM_MAX   = 140   # VERIFIED_FROM_WORKING_REPO
SERVO_ARM_HOME  =  90   # VERIFIED_FROM_WORKING_REPO

SERVO_CLAW_MIN  =  40   # VERIFIED_FROM_WORKING_REPO
SERVO_CLAW_MAX  = 140   # VERIFIED_FROM_WORKING_REPO
SERVO_CLAW_HOME =  90   # VERIFIED_FROM_WORKING_REPO
