import time
import board
import analogio
import digitalio

# user settings - placeholders
skin_type = 1
sample_interval = 5.0

# GUVA breakout board: uvi = sensor output voltage * 10
uvi_per_volt = 10.0
uv_minimum = 0.0

# white LED stays on while the sensor voltage is above this value
uv_detect_voltage = 0.1

# skin type thresholds
# automatically assumed 1 for now
skin_thresholds = {
    1: (849000, 2200000),
    2: (1150000, 2500000),
    3: (1430000, 2790000),
    4: (1950000, 3300000)
}
first_threshold, second_threshold = skin_thresholds[skin_type]

# sensor configuration (GUVA breakout OUT -> A1)
uv_sensor = analogio.AnalogIn(board.A1)

def get_voltage():
    return uv_sensor.value * 3.3 / 65535

def voltage_to_uv_index(voltage):
    uv_index = voltage * uvi_per_volt
    return max(0.0, uv_index)

# alert output (RGB LED)
red_output = digitalio.DigitalInOut(board.D5)
red_output.direction = digitalio.Direction.OUTPUT
green_output = digitalio.DigitalInOut(board.D7)
green_output.direction = digitalio.Direction.OUTPUT
blue_output = digitalio.DigitalInOut(board.D9)
blue_output.direction = digitalio.Direction.OUTPUT

def set_leds(red, green, blue):
    red_output.value = red
    green_output.value = green
    blue_output.value = blue

def show_baseline(uv_present):
    # white (all three on) while UV is detected, otherwise off
    set_leds(uv_present, uv_present, uv_present)

# alert timing settings
alert_interval = 30.0  # seconds between alerts
alert_duration = 2.0   # seconds alert stays active
next_alert_time = 0.0
pulse_end_time = 0.0

def activate_alert(level, current_time, uv_present):
    global next_alert_time
    global pulse_end_time
    # No alert needed: just show the baseline (white if UV is present)
    if level == 0:
        show_baseline(uv_present)
        pulse_end_time = 0.0
        next_alert_time = current_time
        return
    # Start a new alert pulse when the next alert time is reached
    if current_time >= next_alert_time:
        if level == 1:
            set_leds(False, True, False)
        elif level == 2:
            set_leds(False, False, True)
        elif level == 3:
            set_leds(True, False, False)
        pulse_end_time = current_time + alert_duration
        next_alert_time = current_time + alert_interval
    # After the pulse ends, go back to the baseline
    elif current_time >= pulse_end_time:
        show_baseline(uv_present)

# exposure and dose calculations
cumulative_dose = 0.0
exposure_time = 0.0
previous_time = time.monotonic()

def calculate_dose(uv_index, elapsed_time):
    intensity = 18.9 * uv_index
    dose_increment = (intensity ** (4 / 3)) * elapsed_time
    return dose_increment

def update_exposure(uv_index):
    global cumulative_dose
    global exposure_time
    global previous_time
    current_time = time.monotonic()
    elapsed_time = current_time - previous_time
    previous_time = current_time
    if uv_index > uv_minimum:
        exposure_time += elapsed_time
        cumulative_dose += calculate_dose(uv_index, elapsed_time)

# alert threshold checking
def check_alerts():
    if cumulative_dose >= second_threshold:
        return 3
    elif cumulative_dose >= first_threshold:
        return 2
    elif cumulative_dose >= first_threshold * 0.75:
        return 1
    else:
        return 0

# main
def main():
    last_sample = time.monotonic()
    level = 0

    # startup: white for 5 seconds
    start_time = time.time()
    while time.time() - start_time < 5:
        set_leds(True, True, True)
        time.sleep(0.05)
    set_leds(False, False, False)

    while True:
        current_time = time.monotonic()
        voltage = get_voltage()

        # white LED follows the sensor voltage on every loop
        uv_present = voltage > uv_detect_voltage

        # dose measurement every sample_interval seconds
        if current_time - last_sample >= sample_interval:
            update_exposure(voltage_to_uv_index(voltage))
            level = check_alerts()
            last_sample = current_time

        # alert pulses override the white LED briefly
        activate_alert(level, current_time, uv_present)
        time.sleep(0.05)

# run program
main()
