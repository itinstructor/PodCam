# Email Alert System - Logging Documentation Index

## 📋 Documentation Files

### Quick Start
- **[LOGGING_CHANGES_SUMMARY.md](LOGGING_CHANGES_SUMMARY.md)** ⭐ Start here!
  - Overview of all changes made
  - Which files were modified
  - Key features of new logging
  - Impact and compatibility

### Detailed Reference
- **[LOGGING_ENHANCEMENTS.md](LOGGING_ENHANCEMENTS.md)** 📚 Complete reference
  - Full breakdown of all logging additions
  - Log levels and when they're used
  - Troubleshooting guide for common issues
  - Monitoring command examples

### Quick Lookup
- **[ALERT_LOGGING_QUICK_REFERENCE.md](ALERT_LOGGING_QUICK_REFERENCE.md)** 🔍 Quick answers
  - What to look for in logs (success/failure)
  - Useful monitoring commands
  - Understanding alert states
  - Configuration checklist

### Real Examples
- **[EXAMPLE_LOG_OUTPUTS.md](EXAMPLE_LOG_OUTPUTS.md)** 📊 See it in action
  - 8 real-world scenarios
  - Actual log output examples
  - What to interpret from logs
  - Key log patterns table

## 📁 Modified Source Files

### Core Alert System
- **alert_system.py** ✅
  - Added logging for alert triggering
  - Logs for suppression at max limits
  - Logs for recovery detection
  - Overall alert cycle summary

- **sensors_ts.py** ✅
  - Enhanced alert email preparation logging
  - Success/failure notification
  - Real-time and interval-based alert tracking
  - Exception logging with stack traces

- **email_notification.py** ✅
  - SMTP connection attempt logging
  - TLS encryption logging
  - Authentication logging
  - Email transmission logging with subject

## 🎯 Use Cases

### I Want To... | Read This File
---|---
Understand what was changed | [LOGGING_CHANGES_SUMMARY.md](LOGGING_CHANGES_SUMMARY.md)
Monitor alerts in real-time | [ALERT_LOGGING_QUICK_REFERENCE.md](ALERT_LOGGING_QUICK_REFERENCE.md)
Debug email sending issues | [LOGGING_ENHANCEMENTS.md](LOGGING_ENHANCEMENTS.md)
See example log outputs | [EXAMPLE_LOG_OUTPUTS.md](EXAMPLE_LOG_OUTPUTS.md)
Find specific command | [ALERT_LOGGING_QUICK_REFERENCE.md](ALERT_LOGGING_QUICK_REFERENCE.md)

## 🚀 Getting Started

### 1. Review the Changes
Read [LOGGING_CHANGES_SUMMARY.md](LOGGING_CHANGES_SUMMARY.md) to understand what was added.

### 2. Monitor Your System
Use commands from [ALERT_LOGGING_QUICK_REFERENCE.md](ALERT_LOGGING_QUICK_REFERENCE.md) to watch your logs.

### 3. Compare with Examples
When you see logs, compare them with [EXAMPLE_LOG_OUTPUTS.md](EXAMPLE_LOG_OUTPUTS.md) to understand.

### 4. Debug Issues
If something goes wrong, use [LOGGING_ENHANCEMENTS.md](LOGGING_ENHANCEMENTS.md) for detailed troubleshooting.

## 📊 Log Levels Explained

| Level | Color | When Used | Example |
|-------|-------|-----------|---------|
| ERROR | Red | ❌ Failures that stop email | `SMTP Authentication failed` |
| WARNING | Yellow | ⚠️ Alert threshold exceeded | `Temperature alert triggered` |
| INFO | Green | ✅ Important success events | `Email sent successfully` |
| DEBUG | Gray | 📝 Detailed operational info | `Attempting SMTP connection` |

## 📍 Key Concepts

### Alert State Tracking
- **count**: How many times this alert has been sent (0-3)
- **max_cap**: Maximum alerts allowed per violation (usually 3)
- **active**: Whether this alert is currently violated
- **suppressed**: Alert is still active but won't send more emails

### Email Lifecycle
```
Alert Triggered → Check Dedup → Format Email → SMTP Connect → 
TLS Auth → Send → Success/Fail → Log Result
```

### Why 3 Alerts Max?
1. **First alert**: "Hey, something is wrong!"
2. **Second alert**: "It's still wrong"
3. **Third alert**: "Still wrong, we know"
4. **Ongoing**: "Still elevated" (suppressed, one recovery email when fixed)

This prevents email spam for prolonged violations while keeping you informed.

## 🔧 Configuration Files to Check

```bash
# Verify alert thresholds
cat alerts_config.py | grep TEMP_ALERT

# Check email settings
cat config.py | grep DEFAULT_

# Check if alerts enabled
cat alerts_config.py | grep ENABLED
```

## 📈 Monitoring Commands Cheatsheet

```bash
# Watch temperature alerts
tail -f /var/log/wncc_PodsInSpace/sensors.log | grep "Temperature alert"

# See all failures
tail -f /var/log/wncc_PodsInSpace/sensors.log | grep "FAILED\|❌"

# Monitor email sends
tail -f /var/log/wncc_PodsInSpace/sensors.log | grep "✅\|📧"

# Debug SMTP
grep "SMTP\|Authentication\|TLS" /var/log/wncc_PodsInSpace/email_notifications.log

# Count today's alerts
grep "$(date +%Y-%m-%d).*alert triggered" /var/log/wncc_PodsInSpace/sensors.log | wc -l

# Find recent failures
grep "FAILED" /var/log/wncc_PodsInSpace/sensors.log | tail -10
```

## ✅ Verification Checklist

- [ ] Read LOGGING_CHANGES_SUMMARY.md to understand changes
- [ ] Locate log files in /var/log/wncc_PodsInSpace/
- [ ] Run a test alert with alerts_test.py
- [ ] Monitor logs in real-time
- [ ] Check for any ERROR entries
- [ ] Verify emails received
- [ ] Read relevant example scenario in EXAMPLE_LOG_OUTPUTS.md
- [ ] Bookmark useful commands from ALERT_LOGGING_QUICK_REFERENCE.md

## 🐛 Troubleshooting Flow

```
Problem: Alerts not being sent

1. Check: Is alert being triggered?
   → Look for "WARNING" entries in sensors.log
   → See ALERT_LOGGING_QUICK_REFERENCE.md

2. Check: Did email send attempt occur?
   → Look for "Preparing to send alert email"
   → See LOGGING_ENHANCEMENTS.md

3. Check: Did email send succeed?
   → Look for "✅ Email sent successfully"
   → If not, see #4

4. Check: What error occurred?
   → Look for "❌" and ERROR entries
   → Match error to scenario in EXAMPLE_LOG_OUTPUTS.md
   → Follow troubleshooting steps in LOGGING_ENHANCEMENTS.md

5. Check: Is configuration correct?
   → Verify alerts_config.py thresholds
   → Verify config.py email settings
   → Use checklist in ALERT_LOGGING_QUICK_REFERENCE.md
```

## 📞 Support Resources

- **Local Files**: All documentation files in this directory
- **Alert Config**: [alerts_config.py](alerts_config.py)
- **Email Config**: [config.py](config.py)
- **Alert Code**: [alert_system.py](alert_system.py)
- **Test Tool**: [alerts_test.py](alerts_test.py)

## 📝 Related Documentation

- [ALERT_SYSTEM_SUMMARY.md](ALERT_SYSTEM_SUMMARY.md) - Alert system architecture
- [QUICK_START_ALERTS.md](QUICK_START_ALERTS.md) - Getting started with alerts
- [TESTING_ALERTS.md](TESTING_ALERTS.md) - How to test the alert system
- [alert_system.py](alert_system.py) - Source code (now with inline comments)

## 🎓 Learning Path

### Beginner
1. Read: [LOGGING_CHANGES_SUMMARY.md](LOGGING_CHANGES_SUMMARY.md)
2. Try: `tail -f /var/log/wncc_PodsInSpace/sensors.log`
3. Run: `python3 alerts_test.py`

### Intermediate
1. Read: [ALERT_LOGGING_QUICK_REFERENCE.md](ALERT_LOGGING_QUICK_REFERENCE.md)
2. Read: [EXAMPLE_LOG_OUTPUTS.md](EXAMPLE_LOG_OUTPUTS.md)
3. Try: Monitoring commands from section "Watch Temperature Alerts"

### Advanced
1. Read: [LOGGING_ENHANCEMENTS.md](LOGGING_ENHANCEMENTS.md)
2. Study: Source code changes in alert_system.py
3. Debug: Use grep commands to analyze historical logs

## 📅 Last Updated

- Files Created: January 11, 2026
- Documentation Version: 1.0
- Compatible With: alert_system.py, sensors_ts.py, email_notification.py

---

**Quick Help**: Not sure where to start? Read [LOGGING_CHANGES_SUMMARY.md](LOGGING_CHANGES_SUMMARY.md) first! ⭐
