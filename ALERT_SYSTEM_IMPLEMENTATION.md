## Alert System Implementation Summary

### What Was Added

A modular, configurable alert system that sends email alerts when sensor readings exceed or fall below specified thresholds. Alerts are checked at the ThingSpeak interval (10 minutes) to match the sensor averaging period.

### Files Created

1. **`alerts_config.py`** - Configuration file for all alert thresholds
   - Temperature, CO2, humidity, and moisture alert settings
   - Easy to enable/disable individual alert types
   - All in one place for centralized management

2. **`alert_system.py`** - Core alert system with AlertSystem class
   - Modular check methods for each sensor type
   - Built-in deduplication to prevent alert spam
   - Easy-to-extend design for adding new alert types

3. **`ALERT_SYSTEM.md`** - Complete documentation
   - Quick start guide for temperature alerts
   - Configuration reference
   - Instructions for extending with new alert types
   - Troubleshooting tips

### Files Modified

**`sensors_ts.py`**
- Added import of alert system
- Added alert check after ThingSpeak data send
- Integrated email notification for violations
- Resets alert state after sending

### Quick Setup

To enable temperature alerts (85°F high, 70°F low):

```python
# Edit alerts_config.py
TEMP_ALERT_ENABLED = True
TEMP_ALERT_HIGH = 85
TEMP_ALERT_LOW = 70
```

Then restart:
```bash
sudo systemctl restart sensors-ts
```

### Key Features

✅ **Modular Design** - Easy to add more alert types
✅ **Configurable** - All thresholds in one file  
✅ **Smart Deduplication** - Prevents duplicate alerts
✅ **ThingSpeak Aligned** - Checks at 10-minute interval with averaged data
✅ **Email Integrated** - Uses existing email notification system
✅ **Non-Blocking** - Alerts don't interrupt sensor readings
✅ **Logging** - Full audit trail in system logs

### Example: Adding a New Alert Type

To add a new sensor type (e.g., soil pH):

1. Add config in `alerts_config.py`:
```python
PH_ALERT_HIGH = 7.5
PH_ALERT_LOW = 6.0
PH_ALERT_ENABLED = False
```

2. Add method in `alert_system.py`:
```python
def check_ph(self, ph_value):
    # Check logic similar to temperature
```

3. Call in `check_all()` method

4. Pass to alert check in `sensors_ts.py`

That's it! The system is designed to scale.

### Architecture

```
Sensor Readings (30s interval)
           ↓
    Collect 20 readings
           ↓
    Calculate averages (trimmed mean)
           ↓
    Send to ThingSpeak
           ↓
    alert_system.check_all()
           ↓
    If violations found:
      - Log alert
      - Format email
      - Send email
      - Reset state
           ↓
    Start next cycle
```

### Testing

To test alerts without waiting 10 minutes:

1. Temporarily lower thresholds:
```python
TEMP_ALERT_HIGH = 75  # Current room temp
TEMP_ALERT_LOW = 60
```

2. Wait for next averaging cycle (10 minutes)

3. Check logs:
```bash
grep ALERT /var/log/wncc_PodsInSpace/sensors.log
```

4. Restore original thresholds

### Default Configuration

- **Temperature**: Alert if > 85°F or < 70°F (ENABLED)
- **CO2**: Alert if > 1500 ppm (DISABLED)
- **Humidity**: Alert if > 85% or < 35% (DISABLED)  
- **Moisture**: Alert if < 20% (DISABLED)

See `alerts_config.py` to customize.
