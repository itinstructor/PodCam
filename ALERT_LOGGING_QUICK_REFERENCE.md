# Alert System Logging Quick Reference

## What to Look For in the Logs

### ✅ Successful Alert Sending
```
WARNING  Temperature alert triggered: 86.5°F exceeds 85.0°F (count: 1/3)
INFO     Alert cycle complete: 1 alert(s) to send
DEBUG    send_alert called - Type: 'Sensor Threshold'
DEBUG    Attempting SMTP connection to smtp.gmail.com:587
INFO     ✅ Email sent successfully to williamaloring@gmail.com
INFO     📧 Alert email sent successfully - Subject: Sensor Threshold
```

### ⚠️ Alert at Max Limit (Will Stop Sending)
```
DEBUG    Temperature still elevated: 86.5°F (at max alert limit 3)
INFO     Alert cycle complete: 0 alert(s) to send
```
After 3 alerts, the system suppresses further emails while temp stays high (prevents spam).

### 🔄 Alert Recovery
```
INFO     Temperature recovered to safe level: 76.5°F
INFO     Alert cycle complete: 1 alert(s) to send - ℹ️ Temperature normalized
```
One recovery alert sent when temperature returns to normal.

### ❌ Email Sending Failed

**Authentication Error:**
```
ERROR    ❌ SMTP Authentication failed for wnccrobotics@gmail.com. Check email and app password.
ERROR    📧 Alert email FAILED - Subject: Sensor Threshold, Alert count: 1
```
- Check password in config.py
- Verify it's Gmail app password, not regular password
- Enable "Less secure app access" if needed

**SMTP Connection Error:**
```
ERROR    ❌ SMTP error occurred: [Errno 110] Connection timed out
ERROR    📧 Alert email FAILED - Subject: Sensor Threshold, Alert count: 1
```
- Check internet connectivity
- Verify smtp.gmail.com is accessible on port 587
- Check firewall rules

**TLS/SSL Error:**
```
ERROR    Initiating TLS encryption
ERROR    ❌ SMTP error occurred: [SSL: TLSV1_ALERT_UNKNOWN_CA] ...
```
- Network connectivity issue
- Try checking DNS resolution

## Log File Locations

```bash
# Sensor readings and alerts
/var/log/wncc_PodsInSpace/sensors.log

# Email-specific operations  
/var/log/wncc_PodsInSpace/email_notifications.log
```

## Commands to Monitor

### Watch Temperature Alerts in Real-Time
```bash
tail -f /var/log/wncc_PodsInSpace/sensors.log | grep -i temperature
```

### Find All Alerts Today
```bash
grep "Temperature alert\|CO2 alert\|Humidity alert\|Moisture alert" /var/log/wncc_PodsInSpace/sensors.log | tail -20
```

### Find Email Failures
```bash
grep "FAILED\|Authentication failed\|❌" /var/log/wncc_PodsInSpace/sensors.log
```

### Track Alert Limits Being Hit
```bash
grep "at max alert limit" /var/log/wncc_PodsInSpace/sensors.log
```

### See Email Delivery Success Rate
```bash
echo "Sent: $(grep '✅ Email sent' /var/log/wncc_PodsInSpace/sensors.log | wc -l)"
echo "Failed: $(grep 'FAILED' /var/log/wncc_PodsInSpace/sensors.log | wc -l)"
```

## Understanding Alert State

| Reading 1 | Reading 2 | Reading 3 | Reading 4+ | Recovery |
|-----------|-----------|-----------|-----------|----------|
| Alert sent (1/3) | Alert sent (2/3) | Alert sent (3/3) | Alert suppressed | Recovery alert sent |
| count: 1 | count: 2 | count: 3 | count: 3 | count: 0 |
| active: true | active: true | active: true | active: true | active: false |

See log messages for exactly what's happening at each step.

## Configuration to Check

If alerts aren't working as expected:

1. **Check threshold settings** in `alerts_config.py`:
   ```python
   TEMP_ALERT_HIGH = 85  # Check this value
   MAX_TEMP_ALERTS_PER_VIOLATION = 3  # How many before suppressing
   ALERT_DEDUP = True  # Deduplication enabled?
   ```

2. **Check email settings** in `config.py`:
   ```python
   DEFAULT_SENDER_EMAIL = "wnccrobotics@gmail.com"
   DEFAULT_SENDER_PASSWORD = "loyqlzkxisojeqsr"  # App password
   DEFAULT_RECIPIENT_EMAILS = ["williamaloring@gmail.com", ...]
   ```

3. **Check alert enabled flag** in `alerts_config.py`:
   ```python
   TEMP_ALERT_ENABLED = True  # Make sure this is True
   ```
