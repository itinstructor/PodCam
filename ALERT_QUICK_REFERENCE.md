# Alert System Quick Reference Card

## Enable Temperature Alerts (3-line edit)

```python
# File: alerts_config.py
TEMP_ALERT_ENABLED = True
TEMP_ALERT_HIGH = 85   # Change this to your threshold
TEMP_ALERT_LOW = 70    # Change this to your threshold
```

Save, then: `sudo systemctl restart sensors-ts`

---

## Alert Thresholds Cheat Sheet

```python
# Temperature (°F)
TEMP_ALERT_HIGH = 85       # Default
TEMP_ALERT_LOW = 70        # Default

# CO2 (ppm)
CO2_ALERT_HIGH = 1500      # Default

# Humidity (%)
HUMIDITY_ALERT_HIGH = 85   # Default
HUMIDITY_ALERT_LOW = 35    # Default

# Soil Moisture (%)
MOISTURE_ALERT_LOW = 20    # Default
```

---

## Enable/Disable Alerts

```python
# Just change one line to enable/disable each sensor:
TEMP_ALERT_ENABLED = True      # Temperature ON
CO2_ALERT_ENABLED = False      # CO2 OFF
HUMIDITY_ALERT_ENABLED = False # Humidity OFF
MOISTURE_ALERT_ENABLED = False # Moisture OFF
```

---

## Common Thresholds by Plant Type

```python
# ===== GENERAL CROPS =====
TEMP_ALERT_HIGH = 85
TEMP_ALERT_LOW = 70
HUMIDITY_ALERT_HIGH = 75
HUMIDITY_ALERT_LOW = 40

# ===== TROPICAL PLANTS =====
TEMP_ALERT_HIGH = 90
TEMP_ALERT_LOW = 75
HUMIDITY_ALERT_HIGH = 85
HUMIDITY_ALERT_LOW = 60

# ===== COOL CLIMATE CROPS =====
TEMP_ALERT_HIGH = 75
TEMP_ALERT_LOW = 55
HUMIDITY_ALERT_HIGH = 70
HUMIDITY_ALERT_LOW = 45

# ===== DROUGHT RESISTANT =====
TEMP_ALERT_HIGH = 95
TEMP_ALERT_LOW = 50
MOISTURE_ALERT_LOW = 15
```

---

## Monitoring Commands

```bash
# See current readings
tail -20 /var/log/wncc_PodsInSpace/sensors.log | grep "Avg "

# See alerts sent
grep "ALERT:" /var/log/wncc_PodsInSpace/sensors.log

# See email status
grep "Alert email" /var/log/wncc_PodsInSpace/sensors.log

# See last N alerts
grep "ALERT:" /var/log/wncc_PodsInSpace/sensors.log | tail -10

# Watch logs in real-time
tail -f /var/log/wncc_PodsInSpace/sensors.log | grep -E "ALERT|Avg|email"
```

---

## Quick Restart After Changes

```bash
# 1. Edit config
nano alerts_config.py

# 2. Save (Ctrl+X, Y, Enter)

# 3. Restart service
sudo systemctl restart sensors-ts

# 4. Check it worked
grep "ALERT" /var/log/wncc_PodsInSpace/sensors.log | tail -1
```

---

## Testing (Without Waiting 10 Minutes)

### Quick Test in Python:
```bash
python3 << 'EOF'
from alert_system import AlertSystem
alert = AlertSystem()
triggered, msg = alert.check_temperature(87)
print(f"Alert: {triggered}")
print(f"Message: {msg}")
EOF
```

### Temporary Test Threshold:
```python
# In alerts_config.py - temporarily lower threshold
TEMP_ALERT_HIGH = 72  # If room is 70°F, this triggers
# Wait 10 min, check logs
# Then restore: TEMP_ALERT_HIGH = 85
```

---

## Adding New Alert Type (5 Steps)

### 1. Add config option
```python
# In alerts_config.py
PRESSURE_ALERT_ENABLED = False
PRESSURE_ALERT_HIGH = 50  # psi
```

### 2. Add check method
```python
# In alert_system.py - add to AlertSystem class
def check_pressure(self, psi):
    if not PRESSURE_ALERT_ENABLED or psi is None:
        return False, None
    if psi > PRESSURE_ALERT_HIGH:
        msg = f"⚠️ HIGH PRESSURE: {psi} psi"
        return True, msg
    return False, None
```

### 3. Update check_all()
```python
# In alert_system.py - add to check_all method
pressure_alert, pressure_msg = self.check_pressure(pressure)
if pressure_alert:
    messages.append(pressure_msg)
```

### 4. Call in sensors_ts.py
```python
has_alerts, alert_messages = alert_system.check_all(
    temp_f=avg_temp,
    pressure=avg_pressure  # Add here
)
```

### 5. Restart
```bash
sudo systemctl restart sensors-ts
```

---

## Deduplication Examples

```
Cycle 1: Temp 87°F > 85°F → Alert email sent ✓
Cycle 2: Temp 86°F > 85°F → NO email (dedup prevents spam)
Cycle 3: Temp 84°F < 85°F → Cleared, ready again
Cycle 4: Temp 88°F > 85°F → NEW alert sent ✓
```

Prevent this by setting:
```python
ALERT_DEDUP = True  # Keep this True
```

---

## Troubleshooting One-Liners

```bash
# Check if service running
sudo systemctl status sensors-ts

# See if alerts triggering
grep "ALERT:" /var/log/wncc_PodsInSpace/sensors.log | wc -l

# Check last sensor reading
grep "Avg Temperature" /var/log/wncc_PodsInSpace/sensors.log | tail -1

# See email errors
grep -i "error" /var/log/wncc_PodsInSpace/email.log | tail -5

# Restart service
sudo systemctl restart sensors-ts

# View entire log
less /var/log/wncc_PodsInSpace/sensors.log

# Follow log in real-time
tail -f /var/log/wncc_PodsInSpace/sensors.log
```

---

## Email Recipients

To change who gets alerts:

```python
# In config.py
DEFAULT_RECIPIENT_EMAILS = [
    "email1@gmail.com",
    "email2@gmail.com",
    "email3@gmail.com",
]
```

Then: `sudo systemctl restart sensors-ts`

---

## System Check

```bash
# Run this after setup to verify everything works:

echo "=== Service Status ==="
sudo systemctl status sensors-ts | head -5

echo "=== Recent Readings ==="
grep "Avg Temperature" /var/log/wncc_PodsInSpace/sensors.log | tail -3

echo "=== Alerts Configured ==="
grep "ALERT_ENABLED" alerts_config.py

echo "=== Email Configuration ==="
grep -E "SMTP|EMAIL" config.py | head -3
```

---

## File Locations

```
Project Root:
├── alerts_config.py          ← EDIT: Thresholds
├── alert_system.py           ← Core logic (don't edit usually)
├── sensors_ts.py             ← Integration (don't edit usually)
├── QUICK_START_ALERTS.md     ← Start here
├── ALERT_SYSTEM.md           ← Full documentation
├── ALERT_EXAMPLES.py         ← Configuration examples
└── ALERT_WORKFLOW.py         ← Testing guide

Logs:
├── /var/log/wncc_PodsInSpace/sensors.log
└── logs/email_send_state.json (dedup tracking)
```

---

## One-Command Setup

```bash
# Copy this, paste in terminal:
cat > ~/setup_alerts.sh << 'EOF'
#!/bin/bash
cd /path/to/PodCam
echo "Enabling temperature alerts..."
sed -i 's/TEMP_ALERT_ENABLED = False/TEMP_ALERT_ENABLED = True/' alerts_config.py
sudo systemctl restart sensors-ts
echo "Alerts enabled! Checking status..."
grep "Avg Temperature" /var/log/wncc_PodsInSpace/sensors.log | tail -1
EOF

chmod +x ~/setup_alerts.sh
~/setup_alerts.sh
```

---

## Remember

- ✅ Edit `alerts_config.py`
- ✅ Run `sudo systemctl restart sensors-ts`
- ✅ Wait 10 minutes
- ✅ Check logs: `grep ALERT /var/log/wncc_PodsInSpace/sensors.log`
- ✅ Check email inbox

**That's it!** The system handles the rest automatically.
