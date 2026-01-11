# Email Alert System - Logging Flow Diagram

## Data Flow with Logging Points

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SENSOR READING CYCLE                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  Read Sensors (co2_sensor_ts.py, moisture_sensor_ts.py)                │
│         │                                                                │
│         ▼                                                                │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ OPTIONAL: Real-Time Alert Check (if ALERT_REALTIME = True)      │  │
│  │ ┌────────────────────────────────────────────────────────────┐  │  │
│  │ │ call: alert_system.check_all(co2, temp, humidity, moisture)│  │  │
│  │ │                                                            │  │  │
│  │ │ LOGGING POINTS (alert_system.py):                        │  │  │
│  │ │   ✅ WARNING: Alert triggered with reading/threshold      │  │  │
│  │ │   ✅ DEBUG: Alert suppressed or at max limit              │  │  │
│  │ │   ✅ INFO: Sensor recovered to normal                     │  │  │
│  │ │                                                            │  │  │
│  │ └────────────────────────────────────────────────────────────┘  │  │
│  │                     │                                             │  │
│  │                     ▼                                             │  │
│  │              Alert triggered?                                   │  │
│  │              /        \                                         │  │
│  │           YES          NO                                       │  │
│  │           /              \                                      │  │
│  │          ▼                ▼                                      │  │
│  │   Format Email      Continue                                   │  │
│  │   Send Alert        Looping                                    │  │
│  │          │                                                      │  │
│  │          ▼                                                      │  │
│  │   [See Email Flow Below]                                       │  │
│  │                                                                │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                        │
│  Sleep SENSOR_READ_INTERVAL seconds (usually 30s)                    │
│         │                                                             │
│         ▼                                                             │
│  Repeat until THINGSPEAK_INTERVAL seconds have passed (10 min)       │
│                                                                        │
└─────────────────────────────────────────────────────────────────────────┘
```

## Averaging Cycle and Alert Check

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    AVERAGING CYCLE (Every 10 Minutes)                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  Collected 20 readings over 10 minutes                                  │
│         │                                                                │
│         ▼                                                                │
│  Calculate Averages (trim outliers)                                    │
│         │                                                                │
│         ▼                                                                │
│  Send to ThingSpeak                                                    │
│         │                                                                │
│         ▼                                                                │
│  ┌────────────────────────────────────────────────────────────────────┐│
│  │ INTERVAL ALERT CHECK: alert_system.check_all(avg_co2, avg_temp...)││
│  │                                                                    ││
│  │ LOGGING IN alert_system.py:                                      ││
│  │  ✅ WARNING: "Temperature alert triggered: XX°F exceeds YY°F"  ││
│  │  ✅ INFO: "Alert cycle complete: X alert(s) to send"           ││
│  │  ✅ DEBUG: "Temperature still elevated (at max limit 3)"       ││
│  │  ✅ DEBUG: "Alert cycle complete: All sensors normal"          ││
│  │                                                                    ││
│  └────────────────────────────────────────────────────────────────────┘│
│                    │                                                     │
│                    ▼                                                     │
│             Has Alerts?                                                │
│             /       \                                                   │
│          YES         NO                                                 │
│          /             \                                                │
│         ▼               ▼                                                │
│    [Send Email]    Wait for next cycle                                 │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Email Sending Flow (with Logging)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         EMAIL SENDING FLOW                                │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  Format Alert Body                                                       │
│  Determine Recipients (DEFAULT_RECIPIENT_EMAILS)                         │
│         │                                                                 │
│         ▼                                                                 │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ email_notifier.send_alert(                                      │   │
│  │    recipient_email=None,                                        │   │
│  │    alert_type="Sensor Threshold",                              │   │
│  │    alert_message="<html>..."                                   │   │
│  │ )                                                               │   │
│  │                                                                 │   │
│  │ LOGGING IN email_notification.py:                              │   │
│  │  ✅ DEBUG: "send_alert called - Type: X, Recipients: Y, Len: Z" │   │
│  │                                                                 │   │
│  │ Create MIMEMultipart message                                   │   │
│  │ Set headers (From, To, Subject, etc)                          │   │
│  │ Add HTML content                                               │   │
│  │                                                                 │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│         │                                                                 │
│         ▼                                                                 │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ _send_message(msg, recipients)                                  │   │
│  │                                                                 │   │
│  │ LOGGING IN email_notification.py:                              │   │
│  │  ✅ DEBUG: "Attempting SMTP connection to smtp.gmail.com:587"  │   │
│  │                                                                 │   │
│  │ Create SMTP Connection                                         │   │
│  │          │                                                      │   │
│  │          ▼                                                      │   │
│  │  ┌─────────────────────────────────────────────────────────┐  │   │
│  │  │ LOGGING: DEBUG: "Initiating TLS encryption"            │  │   │
│  │  │                                                         │  │   │
│  │  │ server.starttls()                                       │  │   │
│  │  │        │                                                │  │   │
│  │  │        ▼                                                │  │   │
│  │  │ ✅ TLS Connected                                        │  │   │
│  │  │                                                         │  │   │
│  │  └─────────────────────────────────────────────────────────┘  │   │
│  │         │                                                      │   │
│  │         ▼                                                      │   │
│  │  ┌─────────────────────────────────────────────────────────┐  │   │
│  │  │ LOGGING: DEBUG: "Authenticating with Gmail account..."  │  │   │
│  │  │                                                         │  │   │
│  │  │ server.login(sender_email, sender_password)            │  │   │
│  │  │        │                                                │  │   │
│  │  │        ▼                                                │  │   │
│  │  │ Authentication Result?                                 │  │   │
│  │  │ /                       \                               │  │   │
│  │  │SUCCESS                  FAILED                          │  │   │
│  │  │ │                           │                           │  │   │
│  │  │ ▼                           ▼                           │  │   │
│  │  │Continue               ERROR: Auth Failed               │  │   │
│  │  │                       (see error branch)               │  │   │
│  │  │                                                         │  │   │
│  │  └─────────────────────────────────────────────────────────┘  │   │
│  │         │                                                      │   │
│  │         ▼                                                      │   │
│  │  ┌─────────────────────────────────────────────────────────┐  │   │
│  │  │ LOGGING: DEBUG: "Sending email with subject: X"         │  │   │
│  │  │                                                         │  │   │
│  │  │ server.sendmail(sender, recipients, msg)              │  │   │
│  │  │        │                                                │  │   │
│  │  │        ▼                                                │  │   │
│  │  │ Server closes (server.quit())                          │  │   │
│  │  │        │                                                │  │   │
│  │  │        ▼                                                │  │   │
│  │  │ ✅ SUCCESS                                              │  │   │
│  │  │                                                         │  │   │
│  │  └─────────────────────────────────────────────────────────┘  │   │
│  │                                                                 │   │
│  │ LOGGING IN email_notification.py:                              │   │
│  │  ✅ INFO: "✅ Email sent successfully to name@example.com"    │   │
│  │                                                                 │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│         │                                                                 │
│         ▼                                                                 │
│  Return True                                                             │
│         │                                                                 │
│         ▼                                                                 │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ Back in sensors_ts.py:                                            │ │
│  │  LOGGING: INFO: "📧 Alert email sent successfully - Subject: X"  │ │
│  │                                                                    │ │
│  │ Continue normal operation                                        │ │
│  │                                                                    │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└──────────────────────────────────────────────────────────────────────────┘
```

## Error Handling Paths

### Path 1: SMTP Connection Failure
```
Attempting SMTP connection
          │
          ▼
    Connection Failed (timeout, network issue, etc)
          │
          ▼
LOGGING ERROR: "❌ SMTP error occurred: [Errno 110] Connection timed out"
          │
          ▼
Return False
          │
          ▼
LOGGING ERROR: "📧 Alert email FAILED - Subject: X, Alert count: Y"
          │
          ▼
Alert Email Not Sent ❌
```

### Path 2: Authentication Failure
```
TLS Connected Successfully
          │
          ▼
server.login(email, password)
          │
          ▼
Authentication Failed
          │
          ▼
LOGGING ERROR: "❌ SMTP Authentication failed. Check email and app password."
          │
          ▼
Return False
          │
          ▼
LOGGING ERROR: "📧 Alert email FAILED - Subject: X, Alert count: Y"
          │
          ▼
Alert Email Not Sent ❌
```

### Path 3: Unexpected Exception
```
Any operation
          │
          ▼
Unexpected Exception Occurs
          │
          ▼
LOGGING ERROR: "❌ Error sending email: [exception details]"
            + exc_info=True (full stack trace)
          │
          ▼
Return False
          │
          ▼
LOGGING ERROR: "Error sending alert email: [exception]"
            + exc_info=True (full stack trace)
          │
          ▼
Alert Email Not Sent ❌
```

## Log Levels Over Time

```
Timeline of a Temperature Alert Violation:

TIME    │ EVENT                                    │ LOG LEVEL │ LOG MESSAGE
────────┼────────────────────────────────────────┼───────────┼──────────────────────────
14:23:45│ Temperature reads 86.5°F (>85° limit)   │ WARNING   │ Temperature alert triggered
        │ First check_temperature() call          │           │ (count: 1/3)
────────┼────────────────────────────────────────┼───────────┼──────────────────────────
14:25:30│ Averaging cycle completes               │ INFO      │ Alert cycle complete: 1 alert
        │ check_all() called with avg=86.8°F      │           │ to send
────────┼────────────────────────────────────────┼───────────┼──────────────────────────
14:25:31│ send_alert() called                     │ DEBUG     │ send_alert called - Type:
        │                                        │           │ Sensor Threshold
────────┼────────────────────────────────────────┼───────────┼──────────────────────────
14:25:32│ SMTP connection initiated               │ DEBUG     │ Attempting SMTP connection
────────┼────────────────────────────────────────┼───────────┼──────────────────────────
14:25:32│ TLS encryption started                  │ DEBUG     │ Initiating TLS encryption
────────┼────────────────────────────────────────┼───────────┼──────────────────────────
14:25:33│ Gmail authentication                    │ DEBUG     │ Authenticating with Gmail
────────┼────────────────────────────────────────┼───────────┼──────────────────────────
14:25:33│ Email being sent                        │ DEBUG     │ Sending email with subject
────────┼────────────────────────────────────────┼───────────┼──────────────────────────
14:25:34│ Email transmitted successfully          │ INFO      │ ✅ Email sent to user@email
────────┼────────────────────────────────────────┼───────────┼──────────────────────────
14:25:34│ Confirmation in sensors_ts.py           │ INFO      │ 📧 Alert email sent
        │                                        │           │ successfully
────────┼────────────────────────────────────────┼───────────┼──────────────────────────
14:35:40│ Temp still 86.2°F at next cycle         │ WARNING   │ Temperature alert triggered
        │ send_alert() called again              │           │ (count: 2/3)
────────┼────────────────────────────────────────┼───────────┼──────────────────────────
...     │ [Similar pattern repeats]              │ ...       │ ...
────────┼────────────────────────────────────────┼───────────┼──────────────────────────
15:05:00│ Temp still 87.1°F (3rd cycle = 3/3)   │ WARNING   │ Temperature alert triggered
        │                                        │           │ (count: 3/3)
────────┼────────────────────────────────────────┼───────────┼──────────────────────────
15:05:01│ Email sent (last alert allowed)        │ INFO      │ ✅ Email sent successfully
────────┼────────────────────────────────────────┼───────────┼──────────────────────────
15:15:10│ Temp STILL 86.5°F (4th cycle)          │ DEBUG     │ Temperature still elevated
        │ check_all() called                     │           │ (at max alert limit 3)
────────┼────────────────────────────────────────┼───────────┼──────────────────────────
15:15:11│ No alert sent (suppressed)              │ INFO      │ Alert cycle complete: 0
        │                                        │           │ alert(s) to send
────────┼────────────────────────────────────────┼───────────┼──────────────────────────
15:25:20│ Temp returns to 78.3°F (below 85°)    │ INFO      │ Temperature recovered to
        │ Recovery detected!                     │           │ safe level
────────┼────────────────────────────────────────┼───────────┼──────────────────────────
15:25:21│ Recovery email sent                    │ INFO      │ ✅ Email sent successfully
        │ (type = "Alert Cleared")               │           │
────────┼────────────────────────────────────────┼───────────┼──────────────────────────
15:25:22│ Confirmation of recovery email         │ INFO      │ 📧 Alert email sent
        │                                        │           │ successfully (Alert Cleared)
────────┴────────────────────────────────────────┴───────────┴──────────────────────────
```

## Module Interaction Map

```
                        ┌─────────────────┐
                        │   sensors_ts.py │
                        │   Main Loop     │
                        └────────┬────────┘
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
                    ▼            ▼            ▼
            ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐
            │co2_sensor_ts │ │moisture_sensor │humidity from CO2  │
            │   Read Data  │ │     Read Data  │     Read Data     │
            └──────┬───────┘ └────────┬──────┘ └────────┬─────────┘
                   │                  │               │
                   └──────────┬───────┴───────────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │  alert_system.py    │
                    │  check_temperature()│
                    │  check_co2()        │
                    │  check_humidity()   │
                    │  check_moisture()   │
                    │  check_all()        │
                    │                     │
                    │ 📝 LOGGING HERE:   │
                    │  WARNING: Triggered │
                    │  INFO: Recovered    │
                    │  DEBUG: Suppressed  │
                    └──────────┬──────────┘
                               │
                    ┌──────────┴──────────┐
                    │ Has Alerts?        │
                    └──────────┬──────────┘
                               │
                    YES ────────┼──────── NO
                    │           │        │
                    ▼           │        ▼
        ┌─────────────────────┐ │  Continue
        │ email_notification  │ │  Looping
        │  send_alert()       │ │
        │  send_email()       │ │
        │  _send_message()    │ │
        │                     │ │
        │ 📝 LOGGING HERE:   │ │
        │  DEBUG: SMTP setup  │ │
        │  INFO: Sent ✅      │ │
        │  ERROR: Failed ❌   │ │
        └──────────┬──────────┘ │
                   │            │
                   ▼            │
          ┌──────────────────┐  │
          │ Gmail SMTP Server│  │
          │   Connection     │  │
          └──────────────────┘  │
                                │
                                ▼
                    [End of Alert Cycle]
```

## Key Logging Indicators

```
✅ GOOD:
  WARNING  Temperature alert triggered
  INFO     Alert cycle complete: 1 alert(s) to send
  INFO     ✅ Email sent successfully to X@Y.com
  INFO     📧 Alert email sent successfully

❌ BAD:
  ERROR    ❌ SMTP Authentication failed
  ERROR    ❌ SMTP error occurred
  ERROR    📧 Alert email FAILED
  ERROR    Error sending alert email

⚠️  NORMAL (Suppression):
  DEBUG    Temperature still elevated (at max alert limit 3)
  INFO     Alert cycle complete: 0 alert(s) to send

ℹ️  RECOVERY:
  INFO     Temperature recovered to safe level
  INFO     ✅ Email sent successfully
  INFO     📧 Alert email sent successfully (Alert Cleared)
```
