# Wi-Fi AP
WIFI_SSID = "PicoBot"
WIFI_PASSWORD = "picobot123"
WIFI_CHANNEL = 6

# Safety
DEADMAN_MS = 2000         # ms without D frame before motors cut (250 for production; 2000 for testing)
DEADMAN_TICK_MS = 20      # Timer period for deadman check
ENABLE_WDT = False        # set True only after all loops confirmed WDT-safe
WDT_TIMEOUT_MS = 8000     # WDT timeout (ms) — generous for debugging

# Telemetry
TELEMETRY_INTERVAL_MS = 200   # 5 Hz

# Drive gains
TURN_GAIN_RIGHT = 0.6     # right joystick rotation gain
TURN_GAIN_LEFT = 1.0      # left joystick gain
STRAFE_SIGN = 1           # set to -1 if strafe direction is reversed after roller test

# Motor deadband and min-start (percent, 0–100)
MOTOR_DEADBAND = 5
MOTOR_MIN_START = 20

# Motor PWM frequency (Hz)
MOTOR_PWM_FREQ = 20000

# PCA9685
PCA9685_ADDR = 0x40
PCA9685_FREQ = 50         # Hz — do not raise above 50 for standard hobby servos

# Servo channels
SERVO_BASE_CH = 0
SERVO_ARM_CH = 1
SERVO_CLAW_CH = 2

# Servo pulse width range (µs) — adjust if your servos use different ranges
SERVO_PULSE_MIN_US = 500
SERVO_PULSE_MAX_US = 2500

# Servo safe angle limits (degrees) — calibrate per HARDWARE_MAP.md § Servo Safe Ranges
SERVO_BASE_MIN = 20
SERVO_BASE_MAX = 160
SERVO_ARM_MIN = 20
SERVO_ARM_MAX = 160
SERVO_CLAW_MIN = 20
SERVO_CLAW_MAX = 160

# Servo speed limits (degrees/sec)
SERVO_BASE_SPEED = 60
SERVO_ARM_SPEED = 40
SERVO_CLAW_SPEED = 100

# Servo planner tick (ms)
SERVO_TICK_MS = 25        # 40 Hz planner

# Distance sensor
TRIG_PIN = 27
ECHO_PIN = 26
DIST_INTERVAL_MS = 100    # 10 Hz measurement
DIST_MAX_CM = 400
