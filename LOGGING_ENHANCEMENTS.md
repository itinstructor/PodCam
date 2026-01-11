# Email Alert System Logging Enhancements

## Overview
Comprehensive logging has been added to the email alert system to provide detailed visibility into alert triggering, deduplication, email sending, and SMTP operations.

## Logging Additions

### 1. **alert_system.py** - Alert Monitoring

#### Alert Initialization
- `DEBUG`: Reset all alert states when `reset()` is called

#### Temperature Checks
- `WARNING`: When high temperature alert is triggered (includes reading, threshold, and count)
- `DEBUG`: When temperature violation is suppressed (at max alert limit)
- `DEBUG`: When temperature is elevated but already at max alert limit
- `INFO`: When temperature recovers to safe level

- `WARNING`: When low temperature alert is triggered
- `DEBUG`: When low temperature violation is suppressed
- `INFO`: When low temperature recovers to safe level

#### CO2 Checks
- `WARNING`: When high CO2 alert is triggered (includes reading, threshold, and count)
- `DEBUG`: When CO2 violation is suppressed
- `DEBUG`: When CO2 is elevated but at max alert limit
- `INFO`: When CO2 recovers to safe level

#### Humidity Checks
- `WARNING`: When high humidity alert is triggered
- `DEBUG`: When high humidity violation is suppressed
- `INFO`: When high humidity recovers to safe level

- `WARNING`: When low humidity alert is triggered
- `DEBUG`: When low humidity violation is suppressed
- `INFO`: When low humidity recovers to safe level

#### Moisture Checks
- `WARNING`: When low moisture alert is triggered
- `DEBUG`: When low moisture violation is suppressed
- `DEBUG`: When moisture is low but at max alert limit
- `INFO`: When moisture recovers to safe level

#### Overall Alert Cycle
- `INFO`: Summary of alert cycle with count of alerts to send
- `DEBUG`: When all sensors are within normal range

### 2. **sensors_ts.py** - Email Sending

#### Real-Time Alerts
- `INFO`: When preparing to send real-time alert (includes type and message count)
- `INFO`: When real-time alert email sent successfully
- `ERROR`: When real-time alert email fails (includes alert type and message count)
- `ERROR`: When exception occurs in real-time alerting (with full stack trace)

#### Interval-Based Alerts
- `INFO`: When preparing to send averaged data alert
- `INFO`: When alert email sent successfully (includes subject type)
- `ERROR`: When alert email fails (includes subject type and message count)
- `ERROR`: When exception occurs in alert sending (with full stack trace)

### 3. **email_notification.py** - SMTP Operations

#### Send Alert Method
- `DEBUG`: Alert method called with alert type, recipients, and message length

#### SMTP Connection and Transmission
- `DEBUG`: Attempting SMTP connection (server and port)
- `DEBUG`: Initiating TLS encryption
- `DEBUG`: Authenticating with Gmail account
- `DEBUG`: Sending email with subject line
- `INFO`: Email sent successfully to recipient(s) with ✅ emoji
- `ERROR`: SMTP authentication failure with instruction to check credentials
- `ERROR`: Generic SMTP errors
- `ERROR`: Other exceptions during email sending (with full stack trace)

## Log Levels Used

- **ERROR** (❌): Critical failures that prevent email delivery
- **WARNING**: Alert thresholds triggered or sensor violations detected
- **INFO** (✅): Successful operations and important state changes
- **DEBUG**: Detailed operational information, suppressed alerts, normal operation flow

## Monitoring the Logs

### Check Current Alert Status
```bash
tail -f /var/log/wncc_PodsInSpace/sensors.log | grep -E "WARNING|ERROR|ALERT"
```

### Monitor Email Delivery
```bash
tail -f /var/log/wncc_PodsInSpace/sensors.log | grep -E "send_alert|Email|📧"
```

### Track SMTP Operations
```bash
tail -f /var/log/wncc_PodsInSpace/email_notifications.log | grep -E "SMTP|Authentication|TLS|connection"
```

### View All Alert Activity
```bash
tail -f /var/log/wncc_PodsInSpace/sensors.log | grep -i "alert\|temperature\|humidity\|co2\|moisture"
```

### Find Failed Emails
```bash
grep "FAILED\|ERROR\|❌" /var/log/wncc_PodsInSpace/sensors.log
```

## Troubleshooting

### Issue: Alerts Not Being Sent
1. Check for `ALERT:` messages in sensors.log - verify alerts are being triggered
2. Look for `Preparing to send alert email` - email attempt was made
3. Check email_notifications.log for `SMTP Authentication failed` - verify Gmail credentials
4. Look for exception messages with stack traces for detailed error info

### Issue: Too Many Alerts
1. Check `alert_counts` in logs to verify deduplication is working
2. Confirm `MAX_TEMP_ALERTS_PER_VIOLATION` setting in alerts_config.py
3. Look for "violation suppressed" messages indicating hits on max limits

### Issue: Emails Not Arriving
1. Verify recipient addresses in `DEFAULT_RECIPIENT_EMAILS` in config.py
2. Check for `TLS` and `SMTP` connection logs - verify SMTP server connectivity
3. Look for authentication errors - verify Gmail app password (not regular password)
4. Check spam/junk folders - Gmail may filter automated emails

## Example Log Output

```
2026-01-11 14:23:45 WARNING  Temperature alert triggered: 86.5°F exceeds 85.0°F (count: 1/3)
2026-01-11 14:25:30 INFO     Alert cycle complete: 1 alert(s) to send - 🌡️ HIGH TEMPERATURE: 86.5°F...
2026-01-11 14:25:31 DEBUG    send_alert called - Type: 'Sensor Threshold', Recipients: ['williamaloring@gmail.com'], Message length: 2847 chars
2026-01-11 14:25:32 DEBUG    Attempting SMTP connection to smtp.gmail.com:587
2026-01-11 14:25:32 DEBUG    Initiating TLS encryption
2026-01-11 14:25:33 DEBUG    Authenticating with Gmail account: wnccrobotics@gmail.com
2026-01-11 14:25:33 DEBUG    Sending email with subject: PodsInSpace Sensor Threshold Alert
2026-01-11 14:25:34 INFO     ✅ Email sent successfully to williamaloring@gmail.com
2026-01-11 14:25:34 INFO     📧 Alert email sent successfully - Subject: Sensor Threshold
```

## Related Configuration Files

- [alerts_config.py](alerts_config.py) - Alert thresholds and limits
- [config.py](config.py) - Email credentials and recipients
- [logging_config.py](logging_config.py) - Logging configuration
