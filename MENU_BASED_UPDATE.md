# alerts_test.py Updated - Menu-Based Only

## What Changed

The `alerts_test.py` file has been simplified to use **menu-based interaction only**. All command-line argument parsing has been removed.

## How to Use

Simply run:
```bash
python3 alerts_test.py
```

That's it! You'll immediately see the menu with 13 options to choose from.

## Menu Options

```
1. Test Temperature High
2. Test Temperature Low
3. Test Temperature Custom
4. Test CO2 High
5. Test CO2 Custom
6. Test Humidity High
7. Test Humidity Low
8. Test Humidity Custom
9. Test Moisture Low
10. Test Moisture Custom
11. Test ALL Limits (No Email)
12. Test ALL Limits (With Email)
13. View Current Thresholds
0. Exit
```

## Old vs New

### Old Way (With Arguments) - ❌ No longer works
```bash
python3 test_alerts.py --high-temp        # ❌
python3 test_alerts.py --temp 87          # ❌
python3 test_alerts.py --all --send-email # ❌
```

### New Way (Menu-Based) - ✅ Use this now
```bash
python3 alerts_test.py
# Menu appears → Select option → Enter values if needed
```

## Benefits of Menu-Based Only

✅ **Simpler** - No complex command-line arguments to remember  
✅ **Cleaner** - Single entry point for all tests  
✅ **User-Friendly** - Guided prompts for each option  
✅ **Less Code** - Removed ~100 lines of argparse complexity  
✅ **Consistent** - Always the same way to use the tool  

## Example Usage Flow

```
$ python3 alerts_test.py

==============================================================
ALERT SYSTEM TEST MENU
==============================================================
1. Test Temperature High
2. Test Temperature Low
...
13. View Current Thresholds
0. Exit
==============================================================

Select option: 1

==============================================================
Testing Temperature Alert: 87°F
==============================================================
Configured thresholds: 70°F - 85°F
✓ ALERT TRIGGERED: 🌡️ HIGH TEMPERATURE: 87°F (threshold: 85°F)

Select option: 0
Exiting...
```

## Note

- The file is still called `alerts_test.py` (was in the repo with this name)
- There's also `test_alerts.py` which still has the old argument-based system if needed
- For this project, use `alerts_test.py` (menu-based) going forward
