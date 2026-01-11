#!/usr/bin/env python3
"""
REAL-WORLD TESTING EXAMPLES
===========================

Copy & paste examples for common testing scenarios
"""

EXAMPLES = """
EXAMPLE 1: Quick Verification (60 seconds)
============================================

You just set up alerts and want to verify they work.

$ python3 test_alerts.py --all

Expected Output:
1. HIGH TEMPERATURE TEST (87°F)
   ✓ ALERT TRIGGERED: 🌡️ HIGH TEMPERATURE: 87°F

2. LOW TEMPERATURE TEST (68°F)
   ✓ ALERT TRIGGERED: 🌡️ LOW TEMPERATURE: 68°F

3. HIGH CO2 TEST (1600 ppm)
   ✓ ALERT TRIGGERED: ⚠️ HIGH CO2: 1600 ppm

4. HIGH HUMIDITY TEST (90%)
   ✓ ALERT TRIGGERED: 💧 HIGH HUMIDITY: 90%

5. LOW HUMIDITY TEST (30%)
   ✓ ALERT TRIGGERED: 💧 LOW HUMIDITY: 30%

6. LOW MOISTURE TEST (15%)
   ✓ ALERT TRIGGERED: 🌱 LOW SOIL MOISTURE: 15%

Summary: 6 alerts triggered

✓ All working!


EXAMPLE 2: Email Verification (2 minutes)
===========================================

You want to make sure alerts actually send emails.

$ python3 test_alerts.py --high-temp --send-email

Expected Output:
==============================================================
Testing Temperature Alert: 87°F
==============================================================
Configured thresholds: 70°F - 85°F
✓ ALERT TRIGGERED: 🌡️ HIGH TEMPERATURE: 87°F (threshold: 85°F)

📧 Sending test email...
✓ Test email sent successfully!

Then:
1. Wait 5-10 seconds
2. Check your email inbox
3. Look for email from: wnccrobotics@gmail.com
4. Subject: "PodsInSpace Sensor Threshold Alert"
5. Body contains the alert details and current readings

✓ Email working!


EXAMPLE 3: After Configuration Change (2 minutes)
==================================================

You just changed temperature thresholds and want to verify.

Before:
$ nano alerts_config.py
# Changed: TEMP_ALERT_HIGH = 80 (was 85)

After:
$ python3 test_alerts.py --temp 81

Expected:
✓ ALERT TRIGGERED: 🌡️ HIGH TEMPERATURE: 81°F (threshold: 80°F)

Then test safe value:
$ python3 test_alerts.py --temp 78

Expected:
✗ No alert (within safe range)

✓ New threshold working!


EXAMPLE 4: Testing Custom Room Conditions (5 minutes)
======================================================

Your room is at 72°F, 65% humidity. You want to know if alerts
will trigger at your typical conditions.

$ python3 test_alerts.py --temp 72 --humidity 65

Expected:
✗ No alert (within safe range)  ← Both values are safe

What if humidity rises to 86%?
$ python3 test_alerts.py --humidity 86

Expected:
✓ ALERT TRIGGERED: 💧 HIGH HUMIDITY: 86%

✓ You know your system is safe at current conditions,
  but will alert if humidity gets too high.


EXAMPLE 5: Pre-Production Checklist (5 minutes)
================================================

Before going live, run this sequence:

Step 1: Verify all alerts work
$ python3 test_alerts.py --all

# Should see 6 ✓ ALERT TRIGGERED

Step 2: Verify email works
$ python3 test_alerts.py --all --send-email

# Should see ✓ Test email sent successfully!

Step 3: Check email received
# Look in inbox - should have email within 10 seconds

Step 4: Verify at actual thresholds
$ python3 test_alerts.py --temp 85        # At limit
$ python3 test_alerts.py --temp 85.1      # Above limit
$ python3 test_alerts.py --temp 70        # At limit
$ python3 test_alerts.py --temp 69.9      # Below limit

Expected: 85° shows ✗, 85.1° shows ✓, etc.

✓ Ready for production!


EXAMPLE 6: Troubleshooting Email Issues (5 minutes)
====================================================

Emails aren't arriving. Let's debug:

Step 1: Test alert triggers
$ python3 test_alerts.py --high-temp

Expected: ✓ ALERT TRIGGERED

Step 2: Check if email system works at all
$ python3 test_alerts.py --high-temp --send-email

Expected: ✓ Test email sent successfully!

Step 3: If email says "failed (may be deduped)"
$ rm logs/email_send_state.json
$ python3 test_alerts.py --high-temp --send-email

Expected: Now ✓ Test email sent successfully!

Step 4: If still failing, check config
$ grep DEFAULT_RECIPIENT_EMAILS config.py

# Verify email addresses are correct

Step 5: Check if SMTP working
$ python3 << 'EOF'
from email_notification import EmailNotifier
e = EmailNotifier()
print(f"Sender: {e.sender_email}")
print(f"SMTP: {e.smtp_server}:{e.smtp_port}")
EOF

# Verify gmail.com and port 587

✓ Most issues fixed by clearing state file:
  rm logs/email_send_state.json


EXAMPLE 7: Continuous Testing During Development (30 seconds)
==============================================================

You're modifying the alert system and want to quickly verify
your changes work.

$ python3 test_alerts.py --temp 87

Edit alert_system.py...

$ python3 test_alerts.py --temp 87

Check if output changed as expected.

$ python3 test_alerts.py --all

Verify all sensors still work.

No need to restart service or wait for sensor cycles!


EXAMPLE 8: Testing Multiple Scenarios in Sequence
==================================================

Script to test several conditions automatically:

#!/bin/bash
# save as test_sequence.sh

cd /path/to/PodCam

echo "=== Test 1: High Temp ==="
python3 test_alerts.py --temp 87
sleep 1

echo "=== Test 2: Low Temp ==="
python3 test_alerts.py --temp 68
sleep 1

echo "=== Test 3: High Humidity ==="
python3 test_alerts.py --humidity 88
sleep 1

echo "=== Test 4: Low Moisture ==="
python3 test_alerts.py --moisture 15
sleep 1

echo "=== Test 5: All at Limits ==="
python3 test_alerts.py --all
sleep 1

echo "=== All tests complete ==="

$ chmod +x test_sequence.sh
$ ./test_sequence.sh


EXAMPLE 9: Interactive Testing When Unsure
===========================================

You're not sure what thresholds are set, so you use interactive mode:

$ python3 test_alerts.py

Menu appears:
==============================================================
ALERT SYSTEM TEST MENU
==============================================================
1. Test Temperature High
2. Test Temperature Low
...
13. View Current Thresholds
0. Exit

Select option: 13

Output:
==============================================================
CURRENT ALERT THRESHOLDS
==============================================================
Temperature:  70°F - 85°F
CO2:          > 1500 ppm
Humidity:     35% - 85%
Moisture:     < 20%
==============================================================

Now you know the limits!

Select option: 1
✓ ALERT TRIGGERED: HIGH TEMPERATURE: 87°F

✓ Everything clear!


EXAMPLE 10: Real-World Debugging
=================================

Production: Service is running, temperature hits 88°F, but no email sent.

Debug session:
$ python3 test_alerts.py --temp 88

Expected: ✓ ALERT TRIGGERED

Result: ✗ No alert (within safe range)

Hmm, 88°F should trigger! Check config:
$ grep TEMP_ALERT /alerts_config.py

Found: TEMP_ALERT_ENABLED = False

Fix:
$ sed -i 's/TEMP_ALERT_ENABLED = False/TEMP_ALERT_ENABLED = True/' alerts_config.py

Verify:
$ python3 test_alerts.py --temp 88

Result: ✓ ALERT TRIGGERED

Restart service:
$ sudo systemctl restart sensors-ts

✓ Fixed! Emails will now send when temp exceeds 85°F.
"""

PERFORMANCE = """
PERFORMANCE NOTES
=================

Test Execution Times (approximate):

Single test (--temp 87):          < 100ms
All limits test (--all):          < 500ms
With email send:                  2-5 seconds
Interactive menu (first prompt):  < 200ms

No impact on running service:
- Tests run independently
- Use same config/modules but don't interfere
- Multiple tests can run simultaneously
- Can test while service is acquiring data
"""

TIPS = """
PRO TIPS & TRICKS
=================

Tip 1: Quick Test After Config Change
--------------------------------------
1. Edit alerts_config.py
2. Run: python3 test_alerts.py --all
3. Verify changes instantly (no restart needed)
4. If good, restart service: sudo systemctl restart sensors-ts

Tip 2: Email State Management
------------------------------
If test email is "deduped":
  rm logs/email_send_state.json
  python3 test_alerts.py --high-temp --send-email

Tip 3: Batch Testing
--------------------
Test multiple values in sequence:
  for t in 68 72 80 85 87; do
    echo "Testing $t°F:"
    python3 test_alerts.py --temp $t
  done

Tip 4: Grep Log Results
-----------------------
Check all tests from logs:
  grep "Testing\|ALERT" /var/log/wncc_PodsInSpace/sensors.log | tail -30

Tip 5: Combining Test with Monitoring
--------------------------------------
In one terminal:
  tail -f /var/log/wncc_PodsInSpace/sensors.log | grep -E "ALERT|Alert"

In another:
  python3 test_alerts.py --all

See live feedback!

Tip 6: Custom Threshold Testing
--------------------------------
After changing TEMP_ALERT_HIGH to 80:
  python3 test_alerts.py --temp 80   # At limit → ✗
  python3 test_alerts.py --temp 80.1 # Above → ✓

This verifies exactly where threshold is.

Tip 7: Email Template Testing
------------------------------
Want to verify email format looks good?
  python3 test_alerts.py --high-temp --send-email
  # Check received email in your inbox
  # Verify formatting, subject, recipient list all correct

Tip 8: Headless/Remote Testing
-------------------------------
Via SSH on Raspberry Pi:
  ssh user@raspberrypi
  cd /path/to/PodCam
  python3 test_alerts.py --all
  # See results immediately in terminal
"""

print(__doc__)
print(EXAMPLES)
print(PERFORMANCE)
print(TIPS)

if __name__ == "__main__":
    print("\nTo run tests, use:")
    print("  python3 test_alerts.py --help")
    print("  python3 test_alerts.py --all")
    print("  python3 test_alerts.py --temp 87")
    print("  python3 test_alerts.py -i")
