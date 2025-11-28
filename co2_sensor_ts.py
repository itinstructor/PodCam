#!/usr/bin/env python3
import time

# pip install adafruit-circuitpython-scd4x requests
import board
import adafruit_scd4x
import time


class CO2Sensor:
    """Reader for SCD4x CO2 sensor via I2C."""

    def __init__(self):
        self.co2 = None
        self.temp_c = None
        self.temp_f = None
        self.humidity = None
        self.i2c = board.I2C()
        self.scd4x = adafruit_scd4x.SCD4X(self.i2c)
        print("Serial number:", [hex(i) for i in self.scd4x.serial_number])
        self.scd4x.start_periodic_measurement()
        print("Waiting for first measurement....")

    def read_sensors(self):
        """Read CO2, temperature (C, F), and humidity from the sensor. Returns tuple or None."""
        if self.scd4x.data_ready:
            self.co2 = self.scd4x.co2
            self.temp_c = self.scd4x.temperature
            self.temp_f = self.temp_c * 9 / 5 + 32

            self.humidity = self.scd4x.relative_humidity
        return self.co2, self.temp_f, self.humidity


def main():
    print("SCD4x CO2 Sensor Test")
    print("Press Ctrl+C to exit\n")
    sensor = CO2Sensor()


if __name__ == "__main__":
    main()
