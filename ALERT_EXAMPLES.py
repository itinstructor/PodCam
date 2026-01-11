"""
ALERT SETUP EXAMPLES
====================

This file shows common alert configurations.
Copy settings from here to alerts_config.py
"""

# ============================================================================
# EXAMPLE 1: TEMPERATURE ALERTS (Most Common)
# ============================================================================
# Alerts if pod temperature goes above 85°F or below 70°F
# Emails sent every 10 minutes (at ThingSpeak interval)

TEMP_ALERT_ENABLED = True
TEMP_ALERT_HIGH = 85   # Alert if exceeds this
TEMP_ALERT_LOW = 70    # Alert if drops below this

# Other alerts disabled
CO2_ALERT_ENABLED = False
HUMIDITY_ALERT_ENABLED = False
MOISTURE_ALERT_ENABLED = False


# ============================================================================
# EXAMPLE 2: COMPREHENSIVE MONITORING
# ============================================================================
# Monitor all four sensor types with multiple thresholds

TEMP_ALERT_ENABLED = True
TEMP_ALERT_HIGH = 85
TEMP_ALERT_LOW = 70

CO2_ALERT_ENABLED = True
CO2_ALERT_HIGH = 1500  # ppm - too much CO2

HUMIDITY_ALERT_ENABLED = True
HUMIDITY_ALERT_HIGH = 85   # Too humid
HUMIDITY_ALERT_LOW = 35    # Too dry

MOISTURE_ALERT_ENABLED = True
MOISTURE_ALERT_LOW = 20    # Soil needs water


# ============================================================================
# EXAMPLE 3: STRICT TEMPERATURE CONTROL
# ============================================================================
# For sensitive experiments requiring tight temperature range

TEMP_ALERT_ENABLED = True
TEMP_ALERT_HIGH = 78   # Tighter range
TEMP_ALERT_LOW = 72

HUMIDITY_ALERT_ENABLED = True
HUMIDITY_ALERT_HIGH = 70   # Control humidity too
HUMIDITY_ALERT_LOW = 50

CO2_ALERT_ENABLED = False
MOISTURE_ALERT_ENABLED = False


# ============================================================================
# EXAMPLE 4: DROUGHT MONITORING
# ============================================================================
# Focus on soil moisture with high temperature alert

TEMP_ALERT_ENABLED = True
TEMP_ALERT_HIGH = 90   # High threshold (summer heat ok)
TEMP_ALERT_LOW = 50    # Low threshold (frost alert)

MOISTURE_ALERT_ENABLED = True
MOISTURE_ALERT_LOW = 15  # Alert if soil too dry

HUMIDITY_ALERT_ENABLED = False
CO2_ALERT_ENABLED = False


# ============================================================================
# HOW TO USE THIS FILE
# ============================================================================
# 1. Choose the example that best matches your needs
# 2. Copy the settings to alerts_config.py
# 3. Customize values for your specific requirements
# 4. Save and restart the service:
#    sudo systemctl restart sensors-ts


# ============================================================================
# THRESHOLD GUIDANCE
# ============================================================================

TEMPERATURE_RANGES = {
    "Typical Crops": {"min": 65, "max": 85},
    "Heat Sensitive": {"min": 68, "max": 75},
    "Cold Hardy": {"min": 50, "max": 80},
    "Tropical": {"min": 75, "max": 90},
}

HUMIDITY_RANGES = {
    "Most Plants": {"min": 40, "max": 70},
    "Orchids": {"min": 50, "max": 80},
    "Succulents": {"min": 20, "max": 50},
    "Seedlings": {"min": 60, "max": 80},
}

MOISTURE_RANGES = {
    "Well Drained": {"alert_low": 25},
    "Standard": {"alert_low": 20},
    "Water Loving": {"alert_low": 15},
}

CO2_RANGES = {
    "Outdoor Air": {"typical": 410},
    "Normal Room": {"typical": 400-500},
    "High CO2": {"alert_threshold": 1200},
    "Critical": {"alert_threshold": 1500},
}


# ============================================================================
# TIPS FOR SETTING THRESHOLDS
# ============================================================================

TIPS = """
1. START CONSERVATIVE
   - Set wider thresholds initially (e.g., 80°F instead of 75°F)
   - Reduce after observing normal operation

2. CONSIDER NATURAL VARIATION
   - Room temperature varies throughout day
   - Plant growth affects humidity
   - Watering affects soil moisture

3. WATCH THE LOGS
   - Monitor actual readings for a few days
   - Set alerts at extremes, not averages
   - grep ALERT /var/log/wncc_PodsInSpace/sensors.log

4. ALERT FATIGUE
   - Too many alerts = ignored alerts
   - Only alert on truly important thresholds
   - Start with just temperature

5. SEASONAL ADJUSTMENTS
   - Summer: Raise temp alert (AC working harder)
   - Winter: Lower temp alert (heating minimal)
   - Update every season

6. TEST YOUR SETTINGS
   - Temporarily lower threshold to test
   - Verify email arrives
   - Check logs for "Alert email sent"
   - Restore original threshold

7. COORDINATE WITH TEAM
   - Discuss alert thresholds with team
   - Agree on response procedures
   - Document decisions
"""

print(__doc__)
print(TIPS)
