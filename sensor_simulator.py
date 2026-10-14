

import csv
import math
import os
import random
import time
from collections import deque
from datetime import datetime

# PROJECT SENTINEL SETTINGS
READINGS_FILE = "sentinel_readings.csv"
ALERTS_FILE = "sentinel_alerts.csv"

SAMPLE_INTERVAL = 2
WINDOW_SIZE = 5

TEMP_WARNING = 70
TEMP_CRITICAL = 85

VIBRATION_WARNING = 3
VIBRATION_CRITICAL = 5

READING_FIELDS = [
    "time",
    "temperature",
    "vibration",
    "pressure",
    "power",
    "status",
]

ALERT_FIELDS = [
    "time",
    "severity",
    "message",
    "temperature",
    "vibration",
    "pressure",
    "power",
]


def current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def generate_sensor_reading():
    """Generate simulated sensor data."""
    temperature = random.gauss(55, 2)
    vibration = random.gauss(2.0, 0.25)
    pressure = random.gauss(40, 1.5)
    power = random.gauss(1.5, 0.1)

    event = random.random()

    if event < 0.05:
        temperature += random.uniform(15, 25)
    elif event < 0.10:
        vibration += random.uniform(2, 4)

    return {
        "time": current_time(),
        "temperature": round(temperature, 2),
        "vibration": round(max(0, vibration), 2),
        "pressure": round(max(0, pressure), 2),
        "power": round(max(0, power), 2),
    }


def validate_reading(reading):
    """Reject readings containing invalid numbers or impossible values."""
    limits = {
        "temperature": (-40, 150),
        "vibration": (0, 100),
        "pressure": (0, 200),
        "power": (0, 100),
    }

    for sensor, (minimum, maximum) in limits.items():
        value = reading.get(sensor)

        if not isinstance(value, (int, float)):
            return False

        if not math.isfinite(value):
            return False

        if not minimum <= value <= maximum:
            return False

    return True


def analyze_reading(reading):
    """Return alert severity and messages for a reading."""
    alerts = []
    critical = False

    temperature = reading["temperature"]
    vibration = reading["vibration"]

    if temperature >= TEMP_CRITICAL:
        alerts.append("CRITICAL TEMPERATURE")
        critical = True
    elif temperature > TEMP_WARNING:
        alerts.append("HIGH TEMPERATURE")

    if vibration >= VIBRATION_CRITICAL:
        alerts.append("CRITICAL VIBRATION")
        critical = True
    elif vibration > VIBRATION_WARNING:
        alerts.append("HIGH VIBRATION")

    if critical:
        severity = "CRITICAL"
    elif alerts:
        severity = "WARNING"
    else:
        severity = "NORMAL"

    return severity, alerts


def detect_trend(recent_readings):
    """Detect consecutive increases in temperature or vibration."""
    if len(recent_readings) < 5:
        return []

    alerts = []

    temperatures = [
        reading["temperature"] for reading in recent_readings
    ]
    vibrations = [
        reading["vibration"] for reading in recent_readings
    ]

    if all(
        temperatures[i] > temperatures[i - 1]
        for i in range(1, len(temperatures))
    ):
        alerts.append("RISING TEMPERATURE TREND")

    if all(
        vibrations[i] > vibrations[i - 1]
        for i in range(1, len(vibrations))
    ):
        alerts.append("RISING VIBRATION TREND")

    return alerts

def detect_spike(reading, recent_readings):
    """Detect sudden jumps compared with the previous five readings."""
    if len(recent_readings) < 5:
        return []

    alerts = []
    previous = list(recent_readings)[-5:]

    avg_temperature = sum(
        r["temperature"] for r in previous
    ) / len(previous)

    avg_vibration = sum(
        r["vibration"] for r in previous
    ) / len(previous)

    if reading["temperature"] - avg_temperature >= 8:
        alerts.append("SUDDEN TEMPERATURE SPIKE")

    if reading["vibration"] - avg_vibration >= 2:
        alerts.append("SUDDEN VIBRATION SPIKE")

    return alerts

def prepare_csv(filename, fields):
    """Open a CSV for appending and add headers if needed."""
    needs_header = (
        not os.path.exists(filename)
        or os.path.getsize(filename) == 0
    )

    file = open(filename, "a", newline="", encoding="utf-8")
    writer = csv.DictWriter(file, fieldnames=fields)

    if needs_header:
        writer.writeheader()
        file.flush()

    return file, writer


def clear_screen():
    """Refresh the terminal dashboard."""
    print("\033[2J\033[H", end="")


def display_dashboard(
    reading,
    status,
    recent_readings,
    total_readings,
    warning_count,
    critical_count,
    last_alert,
    start_time,
):
    clear_screen()

    avg_temp = sum(
        item["temperature"] for item in recent_readings
    ) / len(recent_readings)

    avg_vibration = sum(
        item["vibration"] for item in recent_readings
    ) / len(recent_readings)

    elapsed = int(time.time() - start_time)
    minutes, seconds = divmod(elapsed, 60)

    print("=" * 64)
    print("                 PROJECT SENTINEL")
    print("             LIVE SENSOR DASHBOARD")
    print("=" * 64)

    print(f"Timestamp:       {reading['time']}")
    print(f"Monitoring time: {minutes}m {seconds}s")
    print(f"Reading number:  {total_readings}")
    print("-" * 64)

    print("CURRENT SENSOR READINGS")
    print(f"Temperature: {reading['temperature']:>8.2f}")
    print(f"Vibration:   {reading['vibration']:>8.2f}")
    print(f"Pressure:    {reading['pressure']:>8.2f}")
    print(f"Power:       {reading['power']:>8.2f}")

    print("-" * 64)
    print(f"CURRENT STATUS: {status}")
    print(f"Warnings this session: {warning_count}")
    print(f"Critical alerts:       {critical_count}")

    print("-" * 64)
    print(f"Last {len(recent_readings)} reading(s) average:")
    print(f"Temperature average: {avg_temp:.2f}")
    print(f"Vibration average:   {avg_vibration:.2f}")

    print("-" * 64)
    print("MOST RECENT ALERT")
    print(last_alert if last_alert else "No alerts recorded yet.")

    print("-" * 64)
    print(f"Readings saved to: {READINGS_FILE}")
    print(f"Alerts saved to:   {ALERTS_FILE}")
    print("Refresh interval:  2 seconds")
    print("Press Control+C to stop monitoring.")
    print("=" * 64)


def display_summary(
    total_readings,
    warning_count,
    critical_count,
    all_readings,
    start_time,
):
    elapsed = int(time.time() - start_time)

    print("\n")
    print("=" * 50)
    print("       PROJECT SENTINEL SESSION SUMMARY")
    print("=" * 50)
    print(f"Total readings:   {total_readings}")
    print(f"Warning readings: {warning_count}")
    print(f"Critical alerts:  {critical_count}")
    print(f"Runtime:          {elapsed} seconds")

    if all_readings:
        print(
            "Average temperature: "
            f"{all_readings['temperature'] / total_readings:.2f}"
        )
        print(
            "Average vibration:   "
            f"{all_readings['vibration'] / total_readings:.2f}"
        )
        print(
            "Average pressure:    "
            f"{all_readings['pressure'] / total_readings:.2f}"
        )
        print(
            "Average power:        "
            f"{all_readings['power'] / total_readings:.2f}"
        )

    print(f"\nSensor history: {READINGS_FILE}")
    print(f"Alert history:  {ALERTS_FILE}")
    print("Your CSV history has been preserved.")
    print("=" * 50)

def test_critical_alert():
    print("\nPROJECT SENTINEL — CRITICAL ALERT SELF-TEST")
    print("-" * 45)

    test_reading = {
        "time": current_time(),
        "temperature": 90.0,
        "vibration": 6.0,
        "pressure": 40.0,
        "power": 1.5,
    }

    severity, messages = analyze_reading(test_reading)

    print("Test temperature:", test_reading["temperature"])
    print("Test vibration:", test_reading["vibration"])
    print("Expected severity: CRITICAL")
    print("Actual severity:", severity)
    print("Detected alerts:", ", ".join(messages))

    if severity == "CRITICAL":
        print("SELF-TEST PASSED: Critical detection works.")
    else:
        print("SELF-TEST FAILED: Check the alert thresholds.")

    print("-" * 45)
def main():
    recent_readings = deque(maxlen=WINDOW_SIZE)

    total_readings = 0
    warning_count = 0
    critical_count = 0

    totals = {
        "temperature": 0.0,
        "vibration": 0.0,
        "pressure": 0.0,
        "power": 0.0,
    }

    last_alert = ""
    start_time = time.time()

    readings_file = None
    alerts_file = None

    try:
        readings_file, readings_writer = prepare_csv(
            READINGS_FILE, READING_FIELDS
        )

        alerts_file, alerts_writer = prepare_csv(
            ALERTS_FILE, ALERT_FIELDS
        )

        print("Project Sentinel is starting...")
        time.sleep(1)

        while True:
            reading = generate_sensor_reading()

            if not validate_reading(reading):
                print("SENSOR ERROR: Invalid reading rejected.")
                time.sleep(SAMPLE_INTERVAL)
                continue

            severity, messages = analyze_reading(reading)
            trend_alerts = detect_trend(recent_readings)
            spike_alerts = detect_spike(reading, recent_readings)

            messages.extend(trend_alerts)
            messages.extend(spike_alerts)

            if (trend_alerts or spike_alerts) and severity == "NORMAL":
                severity = "WARNING"            
           
            if messages:
                status = f"{severity}: " + ", ".join(messages)
            else:
                status = "NORMAL"

            reading["status"] = status

            # Save every valid reading without overwriting old history.
            readings_writer.writerow(reading)
            readings_file.flush()

            total_readings += 1
            recent_readings.append(reading)

            for sensor in totals:
                totals[sensor] += reading[sensor]

            if severity == "WARNING":
                warning_count += 1

            elif severity == "CRITICAL":
                critical_count += 1

            if messages:
                last_alert = (
                    f"{reading['time']} | {status}"
                )

                alert_row = {
                    "time": reading["time"],
                    "severity": severity,
                    "message": ", ".join(messages),
                    "temperature": reading["temperature"],
                    "vibration": reading["vibration"],
                    "pressure": reading["pressure"],
                    "power": reading["power"],
                }

                alerts_writer.writerow(alert_row)
                alerts_file.flush()

            display_dashboard(
                reading,
                status,
                recent_readings,
                total_readings,
                warning_count,
                critical_count,
                last_alert,
                start_time,
            )

            if messages:
                print("\nLIVE ALERT:", status)

                if any("VIBRATION" in message for message in messages):
                    print("ACTION: Check the vibration sensor.")

                if any("TEMPERATURE" in message for message in messages):
                    print("ACTION: Check the temperature sensor.")

            time.sleep(SAMPLE_INTERVAL)

    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")

    finally:
        if readings_file is not None:
            readings_file.close()

        if alerts_file is not None:
            alerts_file.close()

        display_summary(
            total_readings,
            warning_count,
            critical_count,
            totals,
            start_time,
        )


if __name__ == "__main__":
    main()

