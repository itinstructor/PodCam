## Temperature Alert System

This document explains how to set up and use the modular alert system for PodsInSpace sensors.

### Overview

The alert system monitors sensor readings (CO2, temperature, humidity, soil moisture) at the ThingSpeak interval (every 10 minutes by default) and sends email alerts when values exceed or fall below configured thresholds.

### Quick Start: Temperature Alerts

To enable temperature alerts (the most common use case):

1. **Edit `alerts_config.py`** and set:
   ```python
   TEMP_ALERT_ENABLED = True
   TEMP_ALERT_HIGH = 85      # Alert if temperature exceeds 85°F
   TEMP_ALERT_LOW = 70       # Alert if temperature drops below 70°F
   ```

2. **Restart the service:**
   ```bash
   sudo systemctl restart sensors-ts
   ```

3. **Check logs** to confirm:
   ```bash
   tail -f /var/log/wncc_PodsInSpace/sensors.log | grep -i alert
   ```

That's it! When temperature violations occur at the 10-minute interval, email alerts will be sent automatically.

### Configuration Options

All alert settings are in `alerts_config.py`:

#### Temperature Alerts
- `TEMP_ALERT_ENABLED` - Set to `True` to enable
- `TEMP_ALERT_HIGH` - Temperature upper threshold (°F)
- `TEMP_ALERT_LOW` - Temperature lower threshold (°F)

#### CO2 Alerts
- `CO2_ALERT_ENABLED` - Set to `True` to enable
- `CO2_ALERT_HIGH` - CO2 upper threshold (ppm)

#### Humidity Alerts
- `HUMIDITY_ALERT_ENABLED` - Set to `True` to enable
- `HUMIDITY_ALERT_HIGH` - Humidity upper threshold (%)
- `HUMIDITY_ALERT_LOW` - Humidity lower threshold (%)

#### Soil Moisture Alerts
- `MOISTURE_ALERT_ENABLED` - Set to `True` to enable
- `MOISTURE_ALERT_LOW` - Soil moisture lower threshold (%)

#### Alert Behavior
- `ALERT_REALTIME` - If `False` (default), alerts only check at ThingSpeak intervals
- `ALERT_DEDUP` - If `True` (default), prevents duplicate alerts for same threshold violation

### How It Works

1. **Reading Phase**: Every 30 seconds, the system reads sensors and collects readings
2. **Averaging Phase**: After 20 readings (10 minutes), values are averaged using trimmed mean
3. **Alert Check**: The alert system checks averaged values against thresholds
4. **Email Send**: If any threshold is violated, an alert email is sent to all configured recipients
5. **Reset**: Alert state is reset for the next cycle

### Example: Adding a New Alert Type

The modular design makes it easy to add new alerts. Here's how:

#### 1. Add Configuration in `alerts_config.py`
```python
# Soil pH Alert Thresholds
PH_ALERT_HIGH = 7.5        # Alert if pH exceeds this
PH_ALERT_LOW = 6.0         # Alert if pH drops below this
PH_ALERT_ENABLED = False   # Set to True to enable
```

#### 2. Add Check Method in `alert_system.py`
```python
def check_ph(self, ph_value):
    """Check pH against configured thresholds."""
    if not PH_ALERT_ENABLED or ph_value is None:
        return False, None

    alerts = []

    if ph_value > PH_ALERT_HIGH:
        alert_key = "ph_high"
        if not ALERT_DEDUP or not self.active_alerts.get(alert_key):
            alerts.append(f"🧪 HIGH pH: {ph_value:.2f} (threshold: {PH_ALERT_HIGH})")
            self.active_alerts[alert_key] = True
    else:
        self.active_alerts.pop("ph_high", None)

    if ph_value < PH_ALERT_LOW:
        alert_key = "ph_low"
        if not ALERT_DEDUP or not self.active_alerts.get(alert_key):
            alerts.append(f"🧪 LOW pH: {ph_value:.2f} (threshold: {PH_ALERT_LOW})")
            self.active_alerts[alert_key] = True
    else:
        self.active_alerts.pop("ph_low", None)

    if alerts:
        return True, " | ".join(alerts)
    return False, None
```

#### 3. Update `check_all` Method in `alert_system.py`
```python
def check_all(self, co2_ppm=None, temp_f=None, humidity_pct=None, moisture_pct=None, ph=None):
    """Check all enabled alerts and collect messages."""
    messages = []
    
    # ... existing checks ...
    
    ph_alert, ph_msg = self.check_ph(ph)
    if ph_alert:
        messages.append(ph_msg)
    
    return len(messages) > 0, messages
```

#### 4. Update `sensors_ts.py` Main Loop
```python
has_alerts, alert_messages = alert_system.check_all(
    co2_ppm=avg_co2,
    temp_f=avg_temp,
    humidity_pct=avg_humidity,
    moisture_pct=avg_moisture,
    ph=avg_ph,  # Add new sensor
)
```

### Monitoring Alerts

#### View Recent Alerts in Logs
```bash
grep "ALERT:" /var/log/wncc_PodsInSpace/sensors.log | tail -20
```

#### Disable Alerts Temporarily
```python
# In alerts_config.py
TEMP_ALERT_ENABLED = False
# Then restart: sudo systemctl restart sensors-ts
```

#### Change Thresholds
Edit `alerts_config.py` and update values, then restart the service:
```bash
sudo systemctl restart sensors-ts
```

### Email Recipients

Alerts are sent to all addresses in `config.py`:
```python
DEFAULT_RECIPIENT_EMAILS = [
    "williamaloring@gmail.com",
    "williamloring@hotmail.com",
    "sarah.trook31@gmail.com",
]
```

To add/remove recipients, edit this list and restart the service.

### Troubleshooting

**Q: Not receiving alert emails?**
- Check logs: `grep -i "alert\|email" /var/log/wncc_PodsInSpace/*.log`
- Verify recipients in `config.py`
- Confirm Gmail SMTP credentials
- Check network connectivity

**Q: Receiving too many alerts?**
- Increase threshold values in `alerts_config.py`
- Ensure `ALERT_DEDUP = True` to prevent duplicate alerts

**Q: Want alerts at different intervals?**
- Currently alerts only check at ThingSpeak interval (10 minutes)
- To change, modify `SENSOR_READ_INTERVAL` and `THINGSPEAK_INTERVAL` in `config.py`

### File Structure

```
PodCam/
├── alerts_config.py       ← Edit to configure thresholds
├── alert_system.py        ← Core alert logic (extend here for new types)
├── sensors_ts.py          ← Main service that uses alert_system
└── config.py              ← SMTP and recipient configuration
```

### Key Design Principles

1. **Modular**: Each sensor type has its own check method
2. **Configurable**: All thresholds in one file
3. **Deduplication**: Prevents alert spam for same violation
4. **Non-blocking**: Alerts don't interrupt sensor readings
5. **Easy to Extend**: Add new sensors with ~20 lines of code
