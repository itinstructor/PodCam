#!/usr/bin/env python3
"""
ALERT SYSTEM WORKFLOW & TESTING GUIDE
=====================================

This document shows exactly what happens when the alert system runs.
"""

WORKFLOW = """
ALERT SYSTEM WORKFLOW (Every 10 Minutes)
========================================

Timeline:
---------

00:00 - Start service
  ├─ Initialize AlertSystem() object
  │  └─ active_alerts = {} (empty)
  │
  ├─ Read sensors every 30 seconds
  │  └─ Collect readings: co2_readings[], temp_readings[], etc.
  │
  └─ Repeat 20 times over 10 minutes


10:00 - ThingSpeak Update Triggered
  ├─ Calculate averages (trimmed mean)
  │  ├─ avg_temp = 87.2°F
  │  ├─ avg_co2 = 650 ppm
  │  ├─ avg_humidity = 68%
  │  └─ avg_moisture = 45%
  │
  ├─ Send data to ThingSpeak
  │  └─ Log: "Data Received!"
  │
  └─ Run Alert Checks
     ├─ alert_system.check_all(
     │    co2_ppm=650,
     │    temp_f=87.2,
     │    humidity_pct=68,
     │    moisture_pct=45
     │  )
     │
     ├─ check_temperature(87.2)
     │  ├─ Is 87.2 > 85? YES! ✓
     │  ├─ Set active_alerts['temp_high'] = True
     │  └─ Return (True, "🌡️ HIGH TEMPERATURE: 87.2°F (threshold: 85°F)")
     │
     ├─ check_co2(650)
     │  ├─ Is 650 > 1500? NO
     │  └─ Return (False, None)
     │
     ├─ check_humidity(68)
     │  ├─ Is 68 > 85? NO
     │  ├─ Is 68 < 35? NO
     │  └─ Return (False, None)
     │
     └─ check_moisture(45)
        ├─ Is 45 < 20? NO
        └─ Return (False, None)


Alert Check Result: (True, ["🌡️ HIGH TEMPERATURE: 87.2°F (threshold: 85°F)"])


Alert Email Preparation
  ├─ has_alerts = True
  ├─ Log warning: "ALERT: 🌡️ HIGH TEMPERATURE: 87.2°F (threshold: 85°F)"
  │
  ├─ Format email body with:
  │  ├─ Alert messages
  │  ├─ Current readings
  │  └─ HTML formatting
  │
  └─ Send email via SMTP
     ├─ To: williamaloring@gmail.com, williamloring@hotmail.com, sarah.trook31@gmail.com
     ├─ Subject: "PodsInSpace Sensor Threshold Alert"
     └─ Body: <HTML with alert details and readings>


Post-Alert
  ├─ Log: "📧 Alert email sent" or "Alert email failed"
  ├─ alert_system.reset()
  │  └─ active_alerts = {} (cleared for next cycle)
  │
  └─ Clear reading lists for next cycle


20:00 - Next Cycle Begins
  └─ Process repeats...


DEDUPLICATION EXAMPLE
=====================

Scenario: Temperature stays above 85°F for multiple cycles

Cycle 1 (10:00):
  ├─ avg_temp = 87°F > 85°F threshold ✓ ALERT SENT
  ├─ active_alerts['temp_high'] = True
  └─ Email #1 sent: "HIGH TEMPERATURE: 87°F"

Cycle 2 (10:10):
  ├─ avg_temp = 86°F > 85°F threshold ✓
  ├─ Check: ALERT_DEDUP = True
  ├─ Is active_alerts['temp_high'] already True? YES
  ├─ Skip sending another alert (dedup prevents spam)
  └─ NO EMAIL sent (prevents notification fatigue)

Cycle 3 (10:20):
  ├─ avg_temp = 74°F < 85°F threshold ✗
  ├─ Temperature returned to normal
  ├─ Remove active_alerts['temp_high']
  └─ System ready to alert again if threshold violated

Cycle 4 (10:30):
  ├─ avg_temp = 88°F > 85°F threshold ✓
  ├─ Is active_alerts['temp_high'] True? NO (cleared in cycle 3)
  ├─ New violation detected!
  └─ Email #2 sent: "HIGH TEMPERATURE: 88°F" (NEW ALERT)


MULTIPLE ALERTS EXAMPLE
=======================

Scenario: Both temperature AND humidity exceed thresholds

Cycle 1 (14:00):
  ├─ avg_temp = 88°F > 85°F ✓
  ├─ avg_humidity = 87% > 85% ✓
  │
  ├─ check_temperature(88) → (True, "🌡️ HIGH TEMPERATURE: 88°F...")
  ├─ check_humidity(87) → (True, "💧 HIGH HUMIDITY: 87%...")
  │
  └─ Result: (True, [
       "🌡️ HIGH TEMPERATURE: 88°F (threshold: 85°F)",
       "💧 HIGH HUMIDITY: 87% (threshold: 85%)"
     ])


Single Email Sent With Both Alerts:
  ├─ Subject: "PodsInSpace Sensor Threshold Alert"
  ├─ Body includes:
  │  ├─ 🌡️ HIGH TEMPERATURE: 88°F
  │  ├─ 💧 HIGH HUMIDITY: 87%
  │  └─ Current readings table
  │
  └─ One email covers all violations (efficient)
"""

TESTING = """
TESTING THE ALERT SYSTEM
=========================

Method 1: Quick Test (Temperature Alert)
-----------------------------------------

Step 1: Edit alerts_config.py temporarily
  # Change to a value near current room temperature
  TEMP_ALERT_HIGH = 75  # If room is ~74°F, this will trigger
  TEMP_ALERT_ENABLED = True

Step 2: Restart service
  sudo systemctl restart sensors-ts

Step 3: Wait 10 minutes for ThingSpeak cycle
  # Watch logs in real-time:
  tail -f /var/log/wncc_PodsInSpace/sensors.log | grep -E "ALERT|Avg Temperature|Alert email"

Step 4: Expected output
  [14:30:00] Avg Temperature: 74.2 °F
  [14:30:00] ALERT: 🌡️ HIGH TEMPERATURE: 74.2°F (threshold: 75°F)
  [14:30:05] 📧 Alert email sent

Step 5: Restore original threshold
  # Change back to: TEMP_ALERT_HIGH = 85
  sudo systemctl restart sensors-ts


Method 2: Test Email Delivery
------------------------------

1. Check if email was actually received
   - Check your email inbox (including spam folder)
   - Sender: wnccrobotics@gmail.com
   - Subject: "PodsInSpace Sensor Threshold Alert"

2. Verify email content
   - Contains alert message(s)
   - Shows current sensor readings
   - Formatted as HTML

3. If email not received:
   - Check email_send_state.json for dedup history
   - Verify Gmail credentials in config.py
   - Test manual email: email_notification.py in console


Method 3: Check Deduplication
------------------------------

Step 1: Keep temperature above threshold for 30+ minutes
  - Maintain room temperature above your TEMP_ALERT_HIGH
  - Monitor for 3+ cycles (30 minutes)

Step 2: Expected behavior
  Cycle 1 (10:00): Email sent ✓
  Cycle 2 (10:10): NO email (dedup prevents spam)
  Cycle 3 (10:20): NO email (still dedup)

Step 3: Let temperature drop below threshold
  - Turn down heat or step away from heat source
  - Wait for next cycle

Step 4: Temperature goes back above threshold
  - Room warms up again
  - Next alert is sent (new violation)


Checking Alert State File
--------------------------

Alerts track state in: logs/email_send_state.json

View the file:
  cat logs/email_send_state.json

Example content:
  {
    "sensor_alert": {
      "checksum": "abc123...",
      "timestamp": 1704067800
    }
  }

This shows what was last sent to prevent duplicate emails.


Log Grep Examples
-----------------

View all alerts:
  grep ALERT /var/log/wncc_PodsInSpace/sensors.log

View sent emails:
  grep "Alert email sent" /var/log/wncc_PodsInSpace/sensors.log

View alert checks:
  grep "check_all" /var/log/wncc_PodsInSpace/sensors.log

View recent activity:
  tail -50 /var/log/wncc_PodsInSpace/sensors.log


Troubleshooting Steps
---------------------

If alerts not triggering:
  1. Check threshold values: cat alerts_config.py
  2. Check ENABLED flag: grep ALERT_ENABLED alerts_config.py
  3. Watch sensors reading: grep "Avg " sensors.log
  4. Restart service: sudo systemctl restart sensors-ts
  5. Check errors: tail -50 sensors.log | grep -i error

If emails not sending:
  1. Check if alerts triggering: grep ALERT sensors.log
  2. Test email config: python3 email_notification.py
  3. Check credentials: grep gmail config.py
  4. Verify network: ping gmail.com
  5. Check logs for SMTP errors

If too many emails:
  1. Increase threshold to reduce triggers
  2. Enable ALERT_DEDUP in alerts_config.py
  3. Reduce recipients list
  4. Check if temperature/sensor fluctuating


Manual Testing (Python Console)
--------------------------------

Test alert logic directly:

  from alert_system import AlertSystem
  from alerts_config import *

  alert_sys = AlertSystem()

  # Test high temperature alert
  has_alert, msg = alert_sys.check_temperature(87.5)
  print(has_alert, msg)
  # Output: True 🌡️ HIGH TEMPERATURE: 87.5°F (threshold: 85°F)

  # Test low temperature alert
  has_alert, msg = alert_sys.check_temperature(68.5)
  print(has_alert, msg)
  # Output: True 🌡️ LOW TEMPERATURE: 68.5°F (threshold: 70°F)

  # Test all sensors at once
  has_alert, msgs = alert_sys.check_all(
      temp_f=87.5,
      humidity_pct=88,
      co2_ppm=1600,
      moisture_pct=15
  )
  print(has_alert)
  print(msgs)
"""

TROUBLESHOOTING = """
COMMON ISSUES & SOLUTIONS
=========================

Q: "Alert email failed" - Email not sending

A: Check these in order:
   1. Service restarted? sudo systemctl restart sensors-ts
   2. Network working? ping gmail.com
   3. Credentials valid? cat config.py (check password)
   4. Gmail allows? Check "App password" vs regular password
   5. Firewall? Check port 587 open

Q: "Too many emails" - Receiving alert every cycle

A: Enable deduplication:
   # In alerts_config.py
   ALERT_DEDUP = True
   # Restart service

Q: "No alerts at all" - Even when threshold exceeded

A: Check in order:
   1. TEMP_ALERT_ENABLED = True (not False)
   2. Threshold values correct (TEMP_ALERT_HIGH = 85)
   3. Sensors working (check Avg Temp in logs)
   4. ServiceRestart: sudo systemctl restart sensors-ts

Q: "Wrong email recipients"

A: Update in config.py:
   DEFAULT_RECIPIENT_EMAILS = [
       "your_email@gmail.com",
   ]
   sudo systemctl restart sensors-ts

Q: "Alerts at wrong times"

A: Alerts check at ThingSpeak intervals
   Check THINGSPEAK_INTERVAL in config.py (default 600 seconds = 10 min)
   To check more often, reduce this value

Q: "Receiving emails but didn't change temperature"

A: Sensor reading changed within averaging period
   - Temperature fluctuates during 10-minute window
   - Alerts check averaged value, not individual readings
   - Check actual averages: grep "Avg Temp" sensors.log
"""

print(__doc__)
print(WORKFLOW)
print(TESTING)
print(TROUBLESHOOTING)
