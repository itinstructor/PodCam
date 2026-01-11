# Email Alert System - Logging Changes Summary

## What Was Added

Comprehensive logging has been implemented throughout the email alert system to help with:
- ✅ Monitoring alert triggers and status
- ✅ Tracking email delivery success/failure
- ✅ Debugging SMTP connection issues
- ✅ Understanding alert deduplication behavior
- ✅ Troubleshooting authentication problems

## Files Modified

### 1. `alert_system.py`
Added detailed logging for:
- Alert triggering (with reading, threshold, and count/max)
- Alert suppression (when at max limit)
- Alert recovery (when returning to normal)
- Overall alert cycle summary (how many alerts to send)

**Log Levels:**
- WARNING: Alert threshold triggered
- DEBUG: Suppressed alerts, normal operation details
- INFO: Recovery events
- DEBUG: Reset operations

### 2. `sensors_ts.py`
Enhanced alert email sending logging with:
- Pre-send notification (alert type, message count, recipients)
- Success notification with subject type
- Failure logging with alert details
- Exception handling with full stack trace
- Support for both real-time and interval-based alerts

**Log Levels:**
- INFO: Email prepare and success
- ERROR: Email failures with details

### 3. `email_notification.py`
Added SMTP operation logging for:
- Alert method invocation with parameters
- SMTP connection attempts (server, port, TLS)
- Authentication with Gmail account
- Email transmission with subject line
- Success/failure status with emoji indicators

**Log Levels:**
- DEBUG: Connection and auth details
- INFO: Successful sends with ✅ emoji
- ERROR: Failures with ❌ emoji, reasons, and stack trace

## New Documentation Files

### 1. `LOGGING_ENHANCEMENTS.md`
Complete reference of all logging additions including:
- Detailed breakdown by sensor type
- All log levels and when they're used
- Recommended grep commands for monitoring
- Troubleshooting sections for common issues
- Example log output

### 2. `ALERT_LOGGING_QUICK_REFERENCE.md`
Quick guide for:
- What to look for in logs (success/failure patterns)
- Log file locations
- Useful monitoring commands
- Understanding alert state transitions
- Configuration checklist

### 3. `EXAMPLE_LOG_OUTPUTS.md`
8 real-world scenarios with actual log examples:
1. Successful alert and email delivery
2. Multiple alerts in one cycle
3. Alert at maximum limit (suppression)
4. Recovery after violation
5. Email authentication failure
6. Network/SMTP connection failure
7. Real-time alert (before averaging)
8. All sensors normal (no activity)

## Key Features of the New Logging

### Hierarchical Logging
```
SENSOR          ALERTS           EMAILS        SMTP
Temperature   + Alert            + Type        + Connection
CO2           + Count/Limit      + Recipients  + Auth
Humidity      + Recovery         + Success/Fail + TLS
Moisture      + Suppress at Max  + Exception   + Message Sent
```

### Emoji Indicators
- ✅ Successful operations
- ❌ Failed operations
- 📧 Email notifications
- 🌡️ Temperature alerts
- 💧 Humidity/Moisture alerts
- ⚠️ CO2 alerts
- 🌱 Soil moisture alerts

### Structured Information
Each log entry includes:
- Timestamp with milliseconds
- Log level (WARNING, INFO, DEBUG, ERROR)
- Module name (sensor, email)
- Contextual details (readings, thresholds, counts)

### Exception Handling
All exceptions logged with:
- Full error message
- Stack trace (with `exc_info=True`)
- Context about what was being attempted

## Usage Examples

### Monitor Temperature Alerts
```bash
tail -f /var/log/wncc_PodsInSpace/sensors.log | grep "Temperature alert"
```

### Watch Email Delivery
```bash
tail -f /var/log/wncc_PodsInSpace/sensors.log | grep "📧\|FAILED"
```

### Debug SMTP Issues
```bash
grep "SMTP\|Authentication\|TLS" /var/log/wncc_PodsInSpace/email_notifications.log
```

### Find Failed Emails Today
```bash
grep "$(date +%Y-%m-%d).*FAILED" /var/log/wncc_PodsInSpace/sensors.log
```

### Count Alerts vs Sends
```bash
echo "Alerts sent: $(grep '✅ Email sent' /var/log/wncc_PodsInSpace/sensors.log | wc -l)"
echo "Alerts failed: $(grep 'FAILED' /var/log/wncc_PodsInSpace/sensors.log | wc -l)"
```

## Impact on Performance

- **Minimal overhead**: Debug logging is fast, INFO/WARNING/ERROR only on actual events
- **Disk usage**: Logs rotate daily by default (see `logging_config.py`)
- **Memory**: No additional memory required (logging uses standard Python logger)
- **Network**: No new network calls (only standard email system)

## Integration with Existing Code

- ✅ Compatible with existing `logging_config.py` setup
- ✅ Uses existing logger instances
- ✅ Follows existing log level conventions
- ✅ No changes to alert logic, only added logging
- ✅ No changes to email sending logic, only added logging

## Testing the Logging

### Test with alerts_test.py
```bash
python3 alerts_test.py
# Select option to test temperature
# Watch logs in parallel:
tail -f /var/log/wncc_PodsInSpace/sensors.log
```

### Monitor Current sensors_ts.py
```bash
# Watch real-time logs
tail -f /var/log/wncc_PodsInSpace/sensors.log | grep -E "Alert|📧|FAILED"
```

### Check Historical Data
```bash
# Today's alerts
grep "$(date +%Y-%m-%d).*WARNING" /var/log/wncc_PodsInSpace/sensors.log

# Yesterday's failures
grep "$(date -d yesterday +%Y-%m-%d).*FAILED" /var/log/wncc_PodsInSpace/sensors.log
```

## What to Do with Logs

### For Monitoring (Ongoing)
- Set up log tailing in a terminal window
- Watch for ERROR and FAILED patterns
- Note any authentication issues
- Monitor alert frequency trends

### For Debugging (Problem Investigation)
- Search for timestamps around when issue occurred
- Look at full context of errors (including stack traces)
- Check sensor readings before alert
- Verify email configuration in config.py
- Test email sending with alerts_test.py

### For Reporting (Documentation)
- Copy log excerpts showing the issue
- Include timestamps for reference
- Share ERROR entries and context
- Note any patterns in failures

## Backward Compatibility

- ✅ No changes to function signatures
- ✅ No changes to return values
- ✅ No changes to alert behavior
- ✅ No changes to email sending behavior
- ✅ Purely additive logging enhancements
- ✅ Can be disabled by adjusting logging level if needed

## Next Steps

1. **Deploy** the updated code to your system
2. **Monitor** the logs using the provided commands
3. **Check** for any authentication or connection issues
4. **Verify** alerts are being triggered for your thresholds
5. **Confirm** emails are being delivered to recipients

## Support Resources

- [LOGGING_ENHANCEMENTS.md](LOGGING_ENHANCEMENTS.md) - Detailed reference
- [ALERT_LOGGING_QUICK_REFERENCE.md](ALERT_LOGGING_QUICK_REFERENCE.md) - Quick lookup
- [EXAMPLE_LOG_OUTPUTS.md](EXAMPLE_LOG_OUTPUTS.md) - Real scenarios
- [alerts_config.py](alerts_config.py) - Threshold settings
- [config.py](config.py) - Email configuration
