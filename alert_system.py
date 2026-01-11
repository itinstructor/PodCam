#!/usr/bin/env python3
"""
Filename: alert_system.py
Description: Modular alert system for sensor readings
Handles temperature, CO2, humidity, and moisture alerts
Easy to extend with new alert types
"""

from logging_config import setup_sensor_logger
from alerts_config import (
    TEMP_ALERT_HIGH,
    TEMP_ALERT_LOW,
    TEMP_ALERT_ENABLED,
    CO2_ALERT_HIGH,
    CO2_ALERT_ENABLED,
    HUMIDITY_ALERT_HIGH,
    HUMIDITY_ALERT_LOW,
    HUMIDITY_ALERT_ENABLED,
    MOISTURE_ALERT_LOW,
    MOISTURE_ALERT_ENABLED,
    ALERT_DEDUP,
    MAX_ALERTS_PER_VIOLATION,
    MAX_TEMP_ALERTS_PER_VIOLATION,
    MAX_CO2_ALERTS_PER_VIOLATION,
    MAX_HUMIDITY_ALERTS_PER_VIOLATION,
    MAX_MOISTURE_ALERTS_PER_VIOLATION,
)

logger = setup_sensor_logger()


class AlertSystem:
    """
    Modular alert system for monitoring sensor thresholds.
    Tracks alert state to prevent duplicate alerts within a period.
    Easy to extend with new alert types.
    """

    def __init__(self):
        """Initialize alert state tracking."""
        # Track active alerts by key to enable deduplication
        # Format: {alert_key: True} if currently violated
        self.active_alerts = {}
        # Track how many alerts have been sent during the current violation
        # Format: {alert_key: int}
        self.alert_counts = {}

    def _max_for_key(self, alert_key: str) -> int:
        """Return per-sensor cap for given alert key, falling back to global cap."""
        mapping = {
            "temp_high": MAX_TEMP_ALERTS_PER_VIOLATION or MAX_ALERTS_PER_VIOLATION,
            "temp_low": MAX_TEMP_ALERTS_PER_VIOLATION or MAX_ALERTS_PER_VIOLATION,
            "co2_high": MAX_CO2_ALERTS_PER_VIOLATION or MAX_ALERTS_PER_VIOLATION,
            "humidity_high": MAX_HUMIDITY_ALERTS_PER_VIOLATION or MAX_ALERTS_PER_VIOLATION,
            "humidity_low": MAX_HUMIDITY_ALERTS_PER_VIOLATION or MAX_ALERTS_PER_VIOLATION,
            "moisture_low": MAX_MOISTURE_ALERTS_PER_VIOLATION or MAX_ALERTS_PER_VIOLATION,
        }
        return mapping.get(alert_key, MAX_ALERTS_PER_VIOLATION)

    def reset(self):
        """Reset all alert state (use when starting fresh/testing)."""
        logger.debug("Resetting all alert states")
        self.active_alerts.clear()
        self.alert_counts.clear()

    def check_temperature(self, temp_f):
        """
        Check temperature against configured thresholds.

        Args:
            temp_f (float): Temperature in Fahrenheit

        Returns:
            tuple: (alert_triggered, alert_message)
                alert_triggered (bool): True if threshold violated
                alert_message (str): Human-readable alert message
        """
        if not TEMP_ALERT_ENABLED or temp_f is None:
            return False, None

        alerts = []

        # Check high temperature
        if temp_f > TEMP_ALERT_HIGH:
            alert_key = "temp_high"
            # If in violation, send up to per-sensor cap times
            count = self.alert_counts.get(alert_key, 0)
            max_cap = self._max_for_key(alert_key)
            # Mark as active (needed to track state for recovery detection)
            self.active_alerts[alert_key] = True
            # Send alert if dedup is off OR first time OR under limit
            if not ALERT_DEDUP or count == 0 or count < max_cap:
                msg = f"🌡️ HIGH TEMPERATURE: {temp_f:.1f}°F (threshold: {TEMP_ALERT_HIGH}°F)"
                alerts.append(msg)
                if count < max_cap:
                    self.alert_counts[alert_key] = count + 1
                    logger.warning(f"Temperature alert triggered: {temp_f:.1f}°F exceeds {TEMP_ALERT_HIGH}°F (count: {count + 1}/{max_cap})")
                else:
                    logger.debug(f"Temperature still elevated: {temp_f:.1f}°F (at max alert limit {max_cap})")
            else:
                logger.debug(f"Temperature violation suppressed: {temp_f:.1f}°F (count: {count}/{max_cap})")
        else:
            # Recovery: previously violated, now back to normal
            if self.active_alerts.pop("temp_high", None):
                msg = f"ℹ️ Temperature normalized: {temp_f:.1f}°F (below {TEMP_ALERT_HIGH}°F)"
                alerts.append(msg)
                self.alert_counts["temp_high"] = 0
                logger.info(f"Temperature recovered to safe level: {temp_f:.1f}°F")

        # Check low temperature
        if temp_f < TEMP_ALERT_LOW:
            alert_key = "temp_low"
            count = self.alert_counts.get(alert_key, 0)
            max_cap = self._max_for_key(alert_key)
            # Mark as active (needed to track state for recovery detection)
            self.active_alerts[alert_key] = True
            # Send alert if dedup is off OR first time OR under limit
            if not ALERT_DEDUP or count == 0 or count < max_cap:
                msg = f"🌡️ LOW TEMPERATURE: {temp_f:.1f}°F (threshold: {TEMP_ALERT_LOW}°F)"
                alerts.append(msg)
                if count < max_cap:
                    self.alert_counts[alert_key] = count + 1
                    logger.warning(f"Low temperature alert triggered: {temp_f:.1f}°F below {TEMP_ALERT_LOW}°F (count: {count + 1}/{max_cap})")
                else:
                    logger.debug(f"Low temperature still below threshold: {temp_f:.1f}°F (at max alert limit {max_cap})")
            else:
                logger.debug(f"Low temperature violation suppressed: {temp_f:.1f}°F (count: {count}/{max_cap})")
        else:
            if self.active_alerts.pop("temp_low", None):
                msg = f"ℹ️ Temperature normalized: {temp_f:.1f}°F (above {TEMP_ALERT_LOW}°F)"
                alerts.append(msg)
                self.alert_counts["temp_low"] = 0
                logger.info(f"Low temperature recovered to safe level: {temp_f:.1f}°F")

        if alerts:
            return True, " | ".join(alerts)
        return False, None

    def check_co2(self, co2_ppm):
        """
        Check CO2 against configured thresholds.

        Args:
            co2_ppm (float): CO2 level in parts per million

        Returns:
            tuple: (alert_triggered, alert_message)
        """
        if not CO2_ALERT_ENABLED or co2_ppm is None:
            return False, None

        if co2_ppm > CO2_ALERT_HIGH:
            alert_key = "co2_high"
            count = self.alert_counts.get(alert_key, 0)
            max_cap = self._max_for_key(alert_key)
            # Mark as active (needed to track state for recovery detection)
            self.active_alerts[alert_key] = True
            # Send alert if dedup is off OR first time OR under limit
            if not ALERT_DEDUP or count == 0 or count < max_cap:
                msg = f"⚠️ HIGH CO2: {co2_ppm:.0f} ppm (threshold: {CO2_ALERT_HIGH} ppm)"
                if count < max_cap:
                    self.alert_counts[alert_key] = count + 1
                    logger.warning(f"CO2 alert triggered: {co2_ppm:.0f} ppm exceeds {CO2_ALERT_HIGH} ppm (count: {count + 1}/{max_cap})")
                else:
                    logger.debug(f"CO2 still elevated: {co2_ppm:.0f} ppm (at max alert limit {max_cap})")
                return True, msg
            else:
                logger.debug(f"CO2 violation suppressed: {co2_ppm:.0f} ppm (count: {count}/{max_cap})")
        else:
            if self.active_alerts.pop("co2_high", None):
                msg = f"ℹ️ CO2 normalized: {co2_ppm:.0f} ppm (below {CO2_ALERT_HIGH} ppm)"
                self.alert_counts["co2_high"] = 0
                logger.info(f"CO2 recovered to safe level: {co2_ppm:.0f} ppm")
                return True, msg

        return False, None

    def check_humidity(self, humidity_pct):
        """
        Check humidity against configured thresholds.

        Args:
            humidity_pct (float): Humidity as percentage

        Returns:
            tuple: (alert_triggered, alert_message)
        """
        if not HUMIDITY_ALERT_ENABLED or humidity_pct is None:
            return False, None

        alerts = []

        # Check high humidity
        if humidity_pct > HUMIDITY_ALERT_HIGH:
            alert_key = "humidity_high"
            count = self.alert_counts.get(alert_key, 0)
            max_cap = self._max_for_key(alert_key)
            # Mark as active (needed to track state for recovery detection)
            self.active_alerts[alert_key] = True
            # Send alert if dedup is off OR first time OR under limit
            if not ALERT_DEDUP or count == 0 or count < max_cap:
                msg = f"💧 HIGH HUMIDITY: {humidity_pct:.1f}% (threshold: {HUMIDITY_ALERT_HIGH}%)"
                alerts.append(msg)
                if count < max_cap:
                    self.alert_counts[alert_key] = count + 1
                    logger.warning(f"High humidity alert triggered: {humidity_pct:.1f}% exceeds {HUMIDITY_ALERT_HIGH}% (count: {count + 1}/{max_cap})")
                else:
                    logger.debug(f"High humidity still above threshold: {humidity_pct:.1f}% (at max alert limit {max_cap})")
            else:
                logger.debug(f"High humidity violation suppressed: {humidity_pct:.1f}% (count: {count}/{max_cap})")
        else:
            if self.active_alerts.pop("humidity_high", None):
                msg = f"ℹ️ Humidity normalized: {humidity_pct:.1f}% (below {HUMIDITY_ALERT_HIGH}%)"
                alerts.append(msg)
                self.alert_counts["humidity_high"] = 0
                logger.info(f"High humidity recovered to safe level: {humidity_pct:.1f}%")

        # Check low humidity
        if humidity_pct < HUMIDITY_ALERT_LOW:
            alert_key = "humidity_low"
            count = self.alert_counts.get(alert_key, 0)
            max_cap = self._max_for_key(alert_key)
            # Mark as active (needed to track state for recovery detection)
            self.active_alerts[alert_key] = True
            # Send alert if dedup is off OR first time OR under limit
            if not ALERT_DEDUP or count == 0 or count < max_cap:
                msg = f"💧 LOW HUMIDITY: {humidity_pct:.1f}% (threshold: {HUMIDITY_ALERT_LOW}%)"
                alerts.append(msg)
                if count < max_cap:
                    self.alert_counts[alert_key] = count + 1
                    logger.warning(f"Low humidity alert triggered: {humidity_pct:.1f}% below {HUMIDITY_ALERT_LOW}% (count: {count + 1}/{max_cap})")
                else:
                    logger.debug(f"Low humidity still below threshold: {humidity_pct:.1f}% (at max alert limit {max_cap})")
            else:
                logger.debug(f"Low humidity violation suppressed: {humidity_pct:.1f}% (count: {count}/{max_cap})")
        else:
            if self.active_alerts.pop("humidity_low", None):
                msg = f"ℹ️ Humidity normalized: {humidity_pct:.1f}% (above {HUMIDITY_ALERT_LOW}%)"
                alerts.append(msg)
                self.alert_counts["humidity_low"] = 0
                logger.info(f"Low humidity recovered to safe level: {humidity_pct:.1f}%")

        if alerts:
            return True, " | ".join(alerts)
        return False, None

    def check_moisture(self, moisture_pct):
        """
        Check soil moisture against configured thresholds.

        Args:
            moisture_pct (float): Soil moisture as percentage

        Returns:
            tuple: (alert_triggered, alert_message)
        """
        if not MOISTURE_ALERT_ENABLED or moisture_pct is None:
            return False, None

        if moisture_pct < MOISTURE_ALERT_LOW:
            alert_key = "moisture_low"
            count = self.alert_counts.get(alert_key, 0)
            max_cap = self._max_for_key(alert_key)
            # Mark as active (needed to track state for recovery detection)
            self.active_alerts[alert_key] = True
            # Send alert if dedup is off OR first time OR under limit
            if not ALERT_DEDUP or count == 0 or count < max_cap:
                msg = f"🌱 LOW SOIL MOISTURE: {moisture_pct:.1f}% (threshold: {MOISTURE_ALERT_LOW}%)"
                if count < max_cap:
                    self.alert_counts[alert_key] = count + 1
                    logger.warning(f"Low moisture alert triggered: {moisture_pct:.1f}% below {MOISTURE_ALERT_LOW}% (count: {count + 1}/{max_cap})")
                else:
                    logger.debug(f"Low moisture still below threshold: {moisture_pct:.1f}% (at max alert limit {max_cap})")
                return True, msg
            else:
                logger.debug(f"Low moisture violation suppressed: {moisture_pct:.1f}% (count: {count}/{max_cap})")
        else:
            if self.active_alerts.pop("moisture_low", None):
                msg = f"ℹ️ Soil moisture normalized: {moisture_pct:.1f}% (above {MOISTURE_ALERT_LOW}%)"
                self.alert_counts["moisture_low"] = 0
                logger.info(f"Low moisture recovered to safe level: {moisture_pct:.1f}%")
                return True, msg
        else:
            if self.active_alerts.pop("moisture_low", None):
                msg = f"ℹ️ Soil moisture normalized: {moisture_pct:.1f}% (above {MOISTURE_ALERT_LOW}%)"
                self.alert_counts["moisture_low"] = 0
                return True, msg

        return False, None

    def check_all(self, co2_ppm=None, temp_f=None, humidity_pct=None, moisture_pct=None):
        """
        Check all enabled alerts and collect messages.

        Args:
            co2_ppm (float): CO2 level in ppm
            temp_f (float): Temperature in °F
            humidity_pct (float): Humidity percentage
            moisture_pct (float): Soil moisture percentage

        Returns:
            tuple: (any_alerts, messages_list)
                any_alerts (bool): True if any threshold violated
                messages_list (list): List of alert messages to send
        """
        messages = []

        # Check each sensor type
        temp_alert, temp_msg = self.check_temperature(temp_f)
        if temp_alert:
            messages.append(temp_msg)

        co2_alert, co2_msg = self.check_co2(co2_ppm)
        if co2_alert:
            messages.append(co2_msg)

        humidity_alert, humidity_msg = self.check_humidity(humidity_pct)
        if humidity_alert:
            messages.append(humidity_msg)

        moisture_alert, moisture_msg = self.check_moisture(moisture_pct)
        if moisture_alert:
            messages.append(moisture_msg)

        has_alerts = len(messages) > 0
        if has_alerts:
            logger.info(f"Alert cycle complete: {len(messages)} alert(s) to send - {', '.join([m[:30] + '...' if len(m) > 30 else m for m in messages])}")
        else:
            logger.debug("Alert cycle complete: All sensors within normal range")
        
        return has_alerts, messages


def format_alert_body(alerts_list, co2=None, temp=None, humidity=None, moisture=None):
    """
    Format alert messages into an email body.

    Args:
        alerts_list (list): List of alert messages
        co2 (float): Current CO2 reading
        temp (float): Current temperature
        humidity (float): Current humidity
        moisture (float): Current moisture

    Returns:
        str: Formatted email body
    """
    body = "<h2>⚠️ Sensor Alert</h2>\n<p>"
    body += "<br>".join(alerts_list)
    body += "</p>\n<h3>Current Readings:</h3>\n<ul>\n"

    if co2 is not None:
        body += f"<li>CO2: {co2:.0f} ppm</li>\n"
    if temp is not None:
        body += f"<li>Temperature: {temp:.1f}°F</li>\n"
    if humidity is not None:
        body += f"<li>Humidity: {humidity:.1f}%</li>\n"
    if moisture is not None:
        body += f"<li>Soil Moisture: {moisture:.1f}%</li>\n"

    body += "</ul>\n<p>Check your PodsInSpace system immediately.</p>\n"

    return body
