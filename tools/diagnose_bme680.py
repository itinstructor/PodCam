#!/usr/bin/env python3
"""
BME680 Diagnostic Tool
Tests I2C connection and attempts to detect BME680 sensor
"""

import sys
import subprocess

def run_command(cmd):
    """Run a shell command and return output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), 1

def check_i2c_tools():
    """Check if i2c-tools is installed."""
    print("=" * 60)
    print("1. Checking for i2c-tools...")
    print("=" * 60)
    stdout, stderr, code = run_command("which i2cdetect")
    if code == 0:
        print("✓ i2c-tools is installed")
        return True
    else:
        print("✗ i2c-tools is NOT installed")
        print("  Install with: sudo apt-get install -y i2c-tools")
        return False

def scan_i2c_bus():
    """Scan I2C bus for devices."""
    print("\n" + "=" * 60)
    print("2. Scanning I2C bus 1 for devices...")
    print("=" * 60)
    stdout, stderr, code = run_command("i2cdetect -y 1")
    if code == 0:
        print(stdout)
        if "76" in stdout:
            print("✓ Device found at address 0x76 (BME680 PRIMARY)")
        elif "77" in stdout:
            print("✓ Device found at address 0x77 (BME680 SECONDARY)")
        else:
            print("✗ No device found at 0x76 or 0x77")
        return stdout
    else:
        print(f"✗ Error scanning I2C bus: {stderr}")
        return None

def test_bme680_primary():
    """Test BME680 at primary address (0x76)."""
    print("\n" + "=" * 60)
    print("3. Testing BME680 at PRIMARY address (0x76)...")
    print("=" * 60)
    try:
        import bme680
        sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)
        print(f"✓ BME680 detected at 0x76")
        print(f"  Chip ID: 0x{sensor.chip_id:02x}")
        return True
    except Exception as e:
        print(f"✗ Failed to connect at 0x76: {e}")
        return False

def test_bme680_secondary():
    """Test BME680 at secondary address (0x77)."""
    print("\n" + "=" * 60)
    print("4. Testing BME680 at SECONDARY address (0x77)...")
    print("=" * 60)
    try:
        import bme680
        sensor = bme680.BME680(bme680.I2C_ADDR_SECONDARY)
        print(f"✓ BME680 detected at 0x77")
        print(f"  Chip ID: 0x{sensor.chip_id:02x}")
        return True
    except Exception as e:
        print(f"✗ Failed to connect at 0x77: {e}")
        return False

def check_i2c_speed():
    """Check I2C bus speed."""
    print("\n" + "=" * 60)
    print("5. Checking I2C bus speed...")
    print("=" * 60)
    stdout, stderr, code = run_command("grep 'i2c_arm_baudrate' /boot/config.txt")
    if "i2c_arm_baudrate" in stdout:
        print(f"I2C speed setting found: {stdout.strip()}")
    else:
        print("No custom I2C speed set (using default 100kHz)")
        print("If you have connection issues, try reducing speed:")
        print("  sudo nano /boot/config.txt")
        print("  Add: dtparam=i2c_arm_baudrate=10000")

def check_permissions():
    """Check if user has I2C permissions."""
    print("\n" + "=" * 60)
    print("6. Checking I2C permissions...")
    print("=" * 60)
    stdout, stderr, code = run_command("groups")
    if "i2c" in stdout:
        print("✓ User is in i2c group")
    else:
        print("✗ User is NOT in i2c group")
        print("  Add user to group: sudo usermod -a -G i2c $USER")
        print("  Then logout and login again")

def main():
    """Run all diagnostic checks."""
    print("\n" + "=" * 60)
    print("BME680 SENSOR DIAGNOSTIC TOOL")
    print("=" * 60 + "\n")
    
    # Check prerequisites
    has_i2c_tools = check_i2c_tools()
    
    # Scan bus if tools available
    if has_i2c_tools:
        i2c_scan = scan_i2c_bus()
    
    # Try to import bme680 library
    try:
        import bme680
        print("\n✓ bme680 Python library is installed")
    except ImportError:
        print("\n✗ bme680 Python library is NOT installed")
        print("  Install with: pip install bme680")
        return
    
    # Test both possible addresses
    primary_ok = test_bme680_primary()
    secondary_ok = test_bme680_secondary()
    
    # Check I2C configuration
    check_i2c_speed()
    check_permissions()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    if primary_ok:
        print("✓ BME680 is working at PRIMARY address (0x76)")
    elif secondary_ok:
        print("✓ BME680 is working at SECONDARY address (0x77)")
        print("  You need to update your code to use I2C_ADDR_SECONDARY")
    else:
        print("✗ BME680 sensor not detected")
        print("\nPossible issues:")
        print("  1. Sensor not connected properly (check wiring)")
        print("  2. I2C not enabled (run: sudo raspi-config)")
        print("  3. Wrong I2C bus (try bus 0 instead of 1)")
        print("  4. Faulty sensor or connection")
        print("  5. Power issue (check 3.3V supply)")

if __name__ == "__main__":
    main()
