"""
Configuration file for the PodsInSpace Monitoring System
Centralizes all configurable parameters for easy maintenance
"""

# Sensor Reading Configuration
SENSOR_READ_INTERVAL = 30  # seconds between sensor readings
THINGSPEAK_INTERVAL = 600  # seconds between ThingSpeak updates (10 minutes)

# Calculated values based on intervals
READINGS_PER_CYCLE = THINGSPEAK_INTERVAL // SENSOR_READ_INTERVAL  # 20 readings

# Email Configuration
ENABLE_SCHEDULED_EMAILS = True
DAILY_EMAIL_TIME = "06:00,18:00"  # HH:MM format for daily status email
SEND_EMAIL_ON_STARTUP = True  # Send one status email at service startup

# Email SMTP Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587  # TLS port for Gmail
EMAIL_TIMEOUT = 30  # Connection timeout in seconds

# Default email settings (can be overridden)
DEFAULT_SENDER_EMAIL = "wnccrobotics@gmail.com"
DEFAULT_SENDER_PASSWORD = (
    "loyqlzkxisojeqsr"  # Use App Password, not regular password
)

# Multiple recipients - add more email addresses here
DEFAULT_RECIPIENT_EMAILS = [
    "williamaloring@gmail.com",
    "williamloring@hotmail.com",
    "sarah.trook31@gmail.com",
]

# Email template constants
SUBJECT_PREFIX = "PodsInSpace "
DEFAULT_SUBJECT = f"{SUBJECT_PREFIX} System Notification"

# Data Processing Configuration
TRIM_PERCENT = 0.1  # Percentage to trim from each end for outlier removal (10%)

HUMIDITY_MIN = 40.0  # Percentage
HUMIDITY_MAX = 80.0  # Percentage

# System Configuration
LOG_BACKUP_COUNT = 7  # Number of log files to keep
LOG_ROTATION = "midnight"  # When to rotate logs

# Network Configuration
THINGSPEAK_TIMEOUT = 30  # seconds
RETRY_DELAY = 5  # seconds to wait before retrying failed operations
RESTART_DELAY = (
    600  # seconds to wait before system restart after critical error
)

# Camera Overlay Configuration
ENABLE_LABEL_OVERLAY = True  # Set to False to completely disable label feature
LABEL_TEXT = (
    "WNCC STEM Club Meeting Thursday at 4 PM in C1"  # Text to display on video
)
LABEL_CYCLE_MINUTES = 10  # Show label every X minutes
LABEL_DURATION_SECONDS = 30  # Show label for X seconds each cycle
LABEL_FONT_SCALE = 0.8  # Size of the label text
LABEL_TRANSPARENCY = (
    0.7  # Background transparency (0.0 = transparent, 1.0 = opaque)
)
TEXT_TRANSPARENCY = 0.9  # Text transparency for overlays (0.0 = fully transparent, 1.0 = fully opaque)
TEXT_COLOR = (0, 85, 204)  # Text color for overlays (BGR format - burnt orange)

# ------------------------ WEBSTREAM CONFIGURATION ------------------------- #
# These constants (values that don't change) control how the camera behaves.
# You can change these to adjust the video quality and frame rate.

# Fish Tank Camera (Camera 0) Frame Rate Settings
CAMERA_FRAME_RATE = (
    20.0  # How many pictures per second we want the fish camera to take
)

# Note: Some cameras may ignore frame rate settings and use their own preferred rate.
# This is normal hardware behavior - the camera will tell us what it's actually using.

# Pod (Camera 0) Resolution
CAMERA_WIDTH = 1920
CAMERA_HEIGHT = 1080

# JPEG compression quality (0-100, higher = better quality but more bandwidth)
JPEG_QUALITY = 85  # Good balance between quality and bandwidth

# Skip camera detection if you know your camera index (faster startup)
# Set to 0, 1, 2, etc. if you know your camera index, or None to auto-detect
KNOWN_CAMERA_INDEX = 0

# Note: Overlay configuration is now imported from PodsInSpace_config.py

# ---------------------- DAY/NIGHT CONFIG (software only) ----------------- #
# Enable automatic day/night switching based on frame brightness
ENABLE_DAY_NIGHT = True  # Set True to enable
# Hysteresis thresholds on normalized luma (0.0-1.0). Use NIGHT < DAY.
NIGHT_LUMA_THRESHOLD = 0.25
DAY_LUMA_THRESHOLD = 0.35
# How often (seconds) to sample brightness to consider switching
LUMA_SAMPLE_EVERY_SEC = 5.0
