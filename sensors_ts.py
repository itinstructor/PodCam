#!/usr/bin/env python3
"""
Filename: sensors_ts.py
Description: Display temperature, pressure, and humidity
from Bosch bme680 sensor with integrated email notifications
!Connect to I2C bus
Press Ctrl+C to exit
"""
import api_key_ts
import logging
import sys
import os
import re
from datetime import datetime
from time import sleep

import requests
from bme680_ts import BME680Sensor

# Import email notification system
from email_notification import EmailNotifier

# Import configuration constants
from config import (
    SENSOR_READ_INTERVAL,
    THINGSPEAK_INTERVAL,
    READINGS_PER_CYCLE,
    ENABLE_SCHEDULED_EMAILS,
    DAILY_EMAIL_TIME,
    DEFAULT_RECIPIENT_EMAILS,
    SEND_EMAIL_ON_STARTUP,
)

# Configure logging
from logging.handlers import TimedRotatingFileHandler

# Create a module-specific logger to prevent conflicts
logger = logging.getLogger(__name__)

# Only configure if not already configured to prevent duplicates
if not logger.handlers:
    log_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s"
    )

    # Create logs directory relative to this script's location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    logs_dir = os.path.join(script_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)

    # File handler with daily rotation, keep 7 days
    log_file_path = os.path.join(logs_dir, "sensors_ts.log")
    file_handler = TimedRotatingFileHandler(
        log_file_path,
        when="midnight",
        interval=1,
        backupCount=7,
    )
    file_handler.setFormatter(log_formatter)
    # Add date before .log extension for rotated files: sensors_ts.YYYY-MM-DD.log
    file_handler.suffix = ".%Y-%m-%d.log"
    file_handler.extMatch = re.compile(r"^\.\d{4}-\d{2}-\d{2}\.log$")

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)

    # Configure logging with our handlers
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Prevent propagation to avoid duplicate messages
    logger.propagate = False

# Initialize sensor objects
sensor = BME680Sensor()

# Initialize email notification system
email_notifier = EmailNotifier()

# Substitute your api key in this file for updating your ThingSpeak channel
TS_KEY = api_key_ts.THINGSPEAK_API_KEY

# Global variables for email scheduling and water level tracking
# Track last sent date per scheduled time (keyed by 'HH:MM')
last_daily_email_dates = {}
# Track what 'next scheduled' message we've already logged to avoid spam
last_announced_next_email = None
previous_water_level = None

# Create ThingSpeak data dictionary
ts_data = {}

logger.info("PodsInSpace sensors send to ThingSpeak with email notifications")
logger.info(f"Reading sensors every {SENSOR_READ_INTERVAL} seconds")
logger.info(
    f"Averaging {READINGS_PER_CYCLE} readings over {THINGSPEAK_INTERVAL/60:.0f} minutes"
)
if ENABLE_SCHEDULED_EMAILS:
    # Display configured daily times (support string or list)
    try:
        if isinstance(DAILY_EMAIL_TIME, list):
            times_descr = ", ".join(DAILY_EMAIL_TIME)
        elif isinstance(DAILY_EMAIL_TIME, str) and "," in DAILY_EMAIL_TIME:
            times_descr = ", ".join(
                [t.strip() for t in DAILY_EMAIL_TIME.split(",")]
            )
        else:
            times_descr = str(DAILY_EMAIL_TIME)
    except Exception:
        times_descr = str(DAILY_EMAIL_TIME)

    logger.info(f"Daily summary emails at {times_descr}")
    logger.info("Water level change alerts enabled")
logger.info("Ctrl+C to exit!")


# ------------------------ CALCULATE TRIMMED MEAN -------------------------- #
def calculate_trimmed_mean(readings, trim_percent=0.1):
    """
    Calculate trimmed mean by removing outliers from the dataset.
    Removes trim_percent from both ends of the sorted data.
    Default removes 10% from each end (20% total).
    """
    if not readings:
        return 0.0

    if len(readings) == 1:
        return readings[0]

    # Sort the readings
    sorted_readings = sorted(readings)

    # Calculate number of values to trim from each end
    trim_count = max(1, int(len(sorted_readings) * trim_percent))

    # Ensure we don't trim all values
    if trim_count * 2 >= len(sorted_readings):
        trim_count = 0

    # Remove outliers from both ends
    if trim_count > 0:
        trimmed_readings = sorted_readings[trim_count:-trim_count]
    else:
        trimmed_readings = sorted_readings

    # Calculate and return the mean
    return sum(trimmed_readings) / len(trimmed_readings)


# ---------------- GET CURRENT SENSOR DATA FOR EMAIL ----------------------- #
def get_current_sensor_data_for_email(temp_f, humidity, pressure_inhg):
    """
    Format current sensor readings for email reports.

    Args:
        temp_f: Air temperature in Fahrenheit
        humidity: Humidity percentage
        pressure_inhg: Pressure in inches of mercury

    Returns:
        dict: Formatted sensor data
        str: System status
    """
    try:

        # Format sensor data
        sensor_data = {
            "Air Temperature": (
                f"{temp_f:.1f} °F" if temp_f is not None else "No data"
            ),
            "Humidity": (
                f"{humidity:.1f}%" if humidity is not None else "No data"
            ),
            "Pressure": (
                f"{pressure_inhg:.2f} inHg"
                if pressure_inhg is not None
                else "No data"
            ),
        }

        # Determine system status
        system_status = "Normal"
        return sensor_data, system_status

    except Exception as e:
        logger.error(f"Error formatting sensor data for email: {e}")
        return {
            "Air Temperature": "Error",
            "Humidity": "Error",
            "Pressure": "Error",
        }, "Critical"


def should_send_daily_email():
    """Determine if it's time to send the daily summary email.

    Rule: Do NOT catch up on missed times. Only send at the next
    upcoming configured time (for today). If all today's times are
    already past, wait until tomorrow.

    Returns a list with at most one time string when it's due now.
    """

    global last_daily_email_dates

    if not ENABLE_SCHEDULED_EMAILS:
        return []

    now = datetime.now()
    current_date = now.date()
    current_time = now.time()

    # Normalize configured times into a list of 'HH:MM' strings
    scheduled_times = []
    if isinstance(DAILY_EMAIL_TIME, list):
        scheduled_times = DAILY_EMAIL_TIME
    elif isinstance(DAILY_EMAIL_TIME, str):
        if "," in DAILY_EMAIL_TIME:
            scheduled_times = [t.strip() for t in DAILY_EMAIL_TIME.split(",") if t.strip()]
        else:
            scheduled_times = [DAILY_EMAIL_TIME.strip()]
    else:
        scheduled_times = [str(DAILY_EMAIL_TIME)]

    # Find the earliest configured time that is >= now (today's next upcoming)
    upcoming_candidates = []
    for t in scheduled_times:
        try:
            h, m = map(int, t.split(":"))
            scheduled_t = current_time.replace(hour=h, minute=m, second=0, microsecond=0)
        except Exception:
            continue

        if scheduled_t >= current_time:
            upcoming_candidates.append((t, scheduled_t))

    if not upcoming_candidates:
        # All scheduled times for today are already past; do not catch up
        # Wait until tomorrow's first time
        return []

    # Select the next upcoming (smallest time >= now)
    next_t, next_time = min(upcoming_candidates, key=lambda x: x[1])

    # If we haven't sent for this time today and we've reached/passed the time, send
    last_sent_date = last_daily_email_dates.get(next_t)
    if last_sent_date != current_date and current_time >= next_time:
        return [next_t]

    return []


def get_next_daily_email_time():
    """Compute the next scheduled time and whether it's today or tomorrow.

    Returns:
        tuple[str, str] | None: (time_str 'HH:MM', 'today'|'tomorrow') or None if misconfigured
    """
    try:
        now = datetime.now()
        current_time = now.time()

        # Normalize configured times
        if isinstance(DAILY_EMAIL_TIME, list):
            scheduled_times = DAILY_EMAIL_TIME
        elif isinstance(DAILY_EMAIL_TIME, str):
            if "," in DAILY_EMAIL_TIME:
                scheduled_times = [t.strip() for t in DAILY_EMAIL_TIME.split(",") if t.strip()]
            else:
                scheduled_times = [DAILY_EMAIL_TIME.strip()]
        else:
            scheduled_times = [str(DAILY_EMAIL_TIME)]

        # Parse all as times
        parsed = []
        for t in scheduled_times:
            try:
                h, m = map(int, t.split(":"))
            except Exception:
                continue
            parsed.append((t, current_time.replace(hour=h, minute=m, second=0, microsecond=0)))

        if not parsed:
            return None

        # Next upcoming today
        upcoming = [(t, tt) for (t, tt) in parsed if tt >= current_time]
        if upcoming:
            next_t, _ = min(upcoming, key=lambda x: x[1])
            return next_t, "today"

        # Otherwise earliest tomorrow
        next_t, _ = min(parsed, key=lambda x: x[1])
        return next_t, "tomorrow"

    except Exception:
        return None


def send_daily_summary_email(
    temp_f,
    humidity,
    pressure_inhg,
    scheduled_time=None,
):
    """Send daily summary email."""

    try:
        logger.info("📧 Sending daily summary email")

        sensor_data, system_status = get_current_sensor_data_for_email(
            temp_f,
            humidity,
            pressure_inhg,
        )

        success = email_notifier.send_status_report(
            recipient_email=None,  # Uses DEFAULT_RECIPIENT_EMAILS for multiple recipients
            sensor_data=sensor_data,
            system_status=system_status,
        )

        if success:
            # Record last sent date for this scheduled_time (or default key)
            key = scheduled_time if scheduled_time else "default"
            last_daily_email_dates[key] = datetime.now().date()
            logger.info("✅ Daily summary email sent successfully")
        else:
            logger.error("❌ Failed to send daily summary email")

    except Exception as e:
        logger.error(f"Error sending daily summary email: {e}")


def main():
    # Initialize lists to store readings for averaging
    temp_readings = []
    humidity_readings = []
    pressure_readings = []

    # Send initial reading on startup
    initial_reading_sent = False
    # Optional: send an initial status email at startup
    startup_email_sent = False

    try:
        # On startup, log next scheduled daily email time once
        if ENABLE_SCHEDULED_EMAILS:
            try:
                nxt = get_next_daily_email_time()
                if nxt:
                    t_str, when = nxt
                    logger.info(f"Next daily email scheduled for {t_str} ({when})")
            except Exception:
                pass

        while True:
            # Check for scheduled emails before sensor readings
            if ENABLE_SCHEDULED_EMAILS:
                # Get current sensor readings for email scheduling
                current_temp_f, current_humidity, current_pressure_inhg = (
                    sensor.read_sensors()
                )

                # Check for daily summary email(s)
                due = should_send_daily_email()
                if due:
                    for scheduled_time in due:
                        send_daily_summary_email(
                            current_temp_f,
                            current_humidity,
                            current_pressure_inhg,
                            scheduled_time=scheduled_time,
                        )

                    # After sending, announce the next schedule time
                    try:
                        nxt = get_next_daily_email_time()
                        if nxt:
                            t_str, when = nxt
                            logger.info(f"Next daily email scheduled for {t_str} ({when})")
                    except Exception:
                        pass
                else:
                    # Periodically announce only when it changes
                    try:
                        global last_announced_next_email
                        nxt = get_next_daily_email_time()
                        if nxt:
                            t_str, when = nxt
                            descriptor = f"{when}:{t_str}"
                            if descriptor != last_announced_next_email:
                                logger.info(f"Next daily email scheduled for {t_str} ({when})")
                                last_announced_next_email = descriptor
                    except Exception:
                        pass

            # Read BME680 sensor data using the abstracted module
            temp_f, humidity, pressure_inhg = sensor.read_sensors()

            # Check if BME680 sensor data was retrieved successfully
            if (
                temp_f is not None
                and humidity is not None
                and pressure_inhg is not None
            ):

                logger.info(
                    f"Reading {len(temp_readings)}/20: {temp_f:.1f} °F | {humidity:.1f}% | {pressure_inhg:.2f} inHg"
                )

                # Add readings to lists for averaging
                temp_readings.append(temp_f)
                humidity_readings.append(humidity)
                pressure_readings.append(pressure_inhg)

                # Send initial reading on startup
                if not initial_reading_sent:
                    logger.info("Sending initial reading to ThingSpeak")
                    thingspeak_send(
                        temp_f,
                        humidity,
                        pressure_inhg,
                    )
                    initial_reading_sent = True

                    # Optionally send a startup status email once
                    if SEND_EMAIL_ON_STARTUP and not startup_email_sent:
                        try:
                            sensor_data, system_status = get_current_sensor_data_for_email(
                                temp_f, humidity, pressure_inhg
                            )
                            if email_notifier.send_status_report(
                                recipient_email=None,
                                sensor_data=sensor_data,
                                system_status=system_status,
                                dedup_key="startup_status",
                            ):
                                logger.info("📧 Startup status email sent")
                            else:
                                logger.warning("Failed to send startup status email")
                        except Exception as e:
                            logger.error(f"Error during startup email send: {e}")
                        finally:
                            startup_email_sent = True

                # Check if we have enough readings for averaging
                if len(temp_readings) >= READINGS_PER_CYCLE:
                    # Calculate averages using trimmed mean (remove outliers)
                    avg_temp = calculate_trimmed_mean(temp_readings)
                    avg_humidity = calculate_trimmed_mean(humidity_readings)
                    avg_pressure = calculate_trimmed_mean(pressure_readings)

                    logger.info(f"Avg Temperature: {avg_temp:.1f} °F")
                    logger.info(f"Avg Humidity: {avg_humidity:.1f}%")
                    logger.info(f"Avg Pressure: {avg_pressure:.2f} inHg")

                    # Send averaged data to ThingSpeak
                    thingspeak_send(
                        avg_temp,
                        avg_humidity,
                        avg_pressure,
                    )

                    # Clear the reading lists for the next cycle
                    temp_readings.clear()
                    humidity_readings.clear()
                    pressure_readings.clear()

                # Sleep for 30 seconds before next reading
                sleep(SENSOR_READ_INTERVAL)
            else:
                logger.warning("Failed to get BME680 sensor data")
                sleep(5)  # Short sleep before retrying

    except KeyboardInterrupt:
        logger.info("Bye!")

        exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

        # Sleep before potential restart
        sleep(600)


# ---------------------------- THINGSPEAK SEND ----------------------------- #
def thingspeak_send(temp, hum, bp):
    """Update the ThingSpeak channel using the requests library"""
    logger.info("Update Thingspeak Channel")

    # Each field number corresponds to a field in ThingSpeak
    params = {
        "api_key": TS_KEY,
        "field1": temp,
        "field2": hum,
        "field3": bp,
    }

    try:
        # Update data on Thingspeak
        ts_update = requests.get(
            "https://api.thingspeak.com/update", params=params, timeout=30
        )

        # Was the update successful?
        if ts_update.status_code == requests.codes.ok:
            logger.info("Data Received!")
        else:
            logger.error("Error Code: " + str(ts_update.status_code))

        # Print ThingSpeak response to console
        # ts_update.text is the thingspeak data entry number in the channel
        logger.info(f"ThingSpeak Channel Entry: {ts_update.text}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error sending to ThingSpeak: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in thingspeak_send: {e}")


# If a standalone program, call the main function
# Else, use as a module
if __name__ == "__main__":
    logger.info("Starting sensors ThingSpeak service...")
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Program interrupted by user")

        exit(0)
    except Exception as e:
        logger.critical(f"Critical error in main: {e}")

        exit(1)
