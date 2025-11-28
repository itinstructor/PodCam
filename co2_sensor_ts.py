#!/usr/bin/env python3
import time

# pip install adafruit-circuitpython-scd4x requests
import board
import adafruit_scd4x
import requests
import time
from api_key_ts import THINGSPEAK_API_KEY, THINGSPEAK_URL


class Co2SensorReader:
    """Reader for SCD4x CO2 sensor via I2C."""

    def __init__(self):
        self.i2c = board.I2C()
        self.scd4x = adafruit_scd4x.SCD4X(self.i2c)
        print("Serial number:", [hex(i) for i in self.scd4x.serial_number])
        self.scd4x.start_periodic_measurement()
        print("Waiting for first measurement....")

    def read_data(self):
        """Read CO2, temperature (C, F), and humidity from the sensor. Returns tuple or None."""
        if self.scd4x.data_ready:
            self.temp_c = self.scd4x.temperature
            self.temp_f = self.temp_c * 9 / 5 + 32
            self.co2 = self.scd4x.CO2
            self.humidity = self.scd4x.relative_humidity

    def send_to_thingspeak(self):
        payload = {
            "api_key": THINGSPEAK_API_KEY,
            "field1": self.avg_co2,
            "field2": self.avg_temp_c,
            "field3": self.avg_humidity,
        }
        try:
            response = requests.post(THINGSPEAK_URL, data=payload, timeout=10)
            print(f"ThingSpeak response: {response.text}")
        except Exception as e:
            print(f"Error sending to ThingSpeak: {e}")

    def read_data_averaged(self, interval=30, avg_window=10 * 60):
        """Read sensor data every `interval` seconds, average over `avg_window` seconds, and send to ThingSpeak."""
        readings = []
        readings_needed = avg_window // interval

        data = self.read_data()
        
        co2, temp_c, temp_f, humidity = data
        readings.append((co2, temp_c, humidity))
        # print(
        #     f"CO2: {co2} ppm, Temp: {temp_c:.1f} C, Humidity: {humidity:.1f}%"
        # )
    
        if len(readings) >= readings_needed:
            # Compute averages
            self.avg_co2 = sum(r[0] for r in readings) / len(readings)
            self.avg_temp_c = sum(r[1] for r in readings) / len(readings)
            self.avg_humidity = sum(r[2] for r in readings) / len(readings)
            self.send_to_thingspeak()
            readings.clear()

        time.sleep(interval)


def main():
    print("SCD4x CO2 Sensor Test")
    print("Press Ctrl+C to exit\n")
    sensor = Co2SensorReader()
    sensor.read_data_averaged(interval=30, avg_window=10 * 60)


if __name__ == "__main__":
    main()
