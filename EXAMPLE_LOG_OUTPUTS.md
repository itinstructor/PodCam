# Email Alert System - Example Log Outputs

## Scenario 1: Temperature Alert Triggered and Email Sent Successfully

```
2026-01-11 14:23:45,123 WARNING  sensor      Temperature alert triggered: 86.5°F exceeds 85.0°F (count: 1/3)
2026-01-11 14:25:30,456 INFO     sensor      Alert cycle complete: 1 alert(s) to send - 🌡️ HIGH TEMPERATURE: 86.5°F...
2026-01-11 14:25:31,789 DEBUG    sensor      send_alert called - Type: 'Sensor Threshold', Recipients: ['williamaloring@gmail.com', 'williamloring@hotmail.com'], Message length: 2847 chars
2026-01-11 14:25:32,012 DEBUG    email       Attempting SMTP connection to smtp.gmail.com:587
2026-01-11 14:25:32,345 DEBUG    email       Initiating TLS encryption
2026-01-11 14:25:33,678 DEBUG    email       Authenticating with Gmail account: wnccrobotics@gmail.com
2026-01-11 14:25:33,901 DEBUG    email       Sending email with subject: PodsInSpace Sensor Threshold Alert
2026-01-11 14:25:34,234 INFO     email       ✅ Email sent successfully to williamaloring@gmail.com
2026-01-11 14:25:34,567 INFO     email       ✅ Email sent successfully to williamloring@hotmail.com
2026-01-11 14:25:34,890 INFO     sensor      📧 Alert email sent successfully - Subject: Sensor Threshold
```

**What happened:** 
- Temperature exceeded threshold at 14:23:45 → Alert triggered
- Averaging cycle completed at 14:25:30 → Email queued
- SMTP connection established and emails sent to both recipients
- ✅ Both emails delivered successfully


## Scenario 2: Multiple Alerts in Single Cycle

```
2026-01-11 14:35:20,123 WARNING  sensor      Temperature alert triggered: 88.2°F exceeds 85.0°F (count: 1/3)
2026-01-11 14:35:20,234 WARNING  sensor      High humidity alert triggered: 87.3% exceeds 85.0% (count: 1/3)
2026-01-11 14:37:45,456 INFO     sensor      Alert cycle complete: 2 alert(s) to send - 🌡️ HIGH TEMPERATURE: 88.2°F..., 💧 HIGH HUMIDITY: 87.3%...
2026-01-11 14:37:46,789 INFO     sensor      Preparing to send alert email - Type: Sensor Threshold, Message count: 2
2026-01-11 14:37:48,012 INFO     email       ✅ Email sent successfully to williamaloring@gmail.com
2026-01-11 14:37:48,345 INFO     sensor      📧 Alert email sent successfully - Subject: Sensor Threshold
```

**What happened:**
- Two sensors exceeded thresholds simultaneously
- Both alerts packed into one email (more efficient)
- Single email sent covering all violations


## Scenario 3: Alert at Maximum Limit (Suppression)

```
2026-01-11 10:15:20,123 WARNING  sensor      Temperature alert triggered: 87.1°F exceeds 85.0°F (count: 1/3)
2026-01-11 10:25:30,456 INFO     sensor      Alert cycle complete: 1 alert(s) to send
2026-01-11 10:25:34,789 INFO     sensor      📧 Alert email sent successfully - Subject: Sensor Threshold

2026-01-11 10:35:40,123 WARNING  sensor      Temperature alert triggered: 86.8°F exceeds 85.0°F (count: 2/3)
2026-01-11 10:45:50,456 INFO     sensor      Alert cycle complete: 1 alert(s) to send
2026-01-11 10:45:54,789 INFO     sensor      📧 Alert email sent successfully - Subject: Sensor Threshold

2026-01-11 10:55:00,123 WARNING  sensor      Temperature alert triggered: 87.5°F exceeds 85.0°F (count: 3/3)
2026-01-11 11:05:10,456 INFO     sensor      Alert cycle complete: 1 alert(s) to send
2026-01-11 11:05:14,789 INFO     sensor      📧 Alert email sent successfully - Subject: Sensor Threshold

2026-01-11 11:15:20,123 DEBUG    sensor      Temperature still elevated: 86.9°F (at max alert limit 3)
2026-01-11 11:25:30,456 DEBUG    sensor      Alert cycle complete: 0 alert(s) to send - No alerts to send
2026-01-11 11:35:40,123 DEBUG    sensor      Temperature still elevated: 87.2°F (at max alert limit 3)
2026-01-11 11:45:50,456 DEBUG    sensor      Alert cycle complete: 0 alert(s) to send - No alerts to send
```

**What happened:**
- 1st cycle: Alert sent (count 1/3)
- 2nd cycle: Alert sent (count 2/3)
- 3rd cycle: Alert sent (count 3/3)
- 4th+ cycles: No emails sent (suppressed at max limit) but state monitored
- This prevents email spam during prolonged violations


## Scenario 4: Recovery After Violation

```
2026-01-11 12:00:15,123 WARNING  sensor      Temperature alert triggered: 86.5°F exceeds 85.0°F (count: 1/3)
2026-01-11 12:10:30,456 INFO     sensor      📧 Alert email sent successfully - Subject: Sensor Threshold

2026-01-11 12:20:45,123 DEBUG    sensor      Temperature still elevated: 86.8°F (at max alert limit 3)
2026-01-11 12:30:56,456 DEBUG    sensor      Alert cycle complete: 0 alert(s) to send

2026-01-11 12:41:07,789 INFO     sensor      Temperature recovered to safe level: 78.5°F
2026-01-11 12:51:20,123 INFO     sensor      Alert cycle complete: 1 alert(s) to send - ℹ️ Temperature normalized: 78.5°F
2026-01-11 12:51:21,456 INFO     sensor      Preparing to send alert email - Type: Alert Cleared, Message count: 1
2026-01-11 12:51:22,789 INFO     email       ✅ Email sent successfully to williamaloring@gmail.com
2026-01-11 12:51:23,012 INFO     sensor      📧 Alert email sent successfully - Subject: Alert Cleared
```

**What happened:**
- Alert triggered and suppressed at max limit
- Temperature returned to safe range → Recovery detected
- Recovery email sent with "Alert Cleared" subject
- Alert counts reset to 0 for next violation cycle


## Scenario 5: Email Authentication Failure

```
2026-01-11 13:30:45,123 WARNING  sensor      Temperature alert triggered: 88.0°F exceeds 85.0°F (count: 1/3)
2026-01-11 13:40:56,456 INFO     sensor      Alert cycle complete: 1 alert(s) to send
2026-01-11 13:40:57,789 INFO     sensor      Preparing to send alert email - Type: Sensor Threshold, Message count: 1
2026-01-11 13:40:58,012 DEBUG    email       Attempting SMTP connection to smtp.gmail.com:587
2026-01-11 13:40:58,345 DEBUG    email       Initiating TLS encryption
2026-01-11 13:40:58,678 DEBUG    email       Authenticating with Gmail account: wnccrobotics@gmail.com
2026-01-11 13:40:59,901 ERROR    email       ❌ SMTP Authentication failed for wnccrobotics@gmail.com. Check email and app password.
2026-01-11 13:40:59,901 ERROR    sensor      📧 Alert email FAILED - Subject: Sensor Threshold, Alert count: 1
```

**What happened:**
- Alert was triggered correctly
- Email sending attempted
- Gmail credentials are wrong (password is likely regular password, not app password)
- Email delivery failed
- Check: Is DEFAULT_SENDER_PASSWORD using Gmail app password (not regular password)?


## Scenario 6: Network/SMTP Connection Failure

```
2026-01-11 14:15:30,123 WARNING  sensor      Temperature alert triggered: 87.3°F exceeds 85.0°F (count: 1/3)
2026-01-11 14:25:45,456 INFO     sensor      Alert cycle complete: 1 alert(s) to send
2026-01-11 14:25:46,789 INFO     sensor      Preparing to send alert email - Type: Sensor Threshold, Message count: 1
2026-01-11 14:25:47,012 DEBUG    email       Attempting SMTP connection to smtp.gmail.com:587
2026-01-11 14:25:47,345 ERROR    email       ❌ SMTP error occurred: [Errno 110] Connection timed out
2026-01-11 14:25:47,678 ERROR    sensor      📧 Alert email FAILED - Subject: Sensor Threshold, Alert count: 1
```

**What happened:**
- Alert was triggered correctly
- Email sending attempted
- Cannot connect to smtp.gmail.com (network issue, firewall, DNS)
- Email delivery failed
- Check: Is internet connectivity working? Can Raspberry Pi reach smtp.gmail.com:587?


## Scenario 7: Real-Time Alert (Before Averaging)

```
2026-01-11 14:03:15,789 WARNING  sensor      Reading 1/20: 1250 ppm | 86.7 °F | 65.3% | Moisture: 45.2%
2026-01-11 14:03:15,890 DEBUG    sensor      High CO2: 1250 ppm (at max alert limit 3)
2026-01-11 14:03:16,123 WARNING  sensor      REALTIME ALERT: ⚠️ HIGH CO2: 1250 ppm (threshold: 1500 ppm)
2026-01-11 14:03:16,234 INFO     sensor      Preparing to send real-time alert - Type: Sensor Threshold, Message count: 1
2026-01-11 14:03:17,567 INFO     email       ✅ Email sent successfully to williamaloring@gmail.com
2026-01-11 14:03:17,890 INFO     sensor      📧 Real-time alert email sent successfully - Subject: Sensor Threshold
```

**What happened:**
- CO2 spike detected on first reading
- Real-time alerting is enabled (ALERT_REALTIME = True in config.py)
- Alert sent immediately, before averaging cycle completes
- Faster response to critical conditions


## Scenario 8: All Sensors Normal - No Activity

```
2026-01-11 15:00:30,123 DEBUG    sensor      Alert cycle complete: All sensors within normal range
2026-01-11 15:10:45,234 DEBUG    sensor      Alert cycle complete: All sensors within normal range
2026-01-11 15:20:56,345 DEBUG    sensor      Alert cycle complete: All sensors within normal range
```

**What happened:**
- All sensors reading normally
- No threshold violations
- No emails sent
- This is the most common case - system running smoothly


## How to Interpret Your Logs

1. **Look for WARNING entries** - These show when thresholds are exceeded
2. **Look for ERROR entries** - These show when emails fail to send (❌ emoji)
3. **Look for INFO entries with ✅** - These show successful operations
4. **Look for DEBUG entries** - These show normal operation details
5. **Look for timestamps** - Help you correlate with when you noticed the issue

## Key Log Patterns

| Pattern | Meaning |
|---------|---------|
| `alert triggered: XX°F exceeds YY°F (count: 1/3)` | First alert for this violation |
| `alert triggered: XX°F exceeds YY°F (count: 2/3)` | Second alert (one more before suppression) |
| `alert triggered: XX°F exceeds YY°F (count: 3/3)` | Third alert (last before suppression) |
| `still elevated: XX°F (at max alert limit 3)` | Suppressed (temperature still high) |
| `recovered to safe level: XX°F` | Violation ended, recovery email sent |
| `FAILED - Subject: X, Alert count: Y` | Email delivery failed |
| `✅ Email sent successfully to X@Y.com` | Email delivered |
| `SMTP Authentication failed` | Wrong password for Gmail |
| `Connection timed out` | Cannot reach Gmail server |

